"""
Chat 模型重排序器

用 DeepSeek v4-pro 的推理能力对向量检索结果做精排：
1. 取向量检索 Top-8 作为候选集
2. 让 Chat 模型从运营视角评估每个候选场站的对比价值
3. 精选 Top-5，每条附带"为什么相似"的解释
4. 若 LLM 不可用，自动降级为向量排序结果
"""
import json
import os

_RERANK_PROMPT = """你是一位充电场站运营对标专家。用户正在诊断一个充电场站，我们已经用向量检索找出了 8 个候选对标场站。

你需要从**运营对比价值**的角度，选出最值得对标的 5 个场站，并解释每个场站为什么有参考意义。

## 评估维度（按重要性排序）
1. **运营可比性**：硬件配置（功率/桩数）和业态是否相似？
2. **地理相关性**：是否在同一片区？共享同样的客群和竞争环境？
3. **对比价值**：运营结果（利用率/收益）差异大不大？差异越大越有分析价值
4. **数据质量**：是否有真实时序数据支撑？（has_timeseries_data=true 加分）

## 用户场站画像
{user_profile_text}

## 候选场站（8 个）
{candidates_text}

## 输出要求
只输出一个 JSON 数组（不要代码块标记），包含 5 个场站，按对比价值从高到低排序：

[
  {{
    "station_id": "场站ID（直接用候选列表里的）",
    "rank": 1,
    "similarity_reason": "一句话说明为什么这个场站值得对标（如：同属办公区、功率接近、但利用率差3倍，且有真实数据）",
    "key_comparison": "最值得看的一个指标对比（如：你的利用率5% vs 它的25%）"
  }},
  ...
]

选满 5 个。如果候选不足 8 个，有几个选几个。"""


def chat_rerank(profile: dict, candidates: list, chat_client, model: str) -> list:
    """
    用 Chat 模型对候选场站重排序，精选 Top-5 并附带解释。

    Args:
        profile: 用户场站画像 dict
        candidates: 向量检索候选场站列表（已含 station_id / document / metadata / similarity_score）
        chat_client: OpenAI 兼容的 Chat 客户端实例
        model: Chat 模型名（如 deepseek-v4-pro）

    Returns:
        重排后的 Top-5 场站列表，每条新增 similarity_reason 和 key_comparison 字段，
        且 similarity_score 调整为 Chat 赋予的新排名分（rank=1 → 1.0, rank=2 → 0.9, ...）
    """
    if not candidates or not chat_client:
        return _fallback_rerank(candidates)

    # 构建用户画像描述
    profile_parts = []
    if profile.get("region"):
        profile_parts.append(f"区域：{profile['region']}")
    biz = profile.get("business_type", [])
    if biz:
        profile_parts.append(f"业态：{', '.join(biz)}")
    if profile.get("total_installed_power"):
        profile_parts.append(f"装机功率：{profile['total_installed_power']} kW")
    if profile.get("pile_count"):
        profile_parts.append(f"桩数：{profile['pile_count']} 个")
    user_profile_text = "\n".join(profile_parts) if profile_parts else "（用户未提供详细画像）"

    # 构建候选文本
    candidate_lines = []
    for i, c in enumerate(candidates, 1):
        meta = c.get("metadata", {})
        lines = [
            f"### 候选 {i}",
            f"- station_id: {c.get('station_id', '')}",
            f"- 名称: {meta.get('station_name', '未知')}",
            f"- 区域: {meta.get('region', '未知')}",
            f"- 业态: {meta.get('business_type', '未知')}",
            f"- 装机功率: {meta.get('total_installed_power', 0):.0f} kW",
            f"- 利用率: {meta.get('avg_utilization', 0)}",
            f"- 日均充电量: {meta.get('avg_daily_energy_kwh', 0):.0f} 度",
            f"- 高峰时段: {meta.get('peak_hour', '未知')}",
            f"- 有真实数据: {meta.get('has_timeseries_data', False)}",
            f"- 向量相似度: {c.get('similarity_score', 0)}",
        ]
        candidate_lines.append("\n".join(lines))
    candidates_text = "\n\n".join(candidate_lines)

    prompt = _RERANK_PROMPT.format(
        user_profile_text=user_profile_text,
        candidates_text=candidates_text,
    )

    try:
        resp = chat_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        # 解析 JSON（处理可能的数组包装）
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "stations" in parsed:
            ranked_list = parsed["stations"]
        elif isinstance(parsed, list):
            ranked_list = parsed
        else:
            return _fallback_rerank(candidates)

        # 按 station_id 回填完整数据
        id_to_candidate = {c["station_id"]: c for c in candidates}
        result = []
        for item in ranked_list[:5]:
            sid = item.get("station_id", "")
            if sid not in id_to_candidate:
                continue
            merged = dict(id_to_candidate[sid])  # 复制原始数据
            merged["similarity_reason"] = item.get("similarity_reason", "")
            merged["key_comparison"] = item.get("key_comparison", "")
            # Chat 排名分：rank=1 → 1.0, rank=2 → 0.9, ...
            merged["rerank_score"] = round(1.0 - (item.get("rank", len(result) + 1) - 1) * 0.1, 2)
            merged["reranked_by"] = "chat"
            result.append(merged)

        if len(result) < len(candidates):
            # 补充未选中的（保持原顺序）
            selected_ids = {r["station_id"] for r in result}
            for c in candidates:
                if c["station_id"] not in selected_ids and len(result) < 5:
                    c_copy = dict(c)
                    c_copy["similarity_reason"] = ""
                    c_copy["key_comparison"] = ""
                    c_copy["rerank_score"] = c.get("similarity_score", 0)
                    c_copy["reranked_by"] = "chat"
                    result.append(c_copy)

        return result

    except Exception:
        return _fallback_rerank(candidates)


def _fallback_rerank(candidates: list) -> list:
    """LLM 不可用时的降级方案：保持向量排序，取前 5 个"""
    result = []
    for c in candidates[:5]:
        c_copy = dict(c)
        c_copy["similarity_reason"] = ""
        c_copy["key_comparison"] = ""
        c_copy["rerank_score"] = c.get("similarity_score", 0)
        c_copy["reranked_by"] = "vector"
        result.append(c_copy)
    return result
