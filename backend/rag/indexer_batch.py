"""
分批索引工具 — 避免长时间运行被中断
用法: python3 backend/rag/indexer_batch.py [批次大小, 默认1000]
"""
import sys
import json
from pathlib import Path

from indexer import index_stations, get_collection

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cleaned" / "stations.jsonl"
BATCH_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 1000


def index_batch(batch_size: int = 1000):
    """索引下一批未索引的数据"""
    col = get_collection()
    existing = set()
    try:
        all_ids = col.get(include=[])
        existing = set(all_ids["ids"])
    except Exception:
        pass

    # 读取全部数据
    stations = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            stations.append(json.loads(line))

    # 找出未索引的
    pending = [s for s in stations if s["station_id"] not in existing]
    if not pending:
        print("[INDEX] 所有数据已索引完成！")
        return False

    # 只取前 batch_size 条
    batch = pending[:batch_size]
    print(f"[INDEX] 总数据 {len(stations)} 条，已索引 {len(existing)} 条，本次索引 {len(batch)} 条...")

    # 直接调用 indexer 的 add 逻辑（不走完整 index_stations，避免检测逻辑重复）
    from indexer import build_station_doc, get_embeddings

    def _safe_float(v):
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

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

    embeddings = get_embeddings(docs)
    col.add(ids=ids, documents=docs, embeddings=embeddings, metadatas=metadatas)

    print(f"[INDEX] 完成！本次索引 {len(batch)} 条，累计 {len(existing) + len(batch)}/{len(stations)}")
    return True


if __name__ == "__main__":
    has_more = index_batch(BATCH_SIZE)
    if has_more:
        remaining = 10942 - (get_collection().count())
        print(f"[INDEX] 还剩 {remaining} 条，请继续运行本脚本")
