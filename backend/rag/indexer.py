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
DATA_PATH = PROJECT_ROOT.parent / "data" / "cleaned" / "stations.jsonl"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"

# Kimi Embedding 客户端
from openai import OpenAI
kimi_client = OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
EMBEDDING_MODEL = "moonshot-v1-embedding"
BATCH_SIZE = 100  # 实测最优 batch size（5秒/100条）


def build_station_doc(station: dict) -> str:
    """把场站结构化数据转成精简自然语言文档（控制token长度）"""
    region = station.get("region", "未知")
    biz = ",".join(station.get("business_type", []) or [""])
    power = station.get("total_installed_power", 0)
    energy = station.get("avg_daily_energy_kwh", 0)
    util = station.get("avg_utilization", 0)
    peak = station.get("peak_hour", "")
    cars = ",".join(station.get("service_car_types_desc", []) or [])

    # 精简文档：保留最核心的检索维度
    parts = [f"{region}{biz}充电站"]
    if power:
        parts.append(f"装机{power}kW")
    if energy:
        parts.append(f"日均{energy}度")
    if util is not None:
        parts.append(f"利用率{util}")
    if peak:
        parts.append(f"高峰{peak}")
    if cars:
        parts.append(f"服务{cars}")

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
    """索引所有场站数据到 ChromaDB"""
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    existing = [c.name for c in client.list_collections()]
    if "stations" in existing and not force_rebuild:
        print(f"[RAG] 集合已存在，跳过索引 ({CHROMA_PATH})")
        return client.get_collection("stations")

    if "stations" in existing:
        client.delete_collection("stations")

    # 创建集合（不使用默认 embedding function）
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
        metadatas = [
            {
                "station_name": str(s.get("station_name", "") or ""),
                "region": str(s.get("region", "") or ""),
                "business_type": ",".join(s.get("business_type", []) or []),
                "total_installed_power": _safe_float(s.get("total_installed_power")),
                "avg_daily_energy_kwh": _safe_float(s.get("avg_daily_energy_kwh")),
                "avg_utilization": _safe_float(s.get("avg_utilization")),
                "peak_hour": str(s.get("peak_hour", "") or ""),
                "has_timeseries_data": bool(s.get("has_timeseries_data", False)),
            }
            for s in batch
        ]

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
