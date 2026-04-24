"""
相似场站检索器 — Kimi Embedding API 版本
"""
from rag.indexer import get_collection, get_embeddings


def retrieve_similar(profile: dict, n_results: int = 5):
    """
    根据场站画像检索相似场站
    """
    collection = get_collection()

    region = profile.get("region", "")
    biz = profile.get("business_type", [])
    power = profile.get("total_installed_power", 0)
    pile_count = profile.get("pile_count", 10)

    biz_str = biz[0] if biz else ""

    # 构建查询文本
    query = (
        f"{region}{biz_str}充电站，"
        f"装机功率{power}kW，{pile_count}个桩"
    )

    # 调用 Kimi API 生成查询向量
    query_embedding = get_embeddings([query])[0]

    # 向量检索（传入预计算 embedding）
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    # 格式化结果
    stations = []
    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for i in range(len(ids)):
        stations.append({
            "station_id": ids[i],
            "document": docs[i],
            "metadata": metas[i],
            "similarity_score": round(1 - distances[i], 4),
        })

    return stations
