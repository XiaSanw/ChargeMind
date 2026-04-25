"""
场站数据向量化索引 — Kimi Embedding API 版本
读取 stations.jsonl，调用 Kimi API 生成 embedding，存入 ChromaDB
"""
import json
import time
from pathlib import Path

import chromadb
from chromadb.config import Settings

from config import KIMI_API_KEY, KIMI_BASE_URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 优先使用带网格画像的数据，若不存在或是 LFS 指针则回退到旧版
GRID_PATH = PROJECT_ROOT.parent / "data" / "cleaned" / "stations_with_grid.jsonl"

def _is_lfs_pointer(path: Path) -> bool:
    """检测文件是否为 Git LFS 指针文件"""
    if not path.exists():
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            first = f.read(64)
        return first.startswith("version https://git-lfs.github.com/spec")
    except Exception:
        return False

DATA_PATH = GRID_PATH if (GRID_PATH.exists() and not _is_lfs_pointer(GRID_PATH)) else PROJECT_ROOT.parent / "data" / "cleaned" / "stations.jsonl"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"

# Kimi Embedding 客户端
from openai import OpenAI
kimi_client = OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
EMBEDDING_MODEL = "moonshot-v1-embedding"
BATCH_SIZE = 100  # 实测最优 batch size（5秒/100条）


def build_station_doc(station: dict) -> str:
    """
    构建 Embedding 检索文档。
    策略：以需求侧真实生态（grid 数据）为核心，供给侧配置为辅助。
    利用率/日均充电量等估算指标不再参与检索——数据质量差，会污染相似度计算。
    """
    region = station.get("region", "未知")
    biz = ",".join(station.get("business_type", []) or [""])
    power = station.get("total_installed_power", 0)

    # 桩数统计
    pile_count = (
        station.get("le_30kw_count", 0)
        + station.get("gt_30_le_120kw_count", 0)
        + station.get("gt_120_le_360kw_count", 0)
        + station.get("gt_360kw_count", 0)
    )

    parts = []

    # ── 第一层：区域定位（用户画像中最准的字段）──
    parts.append(f"{region}{biz}充电需求区域")

    # ── 第二层：需求侧真实生态（grid 数据，观测值，最可靠）──
    gp = station.get("grid_vehicle_profile")
    if gp:
        # 车流量
        car_trips = gp.get("avg_daily_car_trips")
        if car_trips:
            parts.append(f"周边日均{car_trips:.0f}车次")

        # 车型 Top-3
        vtm = gp.get("vehicle_type_mix", {})
        if vtm:
            top3 = sorted(vtm.items(), key=lambda x: -x[1])[:3]
            types_str = "、".join([f"{t}{r*100:.0f}%" for t, r in top3])
            parts.append(f"车型以{types_str}为主")

        # 功率需求 Top-2
        plm = gp.get("power_level_mix", {})
        if plm:
            top2 = sorted(plm.items(), key=lambda x: -x[1])[:2]
            power_str = "、".join([f"{t}{r*100:.0f}%" for t, r in top2])
            parts.append(f"功率需求以{power_str}为主")

        # SOC
        soc = gp.get("avg_soc")
        if soc is not None:
            parts.append(f"平均SOC{soc:.0f}%")

        # 迁移态势
        mig = gp.get("migration", {})
        net = mig.get("net_migration", 0)
        if net > 100:
            parts.append(f"净流入{net:.0f}车次/日")
        elif net < -100:
            parts.append(f"净流出{abs(net):.0f}车次/日")
    else:
        # 无 grid 数据：回退到最小可用信息
        cars = ",".join(station.get("service_car_types_desc", []) or [])
        if cars:
            parts.append(f"服务{cars}")

    # ── 第三层：供给侧配置（辅助参考，放后面降低权重）──
    if pile_count:
        parts.append(f"场站配置{pile_count}个桩")
    if power:
        # 功率数值异常大时简化显示（避免 161035kW 这种异常值主导）
        if power > 100000:
            parts.append(f"装机功率超大型场站")
        else:
            parts.append(f"装机{power:.0f}kW")

    # ── 明确不使用的低质量字段 ──
    # avg_utilization  — 19.6% 场站 <1%，数据质量极差
    # avg_daily_energy_kwh — 网格级平均，非场站实际
    # peak_hour / valley_hour — 样本稀疏，可信度低

    return "，".join(parts)


def get_embeddings(texts: list, retries: int = 3) -> list:
    """调用 Kimi Embedding API 生成向量（带重试）"""
    import time
    for attempt in range(retries):
        try:
            resp = kimi_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
            )
            return [d.embedding for d in resp.data]
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 * (attempt + 1)
                print(f"    [WARN] Embedding 失败，{wait}s 后重试 ({attempt+1}/{retries}): {e}")
                time.sleep(wait)
            else:
                raise


def index_stations(force_rebuild: bool = False):
    """索引所有场站数据到 ChromaDB。支持断点续传。"""
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    existing = [c.name for c in client.list_collections()]

    if "stations" in existing and force_rebuild:
        client.delete_collection("stations")
        print("[RAG] force_rebuild=True，已删除旧集合")

    # 获取或创建集合
    if "stations" in existing and not force_rebuild:
        collection = client.get_collection("stations")
    else:
        collection = client.create_collection(
            name="stations",
            metadata={"hnsw:space": "cosine"},
        )

    # 读取数据
    stations = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            stations.append(json.loads(line))

    # 断点续传：检测已存在的记录
    existing_ids = set()
    try:
        all_existing = collection.get(include=[])
        existing_ids = set(all_existing["ids"])
        print(f"[RAG] 发现已有 {len(existing_ids)} 条记录，将跳过")
    except Exception:
        pass

    # 过滤掉已索引的
    stations_to_index = [s for s in stations if s["station_id"] not in existing_ids]
    if not stations_to_index:
        print("[RAG] 所有记录已索引，无需重建")
        return collection

    print(f"[RAG] 开始索引 {len(stations_to_index)} 条新场站数据（总 {len(stations)} 条）...")

    def _safe_float(v):
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    total = len(stations_to_index)
    for i in range(0, total, BATCH_SIZE):
        batch = stations_to_index[i : i + BATCH_SIZE]

        ids = [s["station_id"] for s in batch]
        docs = [build_station_doc(s) for s in batch]
        def _build_metadata(s):
            meta = {
                "station_name": str(s.get("station_name", "") or ""),
                "region": str(s.get("region", "") or ""),
                "business_type": ",".join(s.get("business_type", []) or []),
                "total_installed_power": _safe_float(s.get("total_installed_power")),
                "avg_daily_energy_kwh": _safe_float(s.get("avg_daily_energy_kwh")),
                "avg_utilization": _safe_float(s.get("avg_utilization")),
                "peak_hour": str(s.get("peak_hour", "") or ""),
                "has_timeseries_data": bool(s.get("has_timeseries_data", False)),
            }
            # 网格画像字段（若存在）
            gp = s.get("grid_vehicle_profile")
            if gp:
                meta["has_grid_profile"] = True
                meta["grid_code"] = str(gp.get("grid_code", "") or "")
                meta["grid_avg_daily_cars"] = _safe_float(gp.get("avg_daily_car_trips"))
                meta["grid_peak_hour_cars"] = _safe_float(gp.get("peak_hour_car_trips"))
                meta["grid_avg_soc"] = _safe_float(gp.get("avg_soc"))
                meta["grid_avg_run_radius_m"] = _safe_float(gp.get("avg_run_radius_m"))
            else:
                meta["has_grid_profile"] = False
            return meta

        metadatas = [_build_metadata(s) for s in batch]

        # 调用 Kimi API 生成 embedding
        embeddings = get_embeddings(docs)

        # 存入 ChromaDB（传入预计算的 embedding）
        collection.add(
            ids=ids,
            documents=docs,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        print(f"[RAG] 已索引 {min(i + BATCH_SIZE, total)}/{total}")
        # 699 套餐无需限流，实测 batch=100 稳定

    print(f"[RAG] 索引完成，存储于 {CHROMA_PATH}")
    return collection


def get_collection():
    """获取已存在的集合"""
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_collection("stations")


if __name__ == "__main__":
    index_stations(force_rebuild=True)
