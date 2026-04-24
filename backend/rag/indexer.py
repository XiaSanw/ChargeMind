"""
场站数据向量化索引
读取 stations.jsonl，生成自然语言描述，存入 ChromaDB
"""
import json
from pathlib import Path

import chromadb
from chromadb.config import Settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT.parent / "data" / "cleaned" / "stations.jsonl"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"


def build_station_doc(station: dict) -> str:
    """把场站结构化数据转成自然语言文档"""
    name = station.get("station_name", "未知场站")
    region = station.get("region", "未知区域")
    biz = ",".join(station.get("business_type", []) or ["未知业态"])
    power = station.get("total_installed_power", 0)
    energy = station.get("avg_daily_energy_kwh", 0)
    util = station.get("avg_utilization", 0)
    peak = station.get("peak_hour", "未知")
    valley = station.get("valley_hour", "未知")
    cars = ",".join(station.get("service_car_types_desc", []) or [])
    land = station.get("land_property_desc", "")

    fee = station.get("electricity_fee_parsed") or {}
    if fee and fee.get("periods"):
        prices = [f"{p['start']}-{p['end']}:{p['price']}元" for p in fee["periods"]]
        fee_desc = "；".join(prices)
    else:
        fee_desc = "未知"

    doc = (
        f"{name}位于{region}，属于{biz}。"
        f"装机功率{power}kW，"
        f"日均充电量{energy}度，利用率{util}，"
        f"高峰时段{peak}，低谷时段{valley}。"
        f"服务车型：{cars}。土地性质：{land}。"
        f"电价结构：{fee_desc}。"
    )
    return doc


def index_stations(force_rebuild: bool = False):
    """索引所有场站数据到 ChromaDB"""
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    # 如果集合已存在且不需要重建，直接返回
    existing = [c.name for c in client.list_collections()]
    if "stations" in existing and not force_rebuild:
        print(f"[RAG] 集合已存在，跳过索引 ({CHROMA_PATH})")
        return client.get_collection("stations")

    if "stations" in existing:
        client.delete_collection("stations")

    collection = client.create_collection(
        name="stations",
        metadata={"hnsw:space": "cosine"},
    )

    # 读取数据
    stations = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            stations.append(json.loads(line))

    print(f"[RAG] 开始索引 {len(stations)} 条场站数据...")

    batch_size = 500
    for i in range(0, len(stations), batch_size):
        batch = stations[i : i + batch_size]
        ids = [s["station_id"] for s in batch]
        docs = [build_station_doc(s) for s in batch]
        def _safe_float(v):
            try:
                return float(v) if v is not None else 0.0
            except (TypeError, ValueError):
                return 0.0

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
        collection.add(ids=ids, documents=docs, metadatas=metadatas)
        print(f"[RAG] 已索引 {min(i + batch_size, len(stations))}/{len(stations)}")

    print(f"[RAG] 索引完成，存储于 {CHROMA_PATH}")
    return collection


def get_collection():
    """获取已存在的集合（不重建）"""
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_collection("stations")


if __name__ == "__main__":
    index_stations(force_rebuild=True)
