"""
诊断接口
POST /api/extract    → LLM 解析用户输入为结构化画像
POST /api/enrich     → 判断缺失字段，生成追问
POST /api/diagnose   → 完整诊断报告（硬算 + RAG + LLM 叙事包装）
"""
import os
import json
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from core.reranker import chat_rerank
from core.report_builder import build_report_by_profile
from rag.retriever import retrieve_for_rerank, retrieve_similar

router = APIRouter()

# 尝试初始化 LLM 客户端（DeepSeek 用于 Chat Completion）
try:
    from openai import OpenAI
    chat_client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    LLM_AVAILABLE = bool(os.getenv("DEEPSEEK_API_KEY"))
except Exception:
    chat_client = None
    LLM_AVAILABLE = False

CHAT_MODEL = os.getenv("CHAT_MODEL", "deepseek-chat")

# ============ 数据模型 ============

class ExtractRequest(BaseModel):
    user_input: str


class StationProfile(BaseModel):
    station_name: Optional[str] = None
    region: Optional[str] = None
    business_type: Optional[list] = None
    total_installed_power: Optional[float] = None
    pile_count: Optional[int] = None
    monthly_rent: Optional[float] = None
    staff_count: Optional[int] = None
    avg_price: Optional[float] = None
    peak_hour: Optional[str] = None
    valley_hour: Optional[str] = None
    pile_breakdown: Optional[dict] = None
    has_brand_pile: Optional[str] = None
    brand_piles: Optional[dict] = None


class EnrichRequest(BaseModel):
    profile: dict


class DiagnoseRequest(BaseModel):
    profile: dict


# 问卷字段定义（用于 enrich）
ENRICH_FIELDS = [
    {"key": "region", "question": "场站位于深圳哪个区？", "type": "select", "options": ["南山区","福田区","宝安区","龙岗区","龙华区","罗湖区","光明区","坪山区","盐田区","大鹏新区","前海"]},
    {"key": "business_type", "question": "周边主要业态是什么？", "type": "multiselect", "options": ["交通枢纽","商业区","办公区","住宅区","工业区","旅游景区"]},
    {"key": "total_installed_power", "question": "装机总功率大约多少 kW？", "type": "number"},
    {"key": "pile_count", "question": "有多少个充电桩？", "type": "number"},
    {"key": "pile_breakdown", "question": "当前不同功率等级的充电桩分别有多少台？", "type": "multi-number", "subfields": [
        {"key": "slow", "label": "30kW以下慢充桩", "placeholder": "例如：5"},
        {"key": "fast", "label": "30-160kW快充桩", "placeholder": "例如：10"},
        {"key": "super", "label": "160kW以上超充桩", "placeholder": "例如：2"}
    ]},
    {"key": "has_brand_pile", "question": "是否有品牌专用桩？", "type": "select", "options": ["有", "无"]},
    {"key": "brand_piles", "question": "各品牌专用桩分别有多少台？（没有填0）", "type": "multi-number", "subfields": [
        {"key": "特斯拉", "label": "特斯拉", "placeholder": "0"},
        {"key": "蔚来", "label": "蔚来", "placeholder": "0"},
        {"key": "小鹏", "label": "小鹏", "placeholder": "0"},
        {"key": "比亚迪", "label": "比亚迪", "placeholder": "0"},
        {"key": "理想", "label": "理想", "placeholder": "0"},
        {"key": "其他", "label": "其他品牌", "placeholder": "0"}
    ]},
    {"key": "monthly_rent", "question": "月租金大约多少元？", "type": "number"},
    {"key": "staff_count", "question": "运维人员有几人？", "type": "number"},
    {"key": "avg_price", "question": "平均电价+服务费大约多少元/度？", "type": "number"},
]


# ============ 端点实现 ============

@router.post("/extract")
def extract_profile(req: ExtractRequest):
    """
    解析用户自然语言输入，提取结构化场站画像。
    若 LLM 不可用，返回基础解析结果。
    """
    if not LLM_AVAILABLE:
        text = req.user_input
        profile = _mock_extract(text)
        return {"profile": profile, "llm_used": False}

    prompt = f"""请从以下用户描述中提取充电场站的关键信息，输出为 JSON。

【核心规则】
- 只提取用户**明确提到**的信息
- 用户**没有提到**的字段，必须设为 null 或空数组，禁止推断、禁止填充默认值
- 不要根据"充电站"推断电价，不要根据区域推断租金

用户描述：""" + req.user_input + """

需要的字段（未提及必须填 null）：
- station_name: 场站名称（如有，否则 null）
- region: 所在行政区（如南山区，未提及则 null）
- business_type: 周边业态列表（未提及则 []）
- total_installed_power: 装机总功率 kW（未提及则 null）
- pile_count: 充电桩数量（未提及则 null）
- monthly_rent: 月租金元（未提及则 null）
- staff_count: 运维人数（未提及则 null）
- avg_price: 平均电价+服务费 元/度（未提及则 null）
- peak_hour: 高峰时段（未提及则 null）

请只输出 JSON，不要其他内容。"""

    try:
        resp = chat_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        profile = json.loads(content)
        profile = {k: v for k, v in profile.items() if v is not None and v != ""}
        return {"profile": profile, "llm_used": True}
    except Exception as e:
        profile = _mock_extract(req.user_input)
        return {"profile": profile, "llm_used": False, "error": str(e)}


def _is_field_missing(profile: dict, field: dict) -> bool:
    """判断某个 enrich 字段是否缺失。"""
    key = field["key"]

    # 条件字段：brand_piles 仅在 has_brand_pile == "有" 时才需要
    if key == "brand_piles":
        has_brand = profile.get("has_brand_pile")
        if has_brand != "有":
            return False

    val = profile.get(key)

    # multi-number 类型：要求是 dict 且所有子字段都有非空数值
    if field.get("type") == "multi-number":
        if not isinstance(val, dict):
            return True
        subfields = field.get("subfields", [])
        for sf in subfields:
            sf_val = val.get(sf["key"])
            if sf_val is None or sf_val == "":
                return True
        return False

    # 其他类型
    if val is None or val == "" or val == []:
        return True
    return False


@router.post("/enrich")
def enrich_profile(req: EnrichRequest):
    """
    判断缺失字段，返回下一个需要追问的问题。
    """
    profile = req.profile
    missing = []
    for field in ENRICH_FIELDS:
        if _is_field_missing(profile, field):
            missing.append(field)

    if not missing:
        return {"complete": True, "next_question": None, "missing_count": 0}

    next_q = missing[0]
    return {
        "complete": False,
        "next_question": next_q,
        "missing_count": len(missing),
        "all_missing_keys": [m["key"] for m in missing],
    }


@router.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """
    完整诊断报告。
    流程：
    1. 根据 profile 匹配最佳场站
    2. 硬算所有分析模块（雷达图、KPI、功率错配、品牌、竞争定位）
    3. RAG 检索相似场站
    4. DeepSeek LLM 叙事包装（称号微调、异常识别、提升路径建议）
    5. 返回完整报告 JSON
    """
    profile = req.profile

    # 0. 先匹配场站，获取 grid_code（用于 RAG 同 grid 优先）
    from core.report_builder import _find_station_by_profile
    matched_station = _find_station_by_profile(profile)
    matched_grid_code = None
    if matched_station:
        gp = matched_station.get("grid_vehicle_profile", {}) or {}
        matched_grid_code = matched_station.get("grid_code") or gp.get("grid_code")

    # 1. RAG 检索相似场站（优先同 grid）
    similar = []
    rerank_info = {"used": False, "method": "vector", "grid_priority": False}
    try:
        if LLM_AVAILABLE:
            candidates = retrieve_for_rerank(profile)
            if len(candidates) > 0 and matched_grid_code:
                # 同 grid 优先排序
                same_grid = [c for c in candidates if _get_grid_code_from_meta(c) == matched_grid_code]
                other_grid = [c for c in candidates if _get_grid_code_from_meta(c) != matched_grid_code]
                candidates = same_grid + other_grid
                rerank_info["grid_priority"] = True
                rerank_info["same_grid_count"] = len(same_grid)
            if len(candidates) > 0:
                similar = chat_rerank(profile, candidates, chat_client, CHAT_MODEL)
                rerank_info["used"] = True
                rerank_info["method"] = "chat"
                rerank_info["candidate_count"] = len(candidates)
                rerank_info["selected_count"] = len(similar)
            else:
                similar = []
        else:
            similar = retrieve_similar(profile, n_results=10)
            if matched_grid_code:
                same_grid = [c for c in similar if _get_grid_code_from_meta(c) == matched_grid_code]
                other_grid = [c for c in similar if _get_grid_code_from_meta(c) != matched_grid_code]
                similar = same_grid + other_grid
                rerank_info["grid_priority"] = True
                rerank_info["same_grid_count"] = len(same_grid)
            rerank_info["method"] = "vector"
    except Exception as e:
        try:
            similar = retrieve_similar(profile, n_results=10)
            rerank_info["error"] = str(e)
        except Exception:
            similar = []

    # 2. 硬算完整报告
    report = build_report_by_profile(profile, similar_stations=similar)

    # 3+4. DeepSeek LLM 两次调用并行执行（详细分析 + 叙事包装）
    if LLM_AVAILABLE and "error" not in report:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _call_detail():
            try:
                return _llm_detail_analysis(report, profile, similar, chat_client, CHAT_MODEL)
            except Exception:
                return None

        def _call_narrative():
            try:
                return _llm_narrative_packaging(report, profile, chat_client, CHAT_MODEL)
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_detail = executor.submit(_call_detail)
            future_narrative = executor.submit(_call_narrative)

            for future in as_completed([future_detail, future_narrative]):
                result = future.result()
                if result is None:
                    continue
                if "detail_analysis" in result:
                    report["detail_text"] = result.get("detail_analysis", report.get("detail_text", ""))
                elif "headline_refined" in result:
                    report["llm_enhancement"] = result
                    refined = result.get("headline_refined", "")
                    if refined:
                        report.setdefault("dashboard", {})["headline"] = refined
                    kpi_summary = result.get("kpi_summary", "")
                    if kpi_summary:
                        report.setdefault("dashboard", {})["kpi_summary"] = kpi_summary
    else:
        report["llm_enhancement"] = {"error": "LLM 不可用"}

    return {
        "profile": profile,
        "report": report,
        "rag": {
            "similar_stations": similar,
            "rerank_info": rerank_info,
        },
    }


# ============ LLM 叙事包装 ============

def _llm_narrative_packaging(report: dict, profile: dict, client, model: str) -> dict:
    """
    用 DeepSeek 做叙事包装：
    1. 基于硬数据微调称号和 headline
    2. 异常识别（功率/价格/利用率异常原因）
    3. 趋势推演（引用季节波动数据，只做方向性解读，禁止生成数字）
    4. 提升路径建议（方向性建议，不生成精确数字）
    """
    dashboard = report.get("dashboard", {})
    radar = dashboard.get("radar", {})
    pm = report.get("power_mismatch", {})
    comp = report.get("competitive_position", {})
    price_bench = report.get("price_benchmark_result", {}).get("price_benchmark", {})
    seasonal = report.get("seasonal", {})

    # 季节波动提示文本（用于 LLM 趋势推演）
    seasonal_hint = ""
    if "error" not in seasonal:
        peak = seasonal.get("peak_season", "")
        trough = seasonal.get("trough_season", "")
        max_change = seasonal.get("max_change_pct", 0)
        hints = seasonal.get("season_changes", [])
        seasonal_hint = (
            f"季节波动：{peak}比{trough}高{max_change}%。"
            f"{'；'.join(hints)}"
        )

    # 价格对标提示文本
    my_prices = price_bench.get("my_prices", {})
    bench_prices = price_bench.get("benchmark_prices", {})
    gaps = price_bench.get("gaps", {})
    if my_prices and bench_prices and (my_prices.get("avg") is not None):
        price_hint = (
            f"价格结构对比——本场站 min/avg/max = "
            f"{my_prices.get('min', 'N/A')}/{my_prices.get('avg', 'N/A')}/{my_prices.get('max', 'N/A')} 元/kWh；"
            f"竞品基准 min/avg/max = "
            f"{bench_prices.get('min', 'N/A')}/{bench_prices.get('avg', 'N/A')}/{bench_prices.get('max', 'N/A')} 元/kWh。"
            f"价差 min={gaps.get('min_gap_pct', 'N/A')}% avg={gaps.get('avg_gap_pct', 'N/A')}% max={gaps.get('max_gap_pct', 'N/A')}%"
        )
    else:
        price_hint = "价格结构：本场站或竞品无有效价格数据，跳过价格对比分析。"

    # 提取 KPI 数据用于 LLM 分析
    kpi_cards = report.get("kpi_cards", [])
    kpi_text = "\n".join([
        f"- {c.get('label', '未知')}：{c.get('value', 'N/A')}（{c.get('benchmark', '')}，可信度{c.get('trust', '')}）"
        for c in kpi_cards
    ])

    prompt = f"""你是一位充电场站运营诊断专家。以下是一份基于硬数据计算的场站体检报告，请你进行叙事包装和异常识别。

【关键规则】
- 你只负责"叙事包装"和"异常识别"，不生成任何数字
- 所有数字已经由硬数据计算完成，你只需解释它们的意义
- 趋势推演只给方向性判断（上行/下行/平稳），禁止预测具体数值
- 提升路径只给方向性建议，不给精确收益预测

【场站画像】
- 区域：{profile.get('region', '未知')}
- 业态：{profile.get('business_type', [])}
- 装机功率：{profile.get('total_installed_power', '未知')}kW
- 桩数：{profile.get('pile_count', '未知')}

【关键指标（KPI）】
{kpi_text}

【硬数据诊断结果】
- 称号：{dashboard.get('title', '')}
- 5维得分：地段{radar.get('地段禀赋', {}).get('score', 'N/A')} / 硬件{radar.get('硬件适配', {}).get('score', 'N/A')} / 定价{radar.get('定价精准', {}).get('score', 'N/A')} / 运营{radar.get('运营产出', {}).get('score', 'N/A')} / 饱和{radar.get('需求饱和度', {}).get('score', 'N/A')}
- TVD功率错配：{pm.get('tvd_score', 'N/A')}（{pm.get('tvd_level', 'N/A')}）
- 竞争定位：{comp.get('competitive_position', {}).get('summary', 'N/A')}
- {price_hint}
- {seasonal_hint}

【输出约束】
- headline_refined：严格 20 字以内，一句话痛点，禁止解释
- kpi_summary：基于上述4个关键指标，给出30-50字的一句话综合分析，点明核心矛盾（如"利用率极低但定价偏高，存在量价错配"），禁止编造数据外的数字
- anomalies：最多 3 条，只列真正有异常的数据点，无异常时返回空数组
- trend_outlook：基于季节波动做方向性推演（上行/下行/平稳），20 字以内，禁止数字
- path_suggestions：最多 3 条，只给方向性建议，禁止出现具体数字

【输出格式】
请输出 JSON：
{{
  "headline_refined": "20字以内的一句话痛点",
  "kpi_summary": "基于4个关键指标的综合分析，30-50字",
  "anomalies": [
    {{
      "type": "功率异常/价格异常/运营异常/季节异常",
      "description": "15字以内异常描述",
      "severity": "高/中/低"
    }}
  ],
  "trend_outlook": "20字以内的季节趋势方向判断",
  "path_suggestions": [
    {{
      "title": "建议方向（10字以内）",
      "rationale": "30字以内逻辑解释"
    }}
  ]
}}
"""

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    return json.loads(content)


def _llm_detail_analysis(report: dict, profile: dict, similar_stations: list, client, model: str) -> dict:
    """
    用 DeepSeek 生成详细分析报告（Markdown）。
    把全部硬算数据 + RAG 相似场站数据都给 LLM，让它做综合分析。
    """
    dashboard = report.get("dashboard", {})
    radar = dashboard.get("radar", {})
    pm = report.get("power_mismatch", {})
    comp = report.get("competitive_position", {})
    brand = report.get("brand_analysis", {})
    price_bench = report.get("price_benchmark_result", {}).get("price_benchmark", {})
    seasonal = report.get("seasonal", {})
    paths = report.get("paths", [])

    # 提取 RAG 相似场站前 3 个关键信息
    rag_stations = []
    for s in similar_stations[:3]:
        meta = s.get("metadata", {})
        rag_stations.append({
            "name": meta.get("station_name", "未命名"),
            "region": meta.get("region", ""),
            "similarity": s.get("similarity_score", 0),
        })

    # 提取品牌 TOP3
    brand_matrix = brand.get("brand_matrix", {})
    top_brands = []
    if "error" not in brand_matrix:
        for b in brand_matrix.get("brands", [])[:3]:
            top_brands.append(f"{b.get('brand')} {b.get('share_pct')}%")

    # 提取电池建议
    bat = brand.get("battery_capacity", {})
    battery_suggestion = bat.get("power_suggestion", "") if "error" not in bat else ""

    # 提取竞争定位关键数据
    cp_inner = comp.get("competitive_position", {}) if isinstance(comp, dict) else {}
    cva = cp_inner.get("capacity_vs_actual", {})
    bench_price = cp_inner.get("competitive_benchmark_price", {})
    eu = cp_inner.get("equilibrium_utilization", {})

    # 提取功率错配关键数据
    dominant = pm.get("dominant_mismatch", {}) if "error" not in pm else {}

    # 提取季节
    seasonal_hint = ""
    if "error" not in seasonal:
        peak = seasonal.get("peak_season", "")
        trough = seasonal.get("trough_season", "")
        max_change = seasonal.get("max_change_pct", 0)
        seasonal_hint = f"{peak}比{trough}高{max_change}%。"

    # 构造 prompt
    prompt = f"""你是一位充电场站运营诊断专家。以下是一份基于硬数据计算的多维度场站体检报告，请你生成一份详细的 Markdown 分析报告。

【关键规则】
- 你负责"综合分析"和"深度解读"，不生成任何新数字
- 所有数字已经由硬数据计算完成，你只需解释它们的意义和相互关系
- 报告要专业但易懂，适合充电运营商阅读
- 分章节组织，每章有明确主题
- 禁止编造数据，所有引用必须来自以下提供的信息

【场站画像】
- 区域：{profile.get('region', '未知')}
- 业态：{profile.get('business_type', [])}
- 装机功率：{profile.get('total_installed_power', '未知')}kW
- 桩数：{profile.get('pile_count', '未知')}

【五维雷达评分】
- 地段禀赋：{radar.get('地段禀赋', {}).get('score', 'N/A')}分 — {radar.get('地段禀赋', {}).get('comment', '')}
- 硬件适配：{radar.get('硬件适配', {}).get('score', 'N/A')}分 — {radar.get('硬件适配', {}).get('comment', '')}
- 定价精准：{radar.get('定价精准', {}).get('score', 'N/A')}分 — {radar.get('定价精准', {}).get('comment', '')}
- 运营产出：{radar.get('运营产出', {}).get('score', 'N/A')}分 — {radar.get('运营产出', {}).get('comment', '')}
- 需求饱和度：{radar.get('需求饱和度', {}).get('score', 'N/A')}分 — {radar.get('需求饱和度', {}).get('comment', '')}

【功率错配分析】
- TVD 分数：{pm.get('tvd_score', 'N/A')}（{pm.get('tvd_level', 'N/A')}）
- 主导错配：{dominant.get('label', 'N/A')} {dominant.get('power_range', '')}，{dominant.get('direction', '')} {dominant.get('gap_pct', 0):.1f}%
- 电池容量建议：{battery_suggestion}

【品牌与客户画像】
- 品牌 TOP3：{'；'.join(top_brands) if top_brands else '无品牌数据'}

【竞争定位】
- 容量份额：{cva.get('capacity_share_pct', 'N/A')}% / 实际份额：{cva.get('actual_share_pct', 'N/A')}% / 偏差：{cva.get('share_gap_pct', 'N/A')}% → {cva.get('interpretation', '')}
- 本场站服务费：¥{bench_price.get('my_price', 'N/A')}/度 vs 竞品基准：¥{bench_price.get('benchmark_price', 'N/A')}/度（{bench_price.get('price_gap_pct', 'N/A')}%）
- 均衡利用率区间：{eu.get('low', 'N/A')}-{eu.get('high', 'N/A')}（弹性 {eu.get('elasticity_range', [1.5, 2.5])}）

【竞品价格对标】
- 本场站 min/avg/max：{price_bench.get('my_prices', {}).get('min', 'N/A')}/{price_bench.get('my_prices', {}).get('avg', 'N/A')}/{price_bench.get('my_prices', {}).get('max', 'N/A')} 元/kWh
- 竞品基准 min/avg/max：{price_bench.get('benchmark_prices', {}).get('min', 'N/A')}/{price_bench.get('benchmark_prices', {}).get('avg', 'N/A')}/{price_bench.get('benchmark_prices', {}).get('max', 'N/A')} 元/kWh
- 本场站峰谷比：{price_bench.get('spread_ratio', 'N/A')} vs 竞品：{price_bench.get('benchmark_spread_ratio', 'N/A')}

【季节波动】
- {seasonal_hint}

【提升路径】
"""
    for i, p in enumerate(paths[:3], 1):
        gain = f"+{p.get('annual_gain')}万/年" if p.get('annual_gain') is not None else "建议方向（无精确收益）"
        calc = f"（公式：{p.get('calculation')}）" if p.get('calculation') else ""
        prompt += f"{i}. {p.get('title')} [{p.get('category')}] — {gain}，投入{p.get('effort')}。{p.get('detail')}{calc}\n"

    prompt += f"""
【RAG 检索到的相似场站】
"""
    for i, s in enumerate(rag_stations, 1):
        prompt += f"{i}. {s['name']}（{s['region']}），相似度 {s['similarity']:.2f}\n"

    prompt += """
【输出约束】
- 生成详细的 Markdown 分析报告，分章节
- 章节建议：竞争格局分析、功率与硬件诊断、品牌与客户洞察、定价策略分析、季节趋势判断、综合提升建议
- 每章要有"核心发现"+"数据支撑"+"行动建议"
- 禁止出现"根据数据显示"等空洞套话，直接讲洞察
- 禁止编造任何数字

【输出格式】
请输出 JSON：
{
  "detail_analysis": "完整的 Markdown 报告文本（支持 ## 二级标题、- 列表、**加粗**）"
}
"""

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    return json.loads(content)


# ============ 辅助函数 ============

def _mock_extract(text: str) -> dict:
    """简单的关键词提取（无 LLM 时的 fallback）"""
    profile = {}
    regions = ["南山", "福田", "宝安", "龙岗", "龙华", "罗湖", "光明", "坪山", "盐田", "大鹏", "前海"]
    for r in regions:
        if r in text:
            profile["region"] = r + "区" if r not in ["前海"] else r
            break

    biz_map = {
        "写字楼": "办公区", "大厦": "办公区", "科技园": "办公区", "工业园": "工业区",
        "小区": "住宅区", "花园": "住宅区", "公寓": "住宅区",
        "商场": "商业区", "购物中心": "商业区",
        "地铁": "交通枢纽", "公交": "交通枢纽", "车站": "交通枢纽",
        "工厂": "工业区", "物流": "工业区", "仓库": "工业区",
    }
    biz_types = []
    for k, v in biz_map.items():
        if k in text and v not in biz_types:
            biz_types.append(v)
    if biz_types:
        profile["business_type"] = biz_types

    import re
    numbers = re.findall(r'(\d+)', text)
    if numbers:
        nums = [int(n) for n in numbers if int(n) > 5]
        if len(nums) >= 1:
            profile["total_installed_power"] = nums[0]
        if len(nums) >= 2:
            profile["pile_count"] = nums[1]

    return profile


def _get_grid_code_from_meta(candidate: dict) -> str:
    """从 RAG 候选结果中提取 grid_code"""
    meta = candidate.get("metadata", {})
    return meta.get("grid_code", "")
