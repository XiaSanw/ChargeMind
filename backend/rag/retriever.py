"""
相似场站检索器 — Kimi Embedding API 版本
"""
from rag.indexer import get_collection, get_embeddings


def retrieve_similar(profile: dict, n_results: int = 10):
    """
    根据场站画像检索相似场站。

    查询策略：
    1. 区域权重最高 — 同片区才有对标价值
    2. 功率作为用户意图参考（非精确匹配）— 反映用户计划的供给规模
    3. 不依赖利用率/日均充电量等低质量估算指标 — 这些字段不参与检索

    Embedding 文档以需求侧 grid 生态为核心，供给侧配置为辅助。
    """
    collection = get_collection()

    region = profile.get("region", "")
    biz = profile.get("business_type", [])
    power = profile.get("total_installed_power", 0)

    biz_str = biz[0] if biz else ""

    # 构建查询文本：区域 > 业态 > 功率（桩数不纳入，与相似度无关）
    query_parts = [f"{region}{biz_str}充电需求区域"]
    if power:
        query_parts.append(f"装机功率{power}kW")
    query = "，".join(query_parts)

    # 调用 Kimi API 生成查询向量
    query_embedding = get_embeddings([query])[0]

    # 向量检索
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


def retrieve_for_rerank(profile: dict) -> list:
    """
    检索候选场站用于 Chat 重排序。
    取 Top-15 给 Chat 模型留足选择空间（最终输出 Top-10）。
    """
    return retrieve_similar(profile, n_results=15)
