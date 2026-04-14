# Prompt：用 PySide6 + Kimi API 开发充电桩智能诊断 Demo

请帮我开发一个完整的 Python 桌面应用。以下是全部规格说明。

---

## 一、项目概述

**产品名称**：AI驱动充电桩智能诊断平台 · Demo

**一句话描述**：用户点击按钮加载一段充电站描述 → 调 Kimi API 提取结构化参数 → 本地算法计算诊断结果 → 再调 Kimi API 流式生成降本增效报告。

**技术栈**：Python 3.10+ / PySide6 / openai SDK（兼容 Kimi 接口）

---

## 二、数据流与架构

整个应用是一条串行 pipeline，共三步：

```
用户点击 [开始诊断]
        │
        ▼
┌───────────────────┐
│ 步骤1: Kimi 提取   │  输入: 固定文本(str)
│   (非流式调用)      │  输出: 结构化参数(dict)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 步骤2: 本地算法     │  输入: 结构化参数(dict)
│   (纯Python计算)    │  输出: 诊断结果(dict)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 步骤3: Kimi 生成   │  输入: 诊断结果(JSON str) + 场站名/位置
│   (流式调用)        │  输出: Markdown 报告(逐token)
└───────────────────┘
```

三步全部在 **QThread 子线程** 中串行执行，通过 **Signal** 通知主线程更新 UI。主线程绝不做任何网络请求或阻塞计算。

---

## 三、项目文件结构

```
cwhdapp/
├── main.py                 # 入口：创建 QApplication，启动 MainWindow
├── constants.py            # 常量：演示文本、字段中文映射
├── core/
│   ├── __init__.py
│   ├── kimi_api.py         # Kimi API 封装：extract_params() + generate_report_stream()
│   ├── diagnosis.py        # 本地算法：diagnose()
│   └── worker.py           # QThread 工作线程：DiagnosisWorker
├── ui/
│   ├── __init__.py
│   ├── main_window.py      # 主窗口：布局、信号连接、UI 更新
│   └── styles.py           # QSS 样式表
└── requirements.txt        # PySide6>=6.5, openai>=1.0
```

**各文件的导入关系**：
```
main.py
  └── ui/main_window.py  (MainWindow)
        ├── core/worker.py  (DiagnosisWorker)
        │     ├── core/kimi_api.py  (extract_params, generate_report_stream)
        │     └── core/diagnosis.py  (diagnose)
        ├── constants.py  (DEMO_INPUT, FIELD_LABELS)
        └── ui/styles.py  (QSS)
```

---

## 四、各文件完整规格

### 4.1 constants.py

```python
DEMO_INPUT = (
    "我们在昆明市盘龙区有一个充电站，名字叫盘龙快充站。"
    "场地有20个120kW的直流快充桩，目前日均充电量约3000度。"
    "当前购电价是峰段1.2元、平段0.9元、谷段0.6元，服务费0.65元/度。"
    "场地月租金3万元，有3个运维人员。"
    "周边3公里内有5个竞品充电站。主要客户是网约车司机。"
    "目前没有储能设备，没有会员体系，支持分时段调价。"
)

# 提取字段 → 界面展示的中文标签
FIELD_LABELS = {
    "station_name": "场站名称",
    "location": "所在位置",
    "pile_count": "充电桩数量",
    "pile_power_kw": "单桩功率(kW)",
    "daily_kwh": "日均充电量(kWh)",
    "price_peak": "峰段电价(元/kWh)",
    "price_flat": "平段电价(元/kWh)",
    "price_valley": "谷段电价(元/kWh)",
    "service_fee": "服务费(元/kWh)",
    "monthly_rent": "月租金(元)",
    "staff_count": "运维人数",
    "competitor_count": "周边竞品数",
    "customer_type": "主要客群",
}

# FIELD_LABELS 的 key 顺序就是界面展示顺序
```

---

### 4.2 core/kimi_api.py

Kimi（Moonshot AI）提供 OpenAI 兼容接口，直接用 `openai` SDK 调用。

```python
import json
import re
from openai import OpenAI

# --- 客户端初始化 ---
# api_key 在运行时由外部传入（见 set_api_key）
_client: OpenAI | None = None

def set_api_key(key: str):
    """设置 Kimi API Key，初始化客户端。由 UI 层调用。"""
    global _client
    _client = OpenAI(api_key=key, base_url="https://api.moonshot.cn/v1")

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
        model="moonshot-v1-8k",
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
1. 所有数据必须引用 JSON 中的数字，禁止自行编造经营数据
2. 区分"事实"和"建议"，建议部分用"建议"二字开头
3. 禁止使用"保证""一定"等绝对化表述
4. 报告末尾列出"核心假设"，内容来自 JSON 中的 assumptions 字段
5. 语言风格：专业、简洁、可执行，面向场站运营管理者

报告结构（严格按此顺序）：
一、场站概况
二、当前经营诊断（引用 current 中的数据，列出收入、各项成本、利润）
三、核心问题（基于数据指出经营瓶颈）
四、优化方案（逐条展开 actions，每条写明：措施内容、生效机制、预期利润贡献）
五、优化后效果预期（引用 optimized 和 summary 做前后对比）
六、核心假设与说明

场站名称：{station_name}
所在位置：{location}

诊断数据：
\"\"\"
{diagnosis_json}
\"\"\""""

def generate_report_stream(station_name: str, location: str, diagnosis_json: str):
    """调 Kimi 流式生成报告，yield 每个 token（str）。"""
    client = _get_client()
    stream = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[{
            "role": "user",
            "content": REPORT_PROMPT.format(
                station_name=station_name,
                location=location,
                diagnosis_json=diagnosis_json,
            ),
        }],
        temperature=0.7,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
```

---

### 4.3 core/diagnosis.py

纯本地计算，不调任何外部 API。所有数字从输入参数推导。

```python
def diagnose(params: dict) -> dict:
    """
    输入: extract_params() 返回的 dict
    输出: 完整诊断结果 dict，结构见下方 return
    """
    daily_kwh = params.get("daily_kwh") or 3000
    annual_kwh = daily_kwh * 365

    price_peak = params.get("price_peak") or 1.2
    price_flat = params.get("price_flat") or 0.9
    price_valley = params.get("price_valley") or 0.6
    service_fee = params.get("service_fee") or 0.65
    monthly_rent = params.get("monthly_rent") or 30000
    staff_count = params.get("staff_count") or 3
    staff_monthly_pay = 6000  # 假设人均月薪

    # =====================
    # 当前经营测算
    # =====================
    # 假设当前峰/平/谷充电量占比
    cur_peak = 0.40
    cur_flat = 0.35
    cur_valley = 0.25

    avg_buy = price_peak * cur_peak + price_flat * cur_flat + price_valley * cur_valley
    avg_sell = avg_buy + service_fee

    rev = round(annual_kwh * avg_sell / 10000, 1)           # 年收入(万元)
    cost_power = round(annual_kwh * avg_buy / 10000, 1)     # 年购电成本
    cost_rent = round(monthly_rent * 12 / 10000, 1)         # 年租金
    cost_labor = round(staff_count * staff_monthly_pay * 12 / 10000, 1)  # 年人工
    cost_other = 0.96                                       # 年其他运维(固定)
    cost_total = round(cost_power + cost_rent + cost_labor + cost_other, 1)
    profit = round(rev - cost_total, 1)

    # =====================
    # 优化后测算
    # =====================
    # 策略: 谷段占比 25% → 40%，峰段 40% → 25%（通过引流调价实现）
    opt_peak = 0.25
    opt_flat = 0.35
    opt_valley = 0.40

    opt_avg_buy = price_peak * opt_peak + price_flat * opt_flat + price_valley * opt_valley
    opt_avg_sell = opt_avg_buy + service_fee

    # 引流提升充电量 15%
    opt_annual_kwh = round(annual_kwh * 1.15)
    # 排班优化: 减 0.5 人当量
    opt_staff = staff_count - 0.5

    opt_rev = round(opt_annual_kwh * opt_avg_sell / 10000, 1)
    opt_cost_power = round(opt_annual_kwh * opt_avg_buy / 10000, 1)
    opt_cost_rent = cost_rent
    opt_cost_labor = round(opt_staff * staff_monthly_pay * 12 / 10000, 1)
    opt_cost_other = cost_other
    opt_cost_total = round(opt_cost_power + opt_cost_rent + opt_cost_labor + opt_cost_other, 1)
    opt_profit = round(opt_rev - opt_cost_total, 1)

    improvement = round(opt_profit - profit, 1)

    # =====================
    # 优化动作（3 条）
    # =====================
    # 将 improvement 按比例拆分到 3 个动作，保证加总 = improvement
    raw_purchase = round((avg_buy - opt_avg_buy) * annual_kwh / 10000, 2)   # 购电成本节省
    raw_volume = round((opt_annual_kwh - annual_kwh) * service_fee / 10000, 2)  # 增量的服务费收益
    raw_labor = round(cost_labor - opt_cost_labor, 2)                        # 人工节省
    raw_total = raw_purchase + raw_volume + raw_labor

    # 按比例缩放使三项加总严格等于 improvement
    if raw_total != 0:
        scale = improvement / raw_total
    else:
        scale = 1.0
    act_purchase = round(raw_purchase * scale, 1)
    act_volume = round(raw_volume * scale, 1)
    act_labor = round(improvement - act_purchase - act_volume, 1)  # 余数兜底

    actions = [
        {
            "name": "峰谷结构优化",
            "type": "降本",
            "detail": (
                f"将谷段充电占比从{int(cur_valley*100)}%提升至{int(opt_valley*100)}%，"
                f"峰段从{int(cur_peak*100)}%降至{int(opt_peak*100)}%，"
                f"平均购电成本从{avg_buy:.2f}元降至{opt_avg_buy:.2f}元/kWh。"
            ),
            "profit_delta": act_purchase,
        },
        {
            "name": "夜间引流调价",
            "type": "增效",
            "detail": (
                f"夜间时段对网约车司机推出充电优惠，"
                f"预计日均充电量从{daily_kwh}kWh提升至{round(daily_kwh*1.15)}kWh，"
                f"年充电量增加{opt_annual_kwh - annual_kwh}kWh。"
            ),
            "profit_delta": act_volume,
        },
        {
            "name": "运维排班优化",
            "type": "降本",
            "detail": (
                f"根据时段负荷调整排班，高峰满员、低谷减员，"
                f"人力当量从{staff_count}人降至{opt_staff}人，"
                f"年节省约{act_labor}万元。"
            ),
            "profit_delta": act_labor,
        },
    ]

    return {
        "current": {
            "annual_kwh": annual_kwh,
            "avg_purchase_price": round(avg_buy, 2),
            "avg_sell_price": round(avg_sell, 2),
            "annual_revenue": rev,
            "annual_power_cost": cost_power,
            "annual_rent": cost_rent,
            "annual_labor": cost_labor,
            "annual_other": cost_other,
            "annual_total_cost": cost_total,
            "annual_profit": profit,
            "peak_ratio": cur_peak,
            "flat_ratio": cur_flat,
            "valley_ratio": cur_valley,
        },
        "optimized": {
            "annual_kwh": opt_annual_kwh,
            "avg_purchase_price": round(opt_avg_buy, 2),
            "avg_sell_price": round(opt_avg_sell, 2),
            "annual_revenue": opt_rev,
            "annual_power_cost": opt_cost_power,
            "annual_rent": opt_cost_rent,
            "annual_labor": opt_cost_labor,
            "annual_other": opt_cost_other,
            "annual_total_cost": opt_cost_total,
            "annual_profit": opt_profit,
            "peak_ratio": opt_peak,
            "flat_ratio": opt_flat,
            "valley_ratio": opt_valley,
        },
        "actions": actions,
        "summary": {
            "profit_improvement": improvement,
            "cost_reduction": round(cost_total - opt_cost_total, 1),
            "revenue_increase": round(opt_rev - rev, 1),
        },
        "assumptions": [
            f"人均月薪按{staff_monthly_pay}元估算",
            f"当前峰平谷充电占比按{int(cur_peak*100)}:{int(cur_flat*100)}:{int(cur_valley*100)}估算",
            "优化后日均充电量提升15%为经验估计值",
            f"其他运维成本按月均{round(cost_other/12*10000)}元估算",
        ],
    }
```

---

### 4.4 core/worker.py

QThread 子线程，串行执行三步，通过 Signal 通知主线程。

```python
import json
import time
from PySide6.QtCore import QThread, Signal
from core.kimi_api import extract_params, generate_report_stream
from core.diagnosis import diagnose


class DiagnosisWorker(QThread):
    # --- 信号 ---
    step_changed = Signal(str)        # → 更新步骤提示文字
    params_extracted = Signal(dict)   # → 填充 B 区(参数表)
    diagnosis_ready = Signal(dict)    # → 填充 C 区(诊断数据)
    report_token = Signal(str)        # → 追加到 D 区(报告，逐token)
    finished_all = Signal()           # → 全部完成
    error_occurred = Signal(str)      # → 显示错误

    def __init__(self, user_input: str, parent=None):
        super().__init__(parent)
        self.user_input = user_input

    def run(self):
        try:
            # 步骤 1
            self.step_changed.emit("正在提取场站参数...")
            params = extract_params(self.user_input)
            self.params_extracted.emit(params)

            # 步骤 2
            self.step_changed.emit("正在运行诊断分析...")
            time.sleep(1.5)  # 人为延迟，让用户感受到"算法在处理"
            result = diagnose(params)
            self.diagnosis_ready.emit(result)

            # 步骤 3
            self.step_changed.emit("正在生成诊断报告...")
            diagnosis_str = json.dumps(result, ensure_ascii=False, indent=2)
            for token in generate_report_stream(
                station_name=params.get("station_name", ""),
                location=params.get("location", ""),
                diagnosis_json=diagnosis_str,
            ):
                self.report_token.emit(token)

            self.step_changed.emit("诊断完成")
            self.finished_all.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))
```

---

### 4.5 ui/styles.py

用 QSS 定义全局视觉风格。以下是推荐方案，可以根据你的审美调整。

**风格方向**：浅色科技蓝白。白色背景 + 浅灰卡片 + 蓝色主按钮 + 圆角。

```python
GLOBAL_QSS = """
/* 全局 */
QMainWindow {
    background-color: #F5F7FA;
}
QLabel {
    color: #333333;
    font-size: 14px;
}

/* 卡片容器 —— 给 QFrame 加 objectName="card" 使用 */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E4E7ED;
    border-radius: 8px;
    padding: 16px;
}

/* 输入文本框 */
QTextEdit#inputBox {
    background-color: #FAFAFA;
    border: 1px solid #DCDFE6;
    border-radius: 6px;
    padding: 12px;
    font-size: 14px;
    color: #606266;
}

/* 报告文本框 */
QTextEdit#reportBox {
    background-color: #FFFFFF;
    border: 1px solid #E4E7ED;
    border-radius: 6px;
    padding: 16px;
    font-size: 14px;
    line-height: 1.8;
    color: #303133;
}

/* 主按钮 */
QPushButton#primaryBtn {
    background-color: #409EFF;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 15px;
    font-weight: bold;
}
QPushButton#primaryBtn:hover {
    background-color: #66B1FF;
}
QPushButton#primaryBtn:disabled {
    background-color: #A0CFFF;
}

/* 次要按钮 */
QPushButton#secondaryBtn {
    background-color: #FFFFFF;
    color: #409EFF;
    border: 1px solid #409EFF;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 14px;
}
QPushButton#secondaryBtn:hover {
    background-color: #ECF5FF;
}

/* 利润卡片 - 当前 */
QLabel#profitCurrent {
    font-size: 28px;
    font-weight: bold;
}

/* 利润卡片 - 优化后 */
QLabel#profitOptimized {
    font-size: 28px;
    font-weight: bold;
    color: #67C23A;
}

/* 动作标签 - 降本 */
QLabel#tagCostDown {
    background-color: #D9ECFF;
    color: #409EFF;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
}

/* 动作标签 - 增效 */
QLabel#tagRevenueUp {
    background-color: #FDF6EC;
    color: #E6A23C;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
}

/* 步骤提示 */
QLabel#stepLabel {
    color: #909399;
    font-size: 13px;
    padding: 8px 0;
}

/* 状态栏 */
QStatusBar {
    background-color: #EBEEF5;
    color: #909399;
    font-size: 12px;
}
"""
```

---

### 4.6 ui/main_window.py

这是最核心的文件。左右分栏布局。

**布局结构图**：

```
QMainWindow
├── QMenuBar
│   └── "设置" → "配置 API Key..."
├── centralWidget (QWidget)
│   └── QHBoxLayout (左右分栏)
│       ├── 左栏 QVBoxLayout (stretch=4)  ← 占 40%
│       │   ├── A区: 输入卡片 (QFrame#card)
│       │   │   ├── QLabel "场站描述"
│       │   │   ├── QTextEdit#inputBox (只读)
│       │   │   ├── QHBoxLayout
│       │   │   │   ├── QPushButton#secondaryBtn "加载演示案例"
│       │   │   │   └── QPushButton#primaryBtn "开始智能诊断"
│       │   ├── B区: 参数卡片 (QFrame#card)
│       │   │   ├── QLabel "AI 提取结果"
│       │   │   └── QGridLayout (2列 × 7行，展示13个字段)
│       │   ├── 步骤提示 QLabel#stepLabel
│       │   └── stretch
│       │
│       └── 右栏 QVBoxLayout (stretch=6)  ← 占 60%
│           ├── C区: 诊断数据卡片 (QFrame#card)
│           │   ├── QHBoxLayout (两张利润卡片并排)
│           │   │   ├── 当前利润卡片
│           │   │   └── 优化后利润卡片
│           │   ├── QLabel "优化动作"
│           │   └── QVBoxLayout (3张动作小卡片)
│           │
│           ├── D区: 报告卡片 (QFrame#card, 占右栏大部分)
│           │   ├── QLabel "诊断报告"
│           │   ├── QTextEdit#reportBox (只读，支持富文本)
│           │   └── QPushButton#secondaryBtn "复制报告"
│           └── stretch
│
└── QStatusBar "引擎版本: demo-rule-v1 | LLM: Kimi (moonshot-v1-8k)"
```

**关键逻辑（信号连接）**：

```python
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGridLayout, QTextEdit, QPushButton, QLabel, QFrame, QInputDialog,
    QApplication, QScrollArea)
from PySide6.QtCore import Qt
from core.worker import DiagnosisWorker
from core.kimi_api import set_api_key
from constants import DEMO_INPUT, FIELD_LABELS
from ui.styles import GLOBAL_QSS
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI驱动充电桩智能诊断平台 · Demo")
        self.resize(1400, 900)
        self.setStyleSheet(GLOBAL_QSS)
        self._api_key = ""
        self._report_text = ""  # 存报告纯文本，用于复制
        self._build_ui()
        self._build_menu()
        self._load_api_key()

    def _build_menu(self):
        menu = self.menuBar().addMenu("设置")
        action = menu.addAction("配置 API Key...")
        action.triggered.connect(self._on_set_api_key)

    def _on_set_api_key(self):
        key, ok = QInputDialog.getText(self, "配置 Kimi API Key",
            "请输入 Moonshot AI API Key:", text=self._api_key)
        if ok and key.strip():
            self._api_key = key.strip()
            set_api_key(self._api_key)
            self.statusBar().showMessage("API Key 已配置", 3000)
            # 保存到 config.json
            import json
            import os
            try:
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump({"api_key": self._api_key}, f)
            except Exception as e:
                self.statusBar().showMessage(f"保存配置失败: {e}", 3000)

    def _load_api_key(self):
        # 尝试从 config.json 加载 API Key
        import json
        import os
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    key = config.get("api_key", "")
                    if key:
                        self._api_key = key
                        set_api_key(self._api_key)
                        self.statusBar().showMessage("API Key 已从配置加载", 3000)
            except Exception:
                pass

    def _on_load_demo(self):
        self.input_edit.setPlainText(DEMO_INPUT)
        self.btn_start.setEnabled(True)

    def _on_start(self):
        if not self._api_key:
            self.step_label.setText("请先在「设置」菜单中配置 API Key")
            self.step_label.setStyleSheet("color: #F56C6C;")
            return
        # 重置 UI
        self.step_label.setStyleSheet("")
        self._report_text = ""
        self.report_edit.clear()
        self.btn_start.setEnabled(False)
        self.btn_load.setEnabled(False)

        self.worker = DiagnosisWorker(self.input_edit.toPlainText())
        self.worker.step_changed.connect(self._on_step)
        self.worker.params_extracted.connect(self._on_params)
        self.worker.diagnosis_ready.connect(self._on_diagnosis)
        self.worker.report_token.connect(self._on_report_token)
        self.worker.finished_all.connect(self._on_done)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _on_step(self, text):
        self.step_label.setText(text)

    def _on_params(self, params: dict):
        # 填充 B 区 QGridLayout
        row, col = 0, 0
        for key, label in FIELD_LABELS.items():
            val = params.get(key, "—")
            # 找到 B 区对应位置的 QLabel 并 setText
            # （具体实现取决于你怎么预创建这些 label）
        self.params_card.setVisible(True)

    def _on_diagnosis(self, result: dict):
        # 填充 C 区
        cur = result["current"]["annual_profit"]
        opt = result["optimized"]["annual_profit"]
        # 设置利润数字和颜色
        # 设置动作卡片
        self.diagnosis_card.setVisible(True)

    def _on_report_token(self, token: str):
        # 打字机效果：逐 token 追加
        self._report_text += token
        cursor = self.report_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self.report_edit.setTextCursor(cursor)
        self.report_edit.ensureCursorVisible()
        if not self.report_card.isVisible():
            self.report_card.setVisible(True)

    def _on_done(self):
        self.btn_start.setEnabled(True)
        self.btn_load.setEnabled(True)

    def _on_error(self, msg: str):
        self.step_label.setText(f"出错: {msg}")
        self.step_label.setStyleSheet("color: #F56C6C;")
        self.btn_start.setEnabled(True)
        self.btn_load.setEnabled(True)

    def _on_copy_report(self):
        QApplication.clipboard().setText(self._report_text)
        self.statusBar().showMessage("报告已复制到剪贴板", 3000)
```

> 上面的 `_on_params` 和 `_on_diagnosis` 是伪代码骨架，请在 `_build_ui()` 中创建好 B区和 C区的子控件，然后在回调中填充数据。

---

### 4.7 main.py

```python
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## 五、界面状态流转

```
初始状态
  B区(参数)隐藏, C区(诊断)隐藏, D区(报告)隐藏
  输入框空, [开始诊断] 禁用

→ 用户点击 [加载演示案例]
  输入框填入演示文本, [开始诊断] 启用

→ 用户点击 [开始诊断]
  两个按钮禁用, 步骤提示显示 "正在提取场站参数..."

→ 步骤1完成
  B区出现，展示13个提取字段
  步骤提示切换 "正在运行诊断分析..."

→ 步骤2完成
  C区出现，展示利润对比卡片和3条优化动作
  步骤提示切换 "正在生成诊断报告..."

→ 步骤3进行中
  D区出现，报告文字逐token追加（打字机效果）

→ 步骤3完成
  步骤提示切换 "诊断完成"
  [复制报告]按钮可用, 两个主按钮恢复
```

---

## 六、关键约束

1. **不卡界面**：所有网络请求和计算在 QThread 中执行。主线程只做 UI 更新。
2. **流式打字机**：第二次 Kimi 调用用 `stream=True`，每个 chunk 立即 emit 到界面。
3. **数字自洽**：`annual_profit = annual_revenue - annual_total_cost`，三条动作的 `profit_delta` 加总 = `profit_improvement`。
4. **错误处理**：API Key 未配置 / 网络异常 / JSON 解析失败，统一在步骤提示区用红色文字显示，不弹 dialog。
5. **复制报告**：把 D 区纯文本（非富文本）复制到系统剪贴板。

---

## 七、依赖安装

```bash
pip install PySide6>=6.5 openai>=1.0
```

---

请根据以上规格实现完整代码。每个文件都要写完整可运行的代码，不要省略。
