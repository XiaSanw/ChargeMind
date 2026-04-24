"""
诊断接口
POST /api/extract    → LLM 解析用户输入为结构化画像
POST /api/enrich     → 判断缺失字段，生成追问
POST /api/diagnose   → 双引擎并行诊断
"""
import os
import json
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from core.stub import algorithm_stub
from rag.retriever import retrieve_similar

router = APIRouter()

# 尝试初始化 LLM 客户端
try:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("KIMI_API_KEY", ""),
        base_url=os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
    )
    LLM_AVAILABLE = bool(os.getenv("KIMI_API_KEY"))
except Exception:
    client = None
    LLM_AVAILABLE = False

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "kimi-latest")

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


class EnrichRequest(BaseModel):
    profile: dict


class DiagnoseRequest(BaseModel):
    profile: dict


# 问卷字段定义（用于 enrich）
ENRICH_FIELDS = [
    {"key": "region", "question": "场站位于深圳哪个区？", "type": "select", "options": ["南山区","福田区","宝安区","龙岗区","龙华区","罗湖区","光明区","坪山区","盐田区","大鹏新区","前海"]},
    {"key": "business_type", "question": "周边主要业态是什么？", "type": "multi_select", "options": ["交通枢纽","商业区","办公区","住宅区","工业区","旅游景区"]},
    {"key": "total_installed_power", "question": "装机总功率大约多少 kW？", "type": "number"},
    {"key": "pile_count", "question": "有多少个充电桩？", "type": "number"},
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
        # Mock 解析：从用户输入中提取关键词
        text = req.user_input
        profile = _mock_extract(text)
        return {"profile": profile, "llm_used": False}

    prompt = f"""请从以下用户描述中提取充电场站的关键信息，输出为 JSON：

用户描述：""" + req.user_input + """

需要的字段：
- station_name: 场站名称（如有）
- region: 所在行政区（如南山区、福田区等）
- business_type: 周边业态列表（如["办公区","商业区"]）
- total_installed_power: 装机总功率（kW，数字）
- pile_count: 充电桩数量（数字）
- monthly_rent: 月租金（元，数字）
- staff_count: 运维人数（数字）
- avg_price: 平均电价+服务费（元/度，数字）
- peak_hour: 高峰时段（如"09:00"）

请只输出 JSON，不要其他内容。"""

    try:
        resp = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        profile = json.loads(content)
        # 清理空值
        profile = {k: v for k, v in profile.items() if v is not None and v != ""}
        return {"profile": profile, "llm_used": True}
    except Exception as e:
        # LLM 失败时 fallback
        profile = _mock_extract(req.user_input)
        return {"profile": profile, "llm_used": False, "error": str(e)}


@router.post("/enrich")
def enrich_profile(req: EnrichRequest):
    """
    判断缺失字段，返回下一个需要追问的问题。
    """
    profile = req.profile
    missing = []
    for field in ENRICH_FIELDS:
        key = field["key"]
        val = profile.get(key)
        if val is None or val == "" or val == []:
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
    双引擎并行诊断：算法 Stub + RAG
    返回综合报告
    """
    profile = req.profile

    # 1. 算法 Stub
    stub_result = algorithm_stub(profile)

    # 2. RAG 检索相似场站
    try:
        similar = retrieve_similar(profile, n_results=5)
    except Exception as e:
        similar = []

    # 3. RAG LLM 分析（如有 LLM）
    rag_analysis = ""
    if LLM_AVAILABLE and similar:
        rag_analysis = _rag_analyze(profile, similar)
    else:
        rag_analysis = _mock_rag_analysis(profile, similar)

    # 4. 综合报告
    report = build_report(profile, stub_result, similar, rag_analysis)

    return {
        "profile": profile,
        "algorithm": stub_result,
        "rag": {
            "similar_stations": similar,
            "analysis": rag_analysis,
        },
        "report": report,
    }


# ============ 辅助函数 ============

def _mock_extract(text: str) -> dict:
    """简单的关键词提取（无 LLM 时的 fallback）"""
    profile = {}
    # 区域
    regions = ["南山", "福田", "宝安", "龙岗", "龙华", "罗湖", "光明", "坪山", "盐田", "大鹏", "前海"]
    for r in regions:
        if r in text:
            profile["region"] = r + "区" if r not in ["前海"] else r
            break
    # 业态
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

    # 功率/桩数（简单数字提取）
    import re
    numbers = re.findall(r'(\d+)', text)
    if numbers:
        # 假设第一个大数字是功率，第二个是桩数
        nums = [int(n) for n in numbers if int(n) > 5]
        if len(nums) >= 1:
            profile["total_installed_power"] = nums[0]
        if len(nums) >= 2:
            profile["pile_count"] = nums[1]

    return profile


def _rag_analyze(profile: dict, similar: list) -> str:
    """用 LLM 分析相似场站"""
    similar_text = "\n\n".join([
        f"【场站 {i+1}】{s['document']}\n利用率: {s['metadata'].get('avg_utilization', '未知')}，"
        f"日均充电量: {s['metadata'].get('avg_daily_energy_kwh', '未知')}度"
        for i, s in enumerate(similar[:3])
    ])

    prompt = f"""你是一位充电场站运营专家。请根据以下相似场站的数据，分析其成功或失败的关键因素，并给出优化建议。

用户场站画像：
- 位置：{profile.get('region', '未知')}
- 业态：{profile.get('business_type', [])}
- 装机功率：{profile.get('total_installed_power', '未知')}kW
- 桩数：{profile.get('pile_count', '未知')}

相似场站数据：
{similar_text}

请给出3-5条具体的、可落地的优化建议。每条建议标注来源：
- [知识库类比]：基于相似场站的实际数据
- [行业规律]：基于行业普遍认知
"""

    try:
        resp = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"分析生成失败：{e}"


def _mock_rag_analysis(profile: dict, similar: list) -> str:
    """无 LLM 时的 mock RAG 分析"""
    region = profile.get("region", "未知")
    biz = profile.get("business_type", [])
    biz_str = biz[0] if biz else "未知"

    lines = [
        "## 基于知识库的分析",
        "",
        f"在{region}的{biz_str}充电站中，我们找到了{len(similar)}个相似场站进行对比。",
        "",
    ]

    for i, s in enumerate(similar[:3], 1):
        meta = s["metadata"]
        lines.append(
            f"**相似场站 {i}**：{meta.get('station_name', '未知')} — "
            f"利用率 {meta.get('avg_utilization', '未知')}，"
            f"日均充电量 {meta.get('avg_daily_energy_kwh', '未知')}度"
        )

    lines.extend([
        "",
        "### 优化建议",
        "",
        "1. **[知识库类比]** 参考相似场站的运营数据，当前利用率有较大提升空间，建议优化峰谷电价结构，引导用户在低谷时段充电。",
        "2. **[行业规律]** 周边业态为办公区，建议在工作日午间（11:00-14:00）推出限时优惠，吸引白领用户。",
        "3. **[行业规律]** 增加充电桩数量或提升单桩功率，可显著提高场站吸引力和周转率。",
    ])

    return "\n".join(lines)


def build_report(profile, stub_result, similar, rag_analysis) -> dict:
    """合并双引擎输出为综合报告"""
    region = profile.get("region", "未知")
    biz = profile.get("business_type", [])

    # 判断是否有明显冲突
    conflicts = []
    if stub_result["predicted_utilization"] < 0.05 and biz and "交通枢纽" in biz:
        conflicts.append({
            "type": "低预测 vs 高潜力业态",
            "algorithm": "预测利用率低",
            "rag": "交通枢纽通常利用率较高",
            "resolution": "建议优先参考知识库类比",
        })

    return {
        "executive_summary": (
            f"该场站位于{region}，属于{','.join(biz) if biz else '未知'}。"
            f"算法预测年利润约 {stub_result['annual_profit']} 元，"
            f"预测利用率 {stub_result['predicted_utilization']}。"
            f"知识库检索到 {len(similar)} 个相似场站供对比参考。"
        ),
        "algorithm_prediction": stub_result,
        "rag_analysis": rag_analysis,
        "conflicts": conflicts,
        "recommendations": [
            {
                "title": "优化峰谷电价结构",
                "source": "[算法预测] + [知识库类比]",
                "detail": "当前预测利用率偏低，参考相似场站数据，通过调整峰谷价差可引导用户行为，提升低谷时段利用率。",
            },
            {
                "title": "精准营销定位",
                "source": "[知识库类比]",
                "detail": f"针对{biz[0] if biz else '周边'}用户特征，制定差异化营销策略。",
            },
            {
                "title": "运维成本优化",
                "source": "[算法预测]",
                "detail": f"当前运维人员 {profile.get('staff_count', '未知')} 人，根据预测充电量评估人力配置合理性。",
            },
        ],
    }
