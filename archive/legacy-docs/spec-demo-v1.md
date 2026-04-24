# 充电桩智能诊断 Demo - 首版落地规格书

> 本文档是首版 demo 的唯一执行基准。prd-v0.1-deprecated 已废弃，prd-v0.2 作为远期参考保留。

## 1. 首版 Demo 做什么

一句话：用户看到一段固定的场站描述 → LLM 提取结构化参数 → 黑箱算法输出诊断结果 → LLM 生成降本增效报告。

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 固定输入文本  │ ──→ │ LLM 提取参数  │ ──→ │ 黑箱算法处理  │ ──→ │ LLM 生成报告  │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     界面展示            第1次调用             本地计算              第2次调用
```

### 1.1 首版做

- 一个固定的演示输入文本，可一键填入
- LLM 从文本中提取 ~10 个关键字段
- 黑箱根据字段输出诊断 JSON（硬编码 + 简单公式）
- LLM 读取诊断 JSON，生成一份结构化报告
- 界面分步展示：输入 → 提取结果 → 诊断数据 → 报告

### 1.2 首版不做

- 用户自由输入 / 参数编辑
- 多套场景模板切换
- 输入校验与冲突处理
- 报告导出（PDF/Word）
- 离线模式（首版依赖 LLM API）

---

## 2. 固定输入文本

```text
我们在昆明市盘龙区有一个充电站，名字叫盘龙快充站。场地有20个120kW的直流快充桩，
目前日均充电量约3000度。当前购电价是峰段1.2元、平段0.9元、谷段0.6元，服务费
0.65元/度。场地月租金3万元，有3个运维人员。周边3公里内有5个竞品充电站。
主要客户是网约车司机。目前没有储能设备，没有会员体系，支持分时段调价。
```

---

## 3. 第一次 LLM 调用：参数提取

### 3.1 提取目标字段（10 个）

| 字段 | 类型 | 说明 |
|------|------|------|
| `station_name` | string | 场站名称 |
| `location` | string | 所在位置 |
| `pile_count` | int | 充电桩数量 |
| `pile_power_kw` | number | 单桩功率(kW) |
| `daily_kwh` | number | 日均充电量(kWh) |
| `price_peak` | number | 峰段购电价(元/kWh) |
| `price_flat` | number | 平段购电价(元/kWh) |
| `price_valley` | number | 谷段购电价(元/kWh) |
| `service_fee` | number | 服务费(元/kWh) |
| `monthly_rent` | number | 月租金(元) |
| `staff_count` | int | 运维人数 |
| `competitor_count` | int | 周边竞品数 |
| `customer_type` | string | 主要客群 |

### 3.2 Prompt

```
你是一个充电桩行业的数据分析助手。请从以下场站描述中提取结构化参数，严格按照
JSON 格式输出，不要输出任何其他内容。

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
"""
{user_input}
"""
```

### 3.3 期望输出

```json
{
  "station_name": "盘龙快充站",
  "location": "昆明市盘龙区",
  "pile_count": 20,
  "pile_power_kw": 120,
  "daily_kwh": 3000,
  "price_peak": 1.2,
  "price_flat": 0.9,
  "price_valley": 0.6,
  "service_fee": 0.65,
  "monthly_rent": 30000,
  "staff_count": 3,
  "competitor_count": 5,
  "customer_type": "网约车司机"
}
```

---

## 4. 黑箱算法层

### 4.1 设计原则

- 输入：第一次 LLM 提取的 JSON
- 输出：一份诊断结果 JSON
- 首版用硬编码 + 简单四则运算实现，不需要模型
- 所有数字必须能从输入推导或解释，不能凭空出现

### 4.2 计算逻辑（伪代码）

```python
def diagnose(params):
    # ---- 基础测算 ----
    annual_kwh = params["daily_kwh"] * 365                    # 年充电量
    avg_purchase_price = (
        params["price_peak"] * 0.40
        + params["price_flat"] * 0.35
        + params["price_valley"] * 0.25
    )  # 当前峰平谷充电占比假设: 40/35/25

    annual_revenue = annual_kwh * (avg_purchase_price + params["service_fee"]) / 10000  # 万元
    annual_power_cost = annual_kwh * avg_purchase_price / 10000                          # 万元
    annual_rent = params["monthly_rent"] * 12 / 10000                                    # 万元
    annual_labor = params["staff_count"] * 6000 * 12 / 10000                             # 万元（人均6000/月）
    annual_other = 0.96                                                                  # 万元（维修/网络等，固定）
    annual_cost = annual_power_cost + annual_rent + annual_labor + annual_other
    annual_profit = annual_revenue - annual_cost

    # ---- 优化测算 ----
    # 优化策略：谷段占比从25%提升到40%，峰段从40%降到25%
    opt_avg_purchase = (
        params["price_peak"] * 0.25
        + params["price_flat"] * 0.35
        + params["price_valley"] * 0.40
    )
    # 优化后充电量提升15%（引流效果）
    opt_annual_kwh = annual_kwh * 1.15
    opt_revenue = opt_annual_kwh * (opt_avg_purchase + params["service_fee"]) / 10000
    opt_power_cost = opt_annual_kwh * opt_avg_purchase / 10000
    # 人工优化：3人减为2.5人当量（排班优化）
    opt_labor = 2.5 * 6000 * 12 / 10000
    opt_cost = opt_power_cost + annual_rent + opt_labor + annual_other
    opt_profit = opt_revenue - opt_cost

    return { ... }  # 见 4.3 输出结构
```

### 4.3 输出 JSON 结构

```json
{
  "current": {
    "annual_kwh": 1095000,
    "avg_purchase_price": 0.93,
    "annual_revenue": 173.1,
    "annual_power_cost": 101.8,
    "annual_rent": 36.0,
    "annual_labor": 21.6,
    "annual_other": 0.96,
    "annual_total_cost": 160.4,
    "annual_profit": 12.7,
    "peak_ratio": 0.40,
    "flat_ratio": 0.35,
    "valley_ratio": 0.25
  },
  "optimized": {
    "annual_kwh": 1259250,
    "avg_purchase_price": 0.78,
    "annual_revenue": 180.1,
    "annual_power_cost": 98.2,
    "annual_rent": 36.0,
    "annual_labor": 18.0,
    "annual_other": 0.96,
    "annual_total_cost": 153.2,
    "annual_profit": 26.9,
    "peak_ratio": 0.25,
    "flat_ratio": 0.35,
    "valley_ratio": 0.40
  },
  "actions": [
    {
      "name": "峰谷结构优化",
      "type": "降本",
      "detail": "将谷段充电占比从25%提升至40%，峰段从40%降至25%，降低平均购电成本。",
      "profit_delta": 3.6
    },
    {
      "name": "夜间引流调价",
      "type": "增效",
      "detail": "夜间时段对网约车司机推出充电优惠，预计提升日均充电量15%。",
      "profit_delta": 7.0
    },
    {
      "name": "运维排班优化",
      "type": "降本",
      "detail": "根据时段负荷调整排班，高峰3人、低谷1人轮转，人力成本降低约17%。",
      "profit_delta": 3.6
    }
  ],
  "summary": {
    "profit_improvement": 14.2,
    "cost_reduction": 7.2,
    "revenue_increase": 7.0
  },
  "assumptions": [
    "人均月薪按6000元估算",
    "当前峰平谷充电占比按40:35:25估算",
    "优化后充电量提升15%为经验估计值",
    "其他运维成本按月均800元估算"
  ]
}
```

> **注意**：以上数字为示意。实际开发时需要用 4.2 的公式跑一遍，确保 `annual_profit = annual_revenue - annual_total_cost` 等口径严格自洽。开发完成后必须做一次数字校验。

---

## 5. 第二次 LLM 调用：生成报告

### 5.1 Prompt

```
你是一位充电桩行业的资深经营顾问。现在你收到了一份充电场站的诊断数据（JSON格式），
请基于这些数据撰写一份《充电场站降本增效诊断报告》。

写作要求：
1. 所有数据必须直接引用 JSON 中的数字，不要自行编造任何经营数据
2. 区分"事实"和"建议"，建议部分用"建议"开头
3. 不使用"保证""一定"等绝对化表述
4. 在报告末尾列出"核心假设"，来自 JSON 中的 assumptions 字段
5. 语言风格：专业、简洁、可执行，面向场站运营管理者

报告结构（严格按此顺序）：
一、场站概况
二、当前经营诊断（引用 current 中的数据）
三、核心问题（基于 current 数据指出瓶颈）
四、优化方案（逐条展开 actions，每条说明措施、机制和预期利润贡献）
五、优化后效果预期（引用 optimized 和 summary 中的数据做前后对比）
六、核心假设与说明

场站名称：{station_name}
所在位置：{location}
诊断数据：
"""
{diagnosis_json}
"""
```

### 5.2 期望输出格式

纯文本，Markdown 格式，界面直接渲染即可。

---

## 6. 界面设计

### 6.1 布局

首版用最简单的**上下单列布局**，不做左右分栏。原因：单列布局开发成本低，信息按时间线从上往下铺开，符合"流程感"。

```
┌──────────────────────────────────────┐
│           顶部标题栏                   │
│   "AI驱动充电桩智能诊断平台 · Demo"    │
├──────────────────────────────────────┤
│  ① 输入区                            │
│  ┌────────────────────────────────┐  │
│  │ 固定文本（只读/灰底展示）        │  │
│  └────────────────────────────────┘  │
│  [加载演示案例]    [开始诊断]         │
├──────────────────────────────────────┤
│  ② 提取结果区（诊断后出现）           │
│  ┌────────────────────────────────┐  │
│  │ 字段名: 值   字段名: 值         │  │
│  │ 字段名: 值   字段名: 值   ...   │  │
│  └────────────────────────────────┘  │
├──────────────────────────────────────┤
│  ③ 诊断数据区（提取完成后出现）       │
│  ┌──────────┐  ┌──────────┐        │
│  │ 当前利润  │  │ 优化后利润 │        │
│  │  12.7万   │  │  26.9万   │        │
│  │  (灰/红)  │  │  (绿色)   │        │
│  └──────────┘  └──────────┘        │
│                                      │
│  优化动作：                           │
│  ┌────────────────────────────────┐  │
│  │ 1. 峰谷结构优化  降本 +3.6万    │  │
│  │ 2. 夜间引流调价  增效 +7.0万    │  │
│  │ 3. 运维排班优化  降本 +3.6万    │  │
│  └────────────────────────────────┘  │
├──────────────────────────────────────┤
│  ④ 报告区（逐字输出）                │
│  ┌────────────────────────────────┐  │
│  │ # 充电场站降本增效诊断报告       │  │
│  │                                │  │
│  │ ## 一、场站概况                  │  │
│  │ ...                            │  │
│  │ (打字机效果逐步展示)             │  │
│  └────────────────────────────────┘  │
│  [复制报告]                          │
└──────────────────────────────────────┘
```

### 6.2 状态流转

界面只有 4 个状态，线性推进：

| 状态 | 界面表现 | 触发条件 |
|------|----------|----------|
| **空闲** | 输入区空白，下方区域隐藏 | 初始状态 |
| **就绪** | 输入区已填充文本，[开始诊断] 可点击 | 点击 [加载演示案例] |
| **处理中** | 按钮禁用，显示当前步骤提示文字 | 点击 [开始诊断] |
| **完成** | 四个区域全部展示 | 报告输出完毕 |

处理中阶段的步骤提示：
1. "正在提取场站参数..."（第一次 LLM 调用）
2. "正在运行诊断分析..."（黑箱计算，可加 1-2 秒人为延迟）
3. "正在生成诊断报告..."（第二次 LLM 调用，流式输出）

### 6.3 视觉要点

- 利润数字：当前若亏损用红色，盈利用灰色；优化后用绿色加粗
- 优化动作：降本用蓝色标签，增效用橙色标签
- 报告区：等宽字体或正文字体均可，支持 Markdown 渲染
- 不需要图表、不需要动画（打字机效果除外）

### 6.4 技术实现要点（PySide6）

- 布局：`QVBoxLayout` 嵌套 `QScrollArea`，整体可滚动
- LLM 调用：`QThread` + `Signal`，避免主线程阻塞
- 打字机效果：报告区用 `QTimer` 逐字追加文本，或直接对接 LLM streaming API 逐 token 写入
- 步骤提示：一个 `QLabel` 动态切换文字即可

---

## 7. 开发检查清单

- [ ] 固定输入文本确认（第 2 节）
- [ ] 提取 Prompt 调试通过，输出 JSON 格式稳定
- [ ] 黑箱计算逻辑实现，数字口径自洽（revenue - cost = profit）
- [ ] 报告 Prompt 调试通过，报告内容引用数据准确
- [ ] 界面四个区域串通，状态流转正常
- [ ] 打字机效果流畅，UI 不卡顿
- [ ] 打包为 EXE 可在 Windows 上运行
