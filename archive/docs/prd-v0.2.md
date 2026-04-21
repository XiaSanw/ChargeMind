# AI驱动充电桩智能诊断平台 - 演示版需求文档 v0.2

## 1. 文档目的

本版本用于将初始构想收敛为一个可落地的演示版产品方案。

本版本的核心原则：

- 当前阶段目标是完成一个可信的咨询闭环 demo，不宣称已接入真实算法模型
- 算法层先以规则引擎 + 案例模板 + 简单计算的方式实现
- LLM 负责两件事：非结构化信息提取、基于结构化结果生成诊断报告
- 所有输出必须可解释、可回溯，避免“只有结论、没有过程”

---

## 2. 项目定位

将已有的场站经营数据认知，封装成一个可演示的 AI 咨询工具。

用户输入某个充电场站的基本信息后，系统完成以下闭环：

1. 提取结构化参数
2. 基于规则化伪算法层生成当前经营测算、问题诊断和优化空间
3. 基于结构化诊断结果生成一份“降本增效”分析报告

对外建议表述：

- 我们已经具备丰富的场站经营数据和咨询经验
- 当前演示版先完成咨询流程产品化
- 中间的诊断引擎可在后续逐步替换为真实算法模型

不建议表述：

- 已具备成熟、泛化、可直接商用的收益预测模型
- 已实现精确 IRR 预测和真实购电优化调度

---

## 3. MVP 目标

搭建一个可在 Windows 上直接运行的 EXE 演示程序，完成以下体验：

1. 用户输入一段场站描述，或在表单中补充/修正字段
2. 系统展示提取后的结构化参数，并允许用户确认
3. 系统基于伪算法层输出当前经营情况、主要问题、优化建议和优化后结果
4. 系统生成一份结构化、可阅读的诊断报告

### 3.1 当前阶段追求

- 演示链路完整
- 结果口径自洽
- 建议内容看起来专业且可执行
- 每个结论都能追溯到中间结构化数据

### 3.2 当前阶段不追求

- 接入真实算法模型
- 接入真实 LLM API 作为必需条件
- 支持开放域、任意质量的自然语言输入
- 支持 PDF/Excel/图片解析
- 输出严格财务意义上的 IRR、NPV 等投资指标

---

## 4. 产品边界

本 demo 的本质是“咨询推演引擎”，不是“生产级预测系统”。

系统输出分为四层：

1. 输入事实
2. 规则推导
3. 结果测算
4. 文本报告

任何文本结论都必须基于前 3 层中的结构化数据，不允许 LLM 自行补充核心经营事实。

---

## 5. 系统架构

```text
用户输入（自然语言 + 表单补充）
    ↓
参数提取层
    - 从输入文本中提取结构化字段
    - 缺失字段使用默认值或要求用户确认
    ↓
场站诊断引擎（伪算法层）
    - 场站分类
    - 经营测算
    - 问题诊断
    - 优化动作生成
    - 优化后结果汇总
    ↓
报告生成层
    - 读取结构化诊断结果
    - 生成人可读的诊断报告
    ↓
结果展示
```

### 5.1 各层职责

| 层级 | 职责 | 当前阶段实现方式 |
|------|------|------------------|
| 参数提取层 | 从用户描述中提取场站参数，并补足默认值 | 离线规则提取或 LLM 提取，结合字段校验 |
| 场站诊断引擎 | 输出经营测算、问题诊断、优化动作与优化结果 | 规则引擎 + 案例模板 + 简单公式 |
| 报告生成层 | 基于结构化结果生成诊断报告 | 模板 + LLM 可选增强 |
| 展示层 | 显示输入、过程、结果与报告 | PySide6 桌面界面 |

---

## 6. 核心演示链路

### 6.1 用户流程

1. 用户输入一段场站描述
2. 系统提取结构化字段
3. 系统展示字段，并允许用户修改
4. 用户点击“开始诊断”
5. 诊断引擎输出：
   - 当前经营面板
   - 核心问题
   - 优化动作清单
   - 优化后经营结果
6. 报告生成层输出最终分析报告

### 6.2 演示版推荐交互方式

优先采用“自然语言输入 + 结构化确认”的方式，而不是完全自由输入直出结果。

原因：

- 可显著降低提取错误带来的演示风险
- 用户会感觉系统“确实理解了输入”
- 可以对缺失字段进行显式补齐

---

## 7. 伪算法层设计原则

### 7.1 设计原则

- 不直接输出一个利润结论，必须输出可解释的经营拆解
- 不追求精确预测，追求“合理、稳定、可讲明白”
- 所有结果来自“规则 + 模板 + 缩放”
- 每个优化建议都必须有量化贡献

### 7.2 实现思路

伪算法层建议采用四步：

1. 场站分类
   - 如城市快充站、高速站、园区站、商圈站
2. 问题识别
   - 如利用率偏低、峰段成本过高、租金压力大、竞争过强
3. 模板匹配
   - 从预设场景模板中选择最接近的经营样本
4. 数值缩放
   - 根据输入字段对模板的收入、成本、利用率、优化空间做线性或区间映射

### 7.3 推荐首版场景模板

- 模板 A：低利用率亏损站
- 模板 B：高租金压力站
- 模板 C：峰段购电成本偏高站
- 模板 D：竞争激烈但可引流改善站
- 模板 E：经营基本健康但有优化空间站

---

## 8. 输入字段表

以下字段为“结构化参数确认区”需要展示的字段。

### 8.1 输入字段定义

| 字段名 | 中文名 | 类型 | 单位 | 是否必填 | 示例 | 来源 | 说明 |
|--------|--------|------|------|----------|------|------|------|
| `station_name` | 场站名称 | string | - | 是 | 盘龙快充站 | 用户输入 | 用于报告展示 |
| `location_city` | 所在城市 | string | - | 是 | 昆明 | 用户输入 | 用于电价、区域说明 |
| `location_area` | 所在区域 | string | - | 否 | 盘龙区 | 用户输入 | 用于报告展示 |
| `station_type` | 场站类型 | enum | - | 是 | 城市快充站 | 推断/用户确认 | 枚举值见 8.2 |
| `pile_count` | 充电桩数量 | integer | 个 | 是 | 20 | 用户输入 | 必须大于 0 |
| `pile_power_kw` | 单桩额定功率 | number | kW | 是 | 120 | 用户输入 | 用于能力上限判断 |
| `gun_count` | 充电枪数量 | integer | 个 | 否 | 40 | 用户输入/默认 | 可缺省 |
| `transformer_capacity_kva` | 变压器容量 | number | kVA | 否 | 2500 | 用户输入 | 当前 demo 可选 |
| `daily_charge_kwh` | 日均充电量 | number | kWh/日 | 是 | 3000 | 用户输入 | 核心经营字段 |
| `utilization_rate` | 利用率 | number | 0-1 | 否 | 0.35 | 用户输入/推导 | 若与日充电量冲突，需提示 |
| `service_fee_per_kwh` | 服务费单价 | number | 元/kWh | 否 | 0.65 | 用户输入/默认 | 未提供时可用默认值 |
| `sell_price_peak` | 峰段销售单价 | number | 元/kWh | 否 | 1.85 | 用户输入/默认 | 含电费和服务费时需在说明中标注 |
| `sell_price_flat` | 平段销售单价 | number | 元/kWh | 否 | 1.55 | 用户输入/默认 | 当前 demo 可选 |
| `sell_price_valley` | 谷段销售单价 | number | 元/kWh | 否 | 1.20 | 用户输入/默认 | 当前 demo 可选 |
| `purchase_price_peak` | 峰段购电单价 | number | 元/kWh | 是 | 1.20 | 用户输入 | 核心成本字段 |
| `purchase_price_flat` | 平段购电单价 | number | 元/kWh | 是 | 0.90 | 用户输入 | 核心成本字段 |
| `purchase_price_valley` | 谷段购电单价 | number | 元/kWh | 是 | 0.60 | 用户输入 | 核心成本字段 |
| `peak_charge_ratio` | 当前峰段充电占比 | number | 0-1 | 否 | 0.40 | 推导/默认 | 三段占比之和应为 1 |
| `flat_charge_ratio` | 当前平段充电占比 | number | 0-1 | 否 | 0.35 | 推导/默认 | 三段占比之和应为 1 |
| `valley_charge_ratio` | 当前谷段充电占比 | number | 0-1 | 否 | 0.25 | 推导/默认 | 三段占比之和应为 1 |
| `monthly_rent` | 月租金 | number | 元/月 | 是 | 30000 | 用户输入 | 固定成本字段 |
| `staff_count` | 运维/值守人数 | integer | 人 | 是 | 3 | 用户输入 | 固定成本字段 |
| `avg_staff_cost` | 人均月成本 | number | 元/月 | 否 | 6000 | 默认 | 未提供时使用默认值 |
| `monthly_other_om_cost` | 其他月运维成本 | number | 元/月 | 否 | 8000 | 默认/用户输入 | 包括维修、保洁、网络等 |
| `nearby_competitor_count` | 周边竞品数量 | integer | 个 | 否 | 5 | 用户输入 | 用于竞争强度判断 |
| `major_customer_type` | 主要客户类型 | enum | - | 否 | 网约车司机 | 用户输入 | 枚举值见 8.2 |
| `can_time_based_pricing` | 是否可分时调价 | boolean | - | 否 | true | 默认/用户确认 | 影响优化建议 |
| `has_energy_storage` | 是否有储能 | boolean | - | 否 | false | 用户输入 | 影响购电优化建议 |
| `has_membership_system` | 是否有会员体系 | boolean | - | 否 | false | 用户输入 | 影响引流策略建议 |
| `parking_fee_policy` | 停车费策略 | enum | - | 否 | 免停车费 | 用户输入/默认 | 影响引流转化 |
| `notes` | 其他说明 | string | - | 否 | 夜间订单多 | 用户输入 | 进入报告补充说明 |

### 8.2 枚举值约定

`station_type` 可选值：

- 城市快充站
- 高速站
- 园区站
- 商圈站
- 社区站
- 其他

`major_customer_type` 可选值：

- 网约车司机
- 私家车主
- 物流车队
- 出租车
- 混合客群
- 其他

`parking_fee_policy` 可选值：

- 免停车费
- 限时免费
- 正常收费
- 未知

### 8.3 输入校验规则

| 规则编号 | 规则说明 | 处理方式 |
|----------|----------|----------|
| R1 | `pile_count` 必须大于 0 | 不通过则禁止诊断 |
| R2 | `daily_charge_kwh` 必须大于 0 | 不通过则禁止诊断 |
| R3 | 峰平谷购电单价必须都存在 | 缺失时提示用户补充或采用默认城市模板 |
| R4 | `peak_charge_ratio + flat_charge_ratio + valley_charge_ratio = 1` | 不满足时自动归一化并提示 |
| R5 | `utilization_rate` 与 `daily_charge_kwh` 冲突时，需要提示 | 用户确认后继续 |
| R6 | 布尔条件会影响建议生成 | 如无储能则不输出储能相关建议 |
| R7 | 缺失的非核心字段可使用默认值 | 在报告中列入“模型假设” |

### 8.4 关键默认值建议

| 字段名 | 默认值建议 | 说明 |
|--------|------------|------|
| `avg_staff_cost` | 6000 元/月/人 | 演示用统一口径 |
| `monthly_other_om_cost` | 8000 元/月 | 演示用统一口径 |
| `service_fee_per_kwh` | 0.60 元/kWh | 若未给出服务费时使用 |
| `peak_charge_ratio` | 0.40 | 默认峰段占比较高 |
| `flat_charge_ratio` | 0.35 | 默认平段占比 |
| `valley_charge_ratio` | 0.25 | 默认谷段占比较低 |
| `can_time_based_pricing` | true | 演示中默认支持策略调整 |
| `has_energy_storage` | false | 保守默认 |
| `has_membership_system` | false | 保守默认 |

---

## 9. 伪算法层输出字段表

伪算法层必须输出完整结构化结果，供界面展示和报告生成层使用。

### 9.1 输出对象结构

```json
{
  "station_profile": {},
  "current_metrics": {},
  "diagnosis": {},
  "optimization_actions": [],
  "optimized_metrics": {},
  "meta": {}
}
```

### 9.2 `station_profile`

| 字段名 | 中文名 | 类型 | 单位 | 示例 | 说明 |
|--------|--------|------|------|------|------|
| `station_type` | 场站类型 | string | - | 城市快充站 | 用于报告分类 |
| `business_stage` | 经营状态 | string | - | 成熟运营期 | 可选值：爬坡期/成熟期/承压期 |
| `annual_charge_kwh` | 年充电量 | number | kWh/年 | 1095000 | 由日均充电量换算 |
| `current_utilization_rate` | 当前利用率 | number | 0-1 | 0.35 | 若缺失可推导 |
| `avg_sell_price` | 平均售电单价 | number | 元/kWh | 1.42 | 用于收入测算 |
| `avg_purchase_price` | 平均购电单价 | number | 元/kWh | 0.89 | 按峰平谷占比加权 |
| `competition_level` | 竞争强度 | string | - | 高 | 低/中/高 |
| `customer_profile` | 客群画像 | string | - | 网约车司机为主 | 用于建议定制 |

### 9.3 `current_metrics`

| 字段名 | 中文名 | 类型 | 单位 | 示例 | 说明 |
|--------|--------|------|------|------|------|
| `annual_revenue` | 年收入 | number | 万元/年 | 155.4 | 收入总额 |
| `annual_power_cost` | 年购电成本 | number | 万元/年 | 97.8 | 购电成本 |
| `annual_rent_cost` | 年租金成本 | number | 万元/年 | 36.0 | 月租金乘 12 |
| `annual_labor_cost` | 年人工成本 | number | 万元/年 | 21.6 | 人数乘人均成本 |
| `annual_other_om_cost` | 年其他运维成本 | number | 万元/年 | 9.6 | 包含维修等 |
| `annual_total_cost` | 年总成本 | number | 万元/年 | 165.0 | 以上成本汇总 |
| `current_annual_profit` | 当前年利润 | number | 万元/年 | -9.6 | 收入减总成本 |
| `current_profit_margin` | 当前利润率 | number | 0-1 | -0.06 | 利润除收入 |
| `peak_power_ratio` | 当前峰段占比 | number | 0-1 | 0.40 | 当前时段结构 |
| `flat_power_ratio` | 当前平段占比 | number | 0-1 | 0.35 | 当前时段结构 |
| `valley_power_ratio` | 当前谷段占比 | number | 0-1 | 0.25 | 当前时段结构 |
| `break_even_utilization_rate` | 盈亏平衡利用率 | number | 0-1 | 0.43 | 可解释指标，优先替代 IRR |

### 9.4 `diagnosis`

| 字段名 | 中文名 | 类型 | 单位 | 示例 | 说明 |
|--------|--------|------|------|------|------|
| `primary_issues` | 核心问题列表 | string[] | - | ["利用率偏低", "固定成本偏高"] | 供报告引用 |
| `issue_summary` | 问题摘要 | string | - | 当前场站主要受利用率不足和固定成本压力影响 | 供界面展示 |
| `utilization_gap_pct` | 利用率差距 | number | pct | -10 | 相对目标值差距 |
| `valley_ratio_gap_pct` | 谷段占比差距 | number | pct | -15 | 相对目标值差距 |
| `rent_pressure_level` | 租金压力等级 | string | - | 高 | 低/中/高 |
| `competition_pressure_level` | 竞争压力等级 | string | - | 高 | 低/中/高 |
| `diagnosis_tags` | 诊断标签 | string[] | - | ["低利用率", "高峰段成本"] | 供模板渲染 |

### 9.5 `optimization_actions`

每个优化动作必须包含以下字段。

| 字段名 | 中文名 | 类型 | 单位 | 示例 | 说明 |
|--------|--------|------|------|------|------|
| `action_id` | 动作编号 | string | - | ACT-01 | 唯一标识 |
| `action_name` | 动作名称 | string | - | 夜间引流调价 | 展示字段 |
| `action_type` | 动作类型 | string | - | 增效 | 降本/增效 |
| `mechanism` | 生效机制 | string | - | 吸引夜间补能，提高谷段充电量 | 必须可解释 |
| `expected_revenue_delta` | 预期收入变化 | number | 万元/年 | 8.2 | 可为正或 0 |
| `expected_cost_delta` | 预期成本变化 | number | 万元/年 | -1.3 | 降本为负数 |
| `expected_profit_delta` | 预期利润变化 | number | 万元/年 | 9.5 | 核心字段 |
| `expected_utilization_delta` | 预期利用率变化 | number | pct | 6 | 与当前相比 |
| `expected_kwh_delta` | 预期充电量变化 | number | kWh/年 | 150000 | 可为 0 |
| `priority` | 优先级 | integer | - | 1 | 1 最高 |
| `difficulty` | 实施难度 | string | - | 中 | 低/中/高 |
| `preconditions` | 前提条件 | string[] | - | ["支持分时调价"] | 不满足则不展示 |
| `risk_note` | 风险提示 | string | - | 可能带来峰段单价敏感用户流失 | 控制 LLM 过度乐观 |

### 9.6 `optimized_metrics`

| 字段名 | 中文名 | 类型 | 单位 | 示例 | 说明 |
|--------|--------|------|------|------|------|
| `optimized_annual_revenue` | 优化后年收入 | number | 万元/年 | 168.5 | 收入结果 |
| `optimized_annual_total_cost` | 优化后年总成本 | number | 万元/年 | 154.2 | 成本结果 |
| `optimized_annual_profit` | 优化后年利润 | number | 万元/年 | 14.3 | 利润结果 |
| `profit_improvement` | 利润提升额 | number | 万元/年 | 23.9 | 与当前比较 |
| `target_utilization_rate` | 目标利用率 | number | 0-1 | 0.46 | 优化目标 |
| `optimized_peak_ratio` | 优化后峰段占比 | number | 0-1 | 0.25 | 时段结构变化 |
| `optimized_flat_ratio` | 优化后平段占比 | number | 0-1 | 0.35 | 时段结构变化 |
| `optimized_valley_ratio` | 优化后谷段占比 | number | 0-1 | 0.40 | 时段结构变化 |
| `break_even_status` | 盈亏平衡状态 | string | - | 达到盈亏平衡 | 便于报告表达 |

### 9.7 `meta`

| 字段名 | 中文名 | 类型 | 单位 | 示例 | 说明 |
|--------|--------|------|------|------|------|
| `engine_version` | 引擎版本 | string | - | demo-rule-v1 | 便于追踪 |
| `scenario_template` | 使用模板 | string | - | 模板 A | 便于调试和展示 |
| `confidence_level` | 置信级别 | string | - | demo | 当前固定为 demo |
| `assumptions` | 核心假设 | string[] | - | ["支持分时调价", "维持现有租金"] | 报告必须展示 |
| `warnings` | 风险提示 | string[] | - | ["未提供真实服务费单价，已采用默认值"] | 控制结果边界 |

---

## 10. 伪算法层逻辑建议

### 10.1 当前经营测算

首版建议只做以下几类测算：

- 年充电量
- 平均售电单价
- 平均购电单价
- 年收入
- 年成本
- 年利润
- 盈亏平衡利用率

不建议首版实现：

- IRR
- NPV
- 多年现金流预测
- 真实购电调度优化

### 10.2 优化动作生成规则

首版可以预置 5 到 8 个动作模板，并根据输入条件控制是否出现：

| 动作名称 | 适用条件 | 主要收益来源 |
|----------|----------|--------------|
| 夜间引流调价 | `can_time_based_pricing = true` | 提升谷段充电量 |
| 网约车会员包 | `major_customer_type = 网约车司机` | 提升复购和黏性 |
| 峰谷结构优化 | `can_time_based_pricing = true` 或 `has_energy_storage = true` | 降低平均购电成本 |
| 运维排班优化 | `staff_count >= 3` | 降低人工成本 |
| 租金重谈建议 | `monthly_rent` 偏高 | 降低固定成本 |
| 竞品差异化营销 | `nearby_competitor_count >= 3` | 抬升利用率 |
| 储能协同建议 | `has_energy_storage = true` | 优化峰谷电价结构 |

### 10.3 输出口径要求

- 所有金额统一使用“万元/年”
- 利用率统一使用 0 到 1 的数值格式，界面展示时转为百分比
- 时段占比统一使用 0 到 1，三者总和为 1
- `expected_profit_delta` 必须等于 `expected_revenue_delta - expected_cost_delta` 的口径一致版本
- `profit_improvement` 必须等于 `optimized_annual_profit - current_annual_profit`

---

## 11. 报告生成层要求

报告层只读取伪算法层输出，不自行创造经营事实。

### 11.1 报告结构

1. 场站概况
2. 当前经营诊断
3. 核心问题归因
4. 降本建议
5. 增效建议
6. 优化后效果预期
7. 核心假设与风险提示

### 11.2 报告写作约束

- 必须引用结构化字段中的数据
- 必须区分“事实”“假设”“建议”
- 不允许输出“保证盈利”“一定提升”等绝对化表述
- 若某项建议依赖前提条件，必须写明
- 若使用默认值或估算值，必须在风险提示中说明

### 11.3 报告生成输入

报告生成层至少读取以下对象：

- `station_profile`
- `current_metrics`
- `diagnosis`
- `optimization_actions`
- `optimized_metrics`
- `meta.assumptions`
- `meta.warnings`

---

## 12. 演示示例

### 12.1 示例输入

> 我们在昆明市盘龙区有一个充电站，名字叫盘龙快充站。场地有20个120kW的直流快充桩，目前日均充电量约3000度。当前电价是峰段1.2元、平段0.9元、谷段0.6元。场地月租金3万元，有3个运维人员。周边3公里内有5个竞品充电站。主要客户是网约车司机。

说明：

- 本版示例不强制要求用户同时提供“利用率”
- 若提供的利用率与日充电量冲突，以日充电量为主，并提示用户确认

### 12.2 示例提取结果

```json
{
  "station_name": "盘龙快充站",
  "location_city": "昆明",
  "location_area": "盘龙区",
  "station_type": "城市快充站",
  "pile_count": 20,
  "pile_power_kw": 120,
  "daily_charge_kwh": 3000,
  "purchase_price_peak": 1.2,
  "purchase_price_flat": 0.9,
  "purchase_price_valley": 0.6,
  "monthly_rent": 30000,
  "staff_count": 3,
  "nearby_competitor_count": 5,
  "major_customer_type": "网约车司机",
  "can_time_based_pricing": true,
  "has_energy_storage": false,
  "has_membership_system": false
}
```

### 12.3 示例伪算法输出

```json
{
  "station_profile": {
    "station_type": "城市快充站",
    "business_stage": "承压期",
    "annual_charge_kwh": 1095000,
    "current_utilization_rate": 0.19,
    "avg_sell_price": 1.46,
    "avg_purchase_price": 0.93,
    "competition_level": "高",
    "customer_profile": "网约车司机为主"
  },
  "current_metrics": {
    "annual_revenue": 159.9,
    "annual_power_cost": 101.8,
    "annual_rent_cost": 36.0,
    "annual_labor_cost": 21.6,
    "annual_other_om_cost": 9.6,
    "annual_total_cost": 169.0,
    "current_annual_profit": -9.1,
    "current_profit_margin": -0.06,
    "peak_power_ratio": 0.40,
    "flat_power_ratio": 0.35,
    "valley_power_ratio": 0.25,
    "break_even_utilization_rate": 0.24
  },
  "diagnosis": {
    "primary_issues": ["利用率偏低", "峰段充电占比偏高", "租金成本偏高"],
    "issue_summary": "当前场站主要问题是充电量不足，固定成本无法被有效摊薄，同时峰段占比较高导致购电成本偏高。",
    "utilization_gap_pct": -5,
    "valley_ratio_gap_pct": -12,
    "rent_pressure_level": "高",
    "competition_pressure_level": "高",
    "diagnosis_tags": ["低利用率", "高固定成本", "高竞争压力"]
  },
  "optimization_actions": [
    {
      "action_id": "ACT-01",
      "action_name": "夜间引流调价",
      "action_type": "增效",
      "mechanism": "通过夜间优惠吸引网约车司机错峰补能，提升谷段充电量。",
      "expected_revenue_delta": 7.5,
      "expected_cost_delta": 1.8,
      "expected_profit_delta": 5.7,
      "expected_utilization_delta": 0.04,
      "expected_kwh_delta": 146000,
      "priority": 1,
      "difficulty": "中",
      "preconditions": ["支持分时调价"],
      "risk_note": "优惠力度过大可能压缩单度毛利。"
    },
    {
      "action_id": "ACT-02",
      "action_name": "网约车会员包",
      "action_type": "增效",
      "mechanism": "通过月卡和专属优惠提升复购率和日均到站频次。",
      "expected_revenue_delta": 4.8,
      "expected_cost_delta": 0.6,
      "expected_profit_delta": 4.2,
      "expected_utilization_delta": 0.03,
      "expected_kwh_delta": 90000,
      "priority": 2,
      "difficulty": "中",
      "preconditions": ["主要客户为网约车司机"],
      "risk_note": "需要配套会员运营能力。"
    },
    {
      "action_id": "ACT-03",
      "action_name": "运维排班优化",
      "action_type": "降本",
      "mechanism": "按时段负荷调整值守安排，降低闲时人工投入。",
      "expected_revenue_delta": 0.0,
      "expected_cost_delta": -2.4,
      "expected_profit_delta": 2.4,
      "expected_utilization_delta": 0.0,
      "expected_kwh_delta": 0,
      "priority": 3,
      "difficulty": "低",
      "preconditions": ["当前排班存在冗余空间"],
      "risk_note": "过度压缩排班可能影响服务体验。"
    }
  ],
  "optimized_metrics": {
    "optimized_annual_revenue": 172.2,
    "optimized_annual_total_cost": 164.6,
    "optimized_annual_profit": 7.6,
    "profit_improvement": 16.7,
    "target_utilization_rate": 0.26,
    "optimized_peak_ratio": 0.31,
    "optimized_flat_ratio": 0.34,
    "optimized_valley_ratio": 0.35,
    "break_even_status": "达到盈亏平衡并具备小幅盈利空间"
  },
  "meta": {
    "engine_version": "demo-rule-v1",
    "scenario_template": "模板 D",
    "confidence_level": "demo",
    "assumptions": [
      "支持分时调价",
      "维持当前租金水平不变",
      "不新增设备投资"
    ],
    "warnings": [
      "未提供真实服务费单价，已采用默认值估算",
      "当前结果用于演示，不代表正式财务预测"
    ]
  }
}
```

---

## 13. 界面建议

首版界面建议分为四块：

1. 输入区
   - 自然语言输入框
   - 示例话术快捷填充
2. 参数确认区
   - 提取字段表单
   - 缺失值补充
3. 诊断结果区
   - 当前经营面板
   - 问题标签
   - 优化动作卡片
   - 优化后结果卡片
4. 报告区
   - 结构化诊断报告
   - 支持复制

---

## 14. 技术选型

| 模块 | 选型 | 理由 |
|------|------|------|
| 桌面应用框架 | PySide6 | 适合快速构建 Windows 演示应用 |
| 打包工具 | PyInstaller | 可输出单 EXE 文件 |
| 参数提取 | 规则提取优先，预留 LLM 接口 | 降低演示环境依赖 |
| 诊断引擎 | Python 本地规则引擎 | 便于快速实现和替换 |
| 报告生成 | 模板优先，预留 LLM 接口 | 确保离线可演示 |

---

## 15. 验收标准

### 15.1 功能验收

- 可以输入示例场站描述并成功完成字段提取
- 提取结果可在界面上修改
- 点击诊断后可得到结构化伪算法结果
- 可展示当前经营数据、问题诊断、优化动作和优化后结果
- 可生成一份完整报告

### 15.2 演示验收

- 输出口径自洽，无明显经营逻辑冲突
- 报告中的每个核心结论都能回溯到结构化数据
- 若字段缺失，系统能给出默认值或提示
- 在无网络情况下也能完成基础演示

---

## 16. 后续替换路径

当真实算法逐步完善后，可按以下顺序替换：

1. 用真实参数提取替换规则提取
2. 用真实收益预测模型替换当前经营测算模块
3. 用真实优化模型替换优化动作贡献测算
4. 保留报告生成层作为统一输出封装

本版字段表尽量按“可替换接口”设计，后续可在不重构前端的情况下替换中间引擎。

---

## 17. 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-04-14 | v0.2 | 明确 demo 定位，补齐伪算法层输入输出字段表，重写可落地方案 |
| 2026-04-14 | v0.1 | 初始需求对齐，确定 MVP 范围与演示闭环 |
