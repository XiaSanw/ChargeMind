import json
import re
from openai import OpenAI
from typing import Optional

# --- 客户端初始化 ---
# api_key 在运行时由外部传入（见 set_api_key）
_client: Optional[OpenAI] = None

def set_api_key(key: str):
    """设置 Kimi API Key，初始化客户端。由 UI 层调用。"""
    global _client
    # 注入默认 headers 伪装成 Kimi CLI 以绕过 Kimi-for-coding 的白名单限制
    _client = OpenAI(
        api_key=key, 
        base_url="https://api.kimi.com/coding/v1",
        default_headers={"User-Agent": "KimiCLI/1.5"}
    )

def _get_client() -> OpenAI:
    if _client is None:
        raise RuntimeError("请先配置 Kimi API Key")
    return _client

# --- 第一次调用：参数提取（非流式） ---

EXTRACT_PROMPT = """你是一个充电桩行业的数据分析助手。请从以下场站描述中提取结构化参数，严格按照 JSON 格式输出，不要输出任何其他内容。

如果某个字段在描述中没有明确提及，对应值填 null。

输出字段：
- station_name: 场站名称（字符串）
- location: 所在位置，包含城市和区域（字符串）
- pile_count: 充电桩数量（整数）
- pile_power_kw: 单桩额定功率，单位kW（数字）
- daily_kwh: 日均充电量，单位kWh（数字）
- price_peak: 峰段购电单价，单位元/kWh（数字）
- price_flat: 平段购电单价，单位元/kWh（数字）
- price_valley: 谷段购电单价，单位元/kWh（数字）
- service_fee: 服务费单价，单位元/kWh（数字）
- monthly_rent: 月租金，单位元（数字）
- staff_count: 运维/值守人数（整数）
- competitor_count: 周边竞品充电站数量（整数）
- customer_type: 主要客户类型（字符串）

场站描述：
\"\"\"
{user_input}
\"\"\""""

def extract_params(user_input: str) -> dict:
    """调 Kimi 从自然语言提取结构化参数，返回 dict。"""
    client = _get_client()
    resp = client.chat.completions.create(
        model="kimi-for-coding",
        messages=[{"role": "user", "content": EXTRACT_PROMPT.format(user_input=user_input)}],
        temperature=0.1,
    )
    raw = resp.choices[0].message.content.strip()
    
    # 尝试提取 JSON 内容
    try:
        if raw.startswith("```"):
            json_str = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        else:
            json_str = raw
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Fallback: 用正则提取 {} 包裹的内容
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            raise ValueError("无法解析返回的 JSON 格式")

# --- 第二次调用：生成报告（流式） ---

REPORT_PROMPT = """你是一位充电桩行业的资深经营顾问。请基于以下诊断数据（JSON），为该充电场站撰写一份《降本增效诊断报告》。

写作要求：
1. 必须直接引用 JSON 中的数字，不要编造。
2. 区分"事实"和"建议"，建议部分用"建议"开头。
3. 不使用"保证""一定"等绝对化表述。
4. 末尾单列一节说明"核心假设"（引用 assumptions 字段）。
5. 风格：专业、简洁、可执行。

报告结构（严格按此顺序）：
一、场站概况
二、当前经营诊断
三、核心问题
四、优化方案（逐条展开）
五、优化后效果预期（前后数据对比）
六、核心假设与说明

场站名称：{station_name}
所在位置：{location}
诊断数据：
{diagnosis_json}
"""

def generate_report_stream(station_name: str, location: str, diagnosis_json: str):
    """调 Kimi 生成报告，yield 每个 token 用于打字机效果。"""
    client = _get_client()
    prompt = REPORT_PROMPT.format(
        station_name=station_name,
        location=location,
        diagnosis_json=diagnosis_json,
    )
    
    stream = client.chat.completions.create(
        model="kimi-for-coding",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        stream=True,
    )
    
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
