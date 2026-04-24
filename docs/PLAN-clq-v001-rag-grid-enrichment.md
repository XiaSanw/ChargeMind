# ChargeMind — RAG 网格画像全量数据增强计划

> **计划编号**: clq-v001  
> **计划名称**: RAG 网格画像全量数据增强（含五维车辆分型）  
> **制定人**: clq  
> **制定时间**: 2026-04-24  
> **前置调研**: [DATA-PIPELINE-OVERVIEW.md](./DATA-PIPELINE-OVERVIEW.md)  
> **关联文档**: [GRID-PROFILE-SPEC.md](./GRID-PROFILE-SPEC.md)  
> **状态**: 🚧 实施中（代码已修改，待运行验证）

---

## 一、核心诉求

当前 `grid_profiles.jsonl` 和 `stations_with_grid.jsonl` 中的网格车辆画像只做了一级聚合（网格级总平均），存在两个问题：

1. **字段消费不足**：现有画像字段已存入 ChromaDB，但诊断接口的 LLM Prompt 完全没有消费这些丰富数据
2. **分型粒度太粗**：不同用户分型（出租车 vs 私家车、30kW vs 360kW）的行为差异巨大，混在一起会抹平关键特征

本计划要同时解决这两个问题：
- **让 RAG "吃透"全量数据**：从 Embedding 文档到 LLM Prompt 全链路消费网格画像
- **车辆分型五维化**：按 5 个维度独立画像，输出"30kW 用户有多少充电量、是否活跃、迁入还是迁出"
- **活动半径驱动建站建议**：通过主导用户的活动半径/日均里程，推导卫星站选址距离

---

## 二、数据资产全量盘点

### 2.1 重要发现：五维数据在 step01~12 中已生成

**调研结论**：`step01~12` 的中间结果中已经包含了 **D1/D2/D4/D5 四个维度的拆分数据**，但 `merge_all_to_grid.py` **只取了网格级总平均**。

| 维度 | step 结果中的字段 | 是否在 grid_profiles 中 |
|------|------------------|:----------------------:|
| D1 只分功率 | `power_mix`, `energy_by_power_level`, `soc_by_power_level`, ... | ❌ |
| D2 只分用途 | `purpose_mix`, `energy_by_vehicle_type`, `soc_by_vehicle_type`, ... | ❌（仅用途占比）|
| D4 用途_功率 | `purpose_power_mix`, `energy_by_purpose_power`, ... | ❌ |
| D5 最细标签 | `full_tag_mix`, `energy_by_full_tag`, `radius_by_full_tag`, ... | ❌ |

**这意味着**：`merge_all_to_grid.py` 只需读取 step 结果中的维度拆分数据并合并，**不需要重新跑原始 CSV 聚合**。

### 2.2 各维度可计算指标矩阵

| 指标 | D1 功率 | D2 用途 | D3 品牌 | D4 用途_功率 | D5 最细标签 |
|------|:------:|:------:|:------:|:-----------:|:----------:|
| 流量活跃度（车次） | ✅ 聚合 | ✅ 聚合 | ✅ 聚合 | ✅ 直接 | ✅ 直接 |
| 充电需求（电量/次数） | ✅ 聚合 | ✅ 聚合 | ✅ 聚合 | ✅ 直接 | ✅ 直接 |
| 充电行为（SOC/时长） | ✅ 聚合 | ✅ 聚合 | ✅ 聚合 | ✅ 直接 | ✅ 直接 |
| 车辆活动（里程/半径） | ❌ | ❌ | ❌ | ❌ | ✅ 直接 |
| 车辆结构（电池/车辆数） | ❌ | ⚠️ | ⚠️ | ⚠️ | ✅ 直接 |
| 迁移态势（距离/时长/能耗） | ❌ | ❌ | ❌ | ✅ 直接 | ⚠️ 间接* |

> *D5 最细标签的迁移数据：表08无品牌维度，但可通过 D4 数据按品牌加权估算。

### 2.3 五维分型定义

`veh_tag` 原始格式：`用途[_品牌]_功率`

| 维度 | 名称 | 解析规则 | 示例 |
|------|------|---------|------|
| D1 | **只分功率** | 提取 `P1/P2/P3/P4` | `P1`（<30kW） |
| D2 | **只分用途** | 提取用途前缀 | `出租车`、`私家车(纯电)` |
| D3 | **只分品牌** | 提取 `Band1~5` / `OtherBand` / `None` | `Band3` |
| D4 | **用途_功率** | 用途 + 功率（表08原生粒度） | `出租车_P1`、`营运车_P2` |
| D5 | **最细标签** | 完整 `veh_tag` | `出租车_P1`、`营运车_Band3_P2` |

> **D3 数据来源**：step01~12 中没有独立的 "只分品牌" 维度，但可从 `purpose_band_mix` 或 `full_tag_mix` 中解析提取。

---

## 三、实施步骤（更新版）

### Phase A: 数据工程（修改现有脚本）

**Step A1: 修改 `merge_all_to_grid.py`** ✅ 已完成
- 扩展 `load_step01~12()` 函数，读取所有维度拆分数据
- 新增 `weighted_dim_values()` 辅助函数：将标签级指标（活动半径、功率）按维度加权到网格
- 新增 `build_dim_maps()` 辅助函数：预构建标签到各维度的映射
- 修改 `main()`：为每个网格构建 `dimensional_profiles` 字段

**Step A2: 修改 `merge_grid_to_station.py`** ✅ 已完成
- 在嵌套 `grid_vehicle_profile` 中传递 `dimensional_profiles`

**Step A3: 新增 `compute_derived_metrics.py`**（待实施）
- 读取新的 `grid_profiles.jsonl`
- 为每个网格的每个维度分型计算衍生指标：
  - `parking_charge_ratio` — 占位比（停车时长 / 充电时长）
  - `soc_urgency_index` — 充电紧迫度（按用户类型分层阈值）
  - `power_mismatch_score` — 功率配置错配分数（含供给规模惩罚）
  - `stationing_recommendation` — 卫星站选址建议（启发式规则）
- 输出更新后的 `grid_profiles.jsonl`

**Step A4: 重新运行流水线**
```bash
python merge_all_to_grid.py      # 生成含 dimensional_profiles 的 grid_profiles.jsonl
python merge_grid_to_station.py  # 生成含 dimensional_profiles 的 stations_with_grid.jsonl
```

### Phase B: RAG 索引增强

**Step B1: 更新 `indexer.py`**
- 重写 `build_station_doc()`：在 Embedding 文档中注入五维画像摘要
- 扩展 `_build_metadata()`：新增 `station_dominant_user_type`、`station_power_mismatch_score` 等字段

**Step B2: 更新 `retriever.py`**
- 查询文本注入网格画像关键词（车流量、主导车型、迁移态势）
- 保持向后兼容

### Phase C: 诊断接口增强

**Step C1: 更新 `diagnosis.py`**
- 重写 `_rag_analyze()` Prompt：相似场站由 **3 个减到 2 个**详细分析（控制 Prompt 长度）
- 每个相似场站提供 20+ 个指标（而非现在的 2 个）
- 新增 `_format_grid_profile()` 辅助函数

**Step C2: 重写 `build_report()`**
- 新增 `grid_ecology` 板块
- 新增 `power_mismatch_diagnosis` 板块
- 新增 `stationing_recommendation` 板块（标注为**启发式规则，需业务校验**）
- 新增 `user_behavior_insights` 板块

**Step C3: 重写 `_mock_rag_analysis()`**
- 构造 1-2 个典型场站的五维画像作为 fallback
- 保持降级后的报告不缺失新增板块

---

## 四、关键算法设计（含评审修正）

### 4.1 功率配置错配检测（含供给规模惩罚）

```python
def compute_power_mismatch(station_power_counts, grid_power_demand, total_piles):
    """
    错配分数 = TVD（总变差距离）+ 供给规模惩罚
    
    供给规模惩罚逻辑：
    - 桩数 < 10：错配影响被放大（小场站容错低）
    - 桩数 10-50：标准计算
    - 桩数 > 50：错配影响被缩小（大场站可调配空间大）
    """
    total = sum(station_power_counts.values())
    station_supply_ratio = {k: v/total for k, v in station_power_counts.items()}
    
    # 基础错配分数（TVD）
    tvd = sum(abs(station_supply_ratio.get(k, 0) - v)
              for k, v in grid_power_demand.items()) / 2
    
    # 供给规模惩罚因子
    if total_piles < 10:
        scale_penalty = 1.2  # 小场站错配影响放大
    elif total_piles > 50:
        scale_penalty = 0.85  # 大场站错配影响缩小
    else:
        scale_penalty = 1.0
    
    mismatch_score = min(tvd * scale_penalty, 1.0)
    
    return {
        "mismatch_score": round(mismatch_score, 2),
        "tvd": round(tvd, 2),
        "scale_penalty": scale_penalty,
        "interpretation": (
            "严重错配" if mismatch_score > 0.7 else
            "中度错配" if mismatch_score > 0.4 else
            "轻度错配" if mismatch_score > 0.15 else
            "基本匹配"
        )
    }
```

### 4.2 活动半径 → 卫星站选址建议（启发式规则）

> **标注**：本算法为初版启发式规则，需结合业务场景校验。

```python
def recommend_satellite_stationing(grid_profile, top_n_users=3):
    """
    基于主导用户的活动半径和迁移流向，生成卫星站选址建议。
    
    核心假设：
    - 卫星站应建在用户日常活动圈的"边缘延伸区"
    - 优先沿主要流出去向布局
    - 充电行为通常发生在通勤路径或居住地 3-5km 内，而非活动圈几何边缘
    """
    sorted_users = sorted(
        grid_profile['by_full_tag'].items(),
        key=lambda x: x[1].get('daily_energy_kwh', 0),
        reverse=True
    )[:top_n_users]
    
    recommendations = []
    for user_type, profile in sorted_users:
        radius = profile.get('avg_run_radius_m', 0)
        mileage = profile.get('avg_daily_mileage_km', 0)
        
        # 距离系数：基于活动半径，但向下修正（用户不会跑到活动圈边缘充电）
        # 修正系数 0.5~0.8：反映"充电便利半径"通常小于活动半径
        correction = 0.6
        min_dist = int(radius * correction * 0.7)
        max_dist = int(radius * correction * 1.2)
        
        # 里程参考：日均里程的 30% 作为单次充电可接受距离
        mileage_ref = int(mileage * 1000 * 0.3) if mileage else 0
        
        # 取两者较小值作为建议范围
        if mileage_ref > 0:
            max_dist = min(max_dist, mileage_ref)
        
        primary_outflow = profile.get('primary_outflow_to', [])
        
        recommendations.append({
            "target_user": user_type,
            "activity_radius_m": radius,
            "daily_mileage_km": mileage,
            "satellite_distance_range_m": (min_dist, max_dist),
            "priority_directions": primary_outflow[:3],
            "rationale": (
                f"该用户群体平均活动半径{radius/1000:.1f}km，日均行驶{mileage:.0f}km。"
                f"考虑充电便利半径修正系数{correction}，"
                f"建议在{min_dist//1000}-{max_dist//1000}km范围内、"
                f"沿主要流出去向布局卫星站。"
            ),
            "heuristic_note": "距离系数为初版假设，需结合实际充电行为数据校准"
        })
    
    return recommendations
```

### 4.3 充电焦虑指数（按用户类型分层阈值）

> **标注**：本算法为初版 heuristic，阈值未经用户调研校准，后续可基于 A/B 测试调整。

```python
def compute_charging_anxiety_index(user_profile, user_type: str):
    """
    按用户类型分层阈值：
    - 出租车/网约车/物流车：营运车辆，日均里程高，对补电频率敏感
    - 私家车：通勤为主，里程中等，对价格敏感度高于速度
    - 公务车/公交车：固定路线，充电可计划，焦虑低
    """
    soc = user_profile.get('avg_soc', 50)
    mileage = user_profile.get('avg_daily_mileage_km', 50)
    
    # 用户类型分层参数
    TYPE_CONFIG = {
        "出租车": {"mileage_threshold": 100, "weight_soc": 0.4, "weight_mileage": 0.6},
        "网约车": {"mileage_threshold": 100, "weight_soc": 0.4, "weight_mileage": 0.6},
        "物流轻卡": {"mileage_threshold": 80, "weight_soc": 0.4, "weight_mileage": 0.6},
        "物流重卡": {"mileage_threshold": 80, "weight_soc": 0.4, "weight_mileage": 0.6},
        "私家车(纯电)": {"mileage_threshold": 60, "weight_soc": 0.6, "weight_mileage": 0.4},
        "私家车(混动)": {"mileage_threshold": 80, "weight_soc": 0.5, "weight_mileage": 0.5},
        "公务车": {"mileage_threshold": 50, "weight_soc": 0.7, "weight_mileage": 0.3},
        "公交车": {"mileage_threshold": 120, "weight_soc": 0.3, "weight_mileage": 0.7},
    }
    
    # 提取用途（去掉功率后缀）
    base_type = user_type.split("_")[0] if "_" in user_type else user_type
    config = TYPE_CONFIG.get(base_type, {"mileage_threshold": 60, "weight_soc": 0.5, "weight_mileage": 0.5})
    
    soc_anxiety = (100 - soc) / 100
    mileage_anxiety = min(mileage / config["mileage_threshold"], 1.0)
    
    anxiety_index = (
        config["weight_soc"] * soc_anxiety +
        config["weight_mileage"] * mileage_anxiety
    )
    
    return {
        "anxiety_index": round(anxiety_index, 2),
        "level": "高焦虑" if anxiety_index > 0.6 else "中焦虑" if anxiety_index > 0.4 else "低焦虑",
        "implication": (
            "用户对充电速度和便利性敏感，愿意为快充支付溢价"
            if anxiety_index > 0.6 else
            "用户对价格敏感度高于速度，适合谷段促销引流"
        ),
        "heuristic_note": f"基于{base_type}分层阈值（里程阈值{config['mileage_threshold']}km），未经用户调研校准"
    }
```

### 4.4 占位问题诊断（按用户类型差异化阈值）

> **标注**：物流车、营运车装卸货/等单，停车时长天然长于充电时长。统一阈值会误报。

```python
# 各用户类型的典型停车/充电行为参考值（用于阈值设定）
TYPICAL_BEHAVIOR = {
    "出租车": {"typical_parking_charge_ratio": 3.0, "reason": "等客、排队"},
    "网约车": {"typical_parking_charge_ratio": 3.5, "reason": "等单、休息"},
    "物流轻卡": {"typical_parking_charge_ratio": 4.0, "reason": "装卸货"},
    "物流重卡": {"typical_parking_charge_ratio": 5.0, "reason": "装卸货、等待"},
    "私家车(纯电)": {"typical_parking_charge_ratio": 2.5, "reason": "购物、办事"},
    "私家车(混动)": {"typical_parking_charge_ratio": 2.0, "reason": "顺便充电"},
    "公务车": {"typical_parking_charge_ratio": 2.0, "reason": "公务等待"},
    "公交车": {"typical_parking_charge_ratio": 1.5, "reason": "调度等待"},
}


def diagnose_parking_occupation(user_profile, user_type: str):
    parking = user_profile.get('avg_parking_minutes', 0)
    charging = user_profile.get('avg_charging_minutes', 0)
    
    if charging <= 0:
        return {"has_occupation_problem": False}
    
    ratio = parking / charging
    
    # 获取该用户类型的典型比值
    base_type = user_type.split("_")[0] if "_" in user_type else user_type
    typical = TYPICAL_BEHAVIOR.get(base_type, {"typical_parking_charge_ratio": 2.5})
    typical_ratio = typical["typical_parking_charge_ratio"]
    
    # 判定：实际比值是否显著超过典型比值
    excess_ratio = ratio / typical_ratio if typical_ratio > 0 else ratio
    
    return {
        "avg_parking_min": parking,
        "avg_charging_min": charging,
        "parking_charge_ratio": round(ratio, 1),
        "typical_ratio_for_type": typical_ratio,
        "excess_ratio": round(excess_ratio, 1),
        "has_occupation_problem": excess_ratio > 1.5,
        "severity": "严重" if excess_ratio > 2.5 else "中等" if excess_ratio > 1.5 else "轻微",
        "recommendation": (
            f"该用户类型({base_type})典型停车/充电比为{typical_ratio}，"
            f"当前实际为{ratio:.1f}（超标{excess_ratio:.1f}倍）。"
            + ("建议设置充满后超时占位费。" if excess_ratio > 1.5 else "占位情况在合理范围内。")
        ),
        "typical_behavior_note": typical["reason"]
    }
```

---

## 五、DEMO 阶段 MVP 范围

评审建议优先 **D4 + D5**，D1~D3 可后移。结合代码实现现状，MVP 范围如下：

| 优先级 | 维度 | 是否纳入 MVP | 理由 |
|--------|------|:----------:|------|
| P0 | **D4 用途_功率** | ✅ | 表08迁移数据原生粒度，数据最完整；step 结果已就绪 |
| P0 | **D5 最细标签** | ✅ | 标签级全局画像（里程/半径/电池/功率）可直接挂接；step 结果已就绪 |
| P1 | **D2 只分用途** | ⚠️ 可选 | step 结果已就绪，但可用 D4 二次聚合得到；后续迭代 |
| P1 | **D1 只分功率** | ⚠️ 可选 | 同理，可用 D4 二次聚合；后续迭代 |
| P2 | **D3 只分品牌** | ❌ 后移 | 原始数据无独立品牌维度，需从 full_tag 解析；品牌对运营策略影响较小 |

**MVP 输出结构**：

```json
{
  "dimensional_profiles": {
    "by_purpose_power": {
      "出租车_P1": {
        "trip_ratio": 0.0713,
        "daily_energy_kwh": 320.5,
        "avg_soc": 49.0,
        "daily_charge_times": 12.8,
        "avg_parking_minutes": 26.6,
        "avg_charging_minutes": 1.0,
        "avg_run_radius_m": 8200,
        "avg_charging_power_kw": 15.3
      }
    },
    "by_full_tag": {
      "Chuzu_P1": {
        "trip_ratio": 0.0018,
        "daily_energy_kwh": 2.1,
        "avg_soc": 49.0,
        "daily_charge_times": 0.8,
        "avg_parking_minutes": 26.6,
        "avg_charging_minutes": 1.0,
        "avg_run_radius_m": 8200,
        "avg_charging_power_kw": 15.3
      }
    }
  }
}
```

---

## 六、关键设计决策（ADR）

### ADR-001: 为什么修改 merge_all_to_grid.py 而不是新增 step13~15？

- **上下文**: 原计划写 step13~15 做五维聚合，但调研发现 step01~12 已经输出了五维拆分数据
- **决策**: 直接修改 `merge_all_to_grid.py`，读取 step 结果中的维度拆分数据并合并
- **理由**: 避免重复计算；减少脚本数量；降低维护成本
- **代价**: `merge_all_to_grid.py` 代码复杂度增加（已从 220 行增至 ~400 行）

### ADR-002: 标签级指标如何加权到网格？

- **上下文**: step07（活动半径）和 step12（功率分布）是标签级全局数据，不区分网格
- **决策**: 用 step01 的 `tag_ratio`（各 tag 在网格内的车次占比）作为权重，加权计算网格级维度值
- **理由**: 车流量占比反映该 tag 在网格内的活跃度，作为权重最合理
- **公式**: `grid_dim_value = Σ(tag_value × tag_ratio) / Σ(tag_ratio)`

### ADR-003: D5 迁移数据的处理

- **上下文**: 表08迁移数据粒度为 `type_power`（D4），不含品牌
- **决策**: D5（最细标签）的迁移指标用 D4 值平铺（同一用途_功率下的所有品牌共享相同迁移数据）
- **理由**: 不编造数据；明确标注数据来源；在报告中注明"按用途_功率估算"

### ADR-004: 建站建议系数为什么标注为启发式？

- **上下文**: 评审指出 `radius * 0.7~1.3` 可能不符合实际充电行为
- **决策**: 引入修正系数 0.6 并标注为"启发式规则，需业务校验"
- **理由**: 活动半径反映的是"地理活动边界"，但充电通常发生在居住地/工作地 3-5km 内，两者不等价

### ADR-005: 错配分数为什么叠加供给规模惩罚？

- **上下文**: 评审指出小场站（<10 桩）的错配影响被低估
- **决策**: 桩数 < 10 时放大错配分数（×1.2），桩数 > 50 时缩小（×0.85）
- **理由**: 小场站供给弹性低，错配影响更直接；大场站可调配空间大，错配可被内部消化

---

## 七、风险与应对（更新版）

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| Embedding 文档过长导致语义稀释 | 中 | 中 | 分层摘要，控制文档长度在 500 字以内 |
| Prompt 过长超出 LLM 上下文限制 | 中 | 高 | **相似场站从 3 个减到 2 个**详细分析；使用表格压缩呈现 |
| 样本稀疏导致画像失真 | 中 | 高 | 设置样本量门槛（≥10）；低于门槛标记为 `insufficient_data` |
| 数据缺失率高（6.8% 场站无 grid_profile） | 低 | 中 | 完整向后兼容，无 grid_profile 时回退到旧逻辑 |
| 索引重建时间 | 低 | 低 | **预留 20-30 分钟**（10,942 条 × 100 batch + 文档变长后的推理时间增加） |
| Mock 降级体验断层 | 中 | 中 | 在 `_mock_rag_analysis` 中构造 1-2 个典型场站五维画像作为 fallback |
| Schema 兼容性 | 低 | 中 | `dimensional_profiles` 为新增可选字段，不影响旧解析逻辑 |
| DEMO 工作量 | 中 | 中 | Phase A 已完成代码修改，仅需运行 + 验证；Phase B/C 控制在 2 天内完成 |

---

## 八、输出示例（诊断报告新增板块）

```markdown
## 一、五维用户分型画像（MVP：D4 用途_功率 + D5 最细标签）

### 按用途_功率分型（D4）
| 分型 | 日均车次占比 | 日均充电量 | 起始SOC | 充电次数 | 活动半径 | 充电功率 |
|------|------------|-----------|--------|---------|---------|---------|
| 出租车_P1 | 7.1% | 320.5 kWh | 49% | 12.8 | 8.2km | 15.3kW |
| 私家车(纯电)_P2 | 21.3% | 580.2 kWh | 65% | 8.5 | 11.4km | 42.6kW |
| 营运车_P2 | 8.9% | 410.0 kWh | 48% | 9.2 | 8.2km | 38.1kW |

### 按最细标签（D5，Top-3）
1. **私家车(纯电)_Band3_P2** — 日均 2,840 车次，充电 1,560 kWh
   - 活动半径：11.4km | 日均里程：46km | 电池容量：40-60kWh
   - 停车 38min / 充电 7min → **占位比 5.4，严重占位**（该类型典型比值为 2.5，超标 2.2 倍）
   - 迁移：净流入 89 车次/日
   - 充电焦虑：**中焦虑**（SOC 65%，日均 46km，私家车阈值 60km）

2. **营运车_Band2_P1** — 日均 1,240 车次，充电 890 kWh
   - 活动半径：8.2km | 日均里程：127km | 电池容量：60-80kWh
   - 起始 SOC 48% → **充电紧迫度高**（高焦虑：营运车阈值 100km，实际 127km）
   - 迁移：净流出 156 车次/日，可能流向竞品场站

## 二、功率配置错配诊断

**场站功率供给**：<30kW×4 (2.4%) | 30-120kW×13 (7.9%) | 120-360kW×34 (20.5%) | ≥360kW×163 (69.3%)  
**总桩数**: 214（大场站，供给规模惩罚 ×0.85）

**周边功率需求**：<30kW 58% | 30-120kW 37% | 120-360kW 4% | ≥360kW 1%

**TVD: 0.72，错配分数: 0.61（中度错配）**

> 场站 90% 的桩功率 ≥120kW，但周边 95% 的车辆功率需求 ≤120kW。由于总桩数 214（大场站），内部调配空间较大，实际错配影响被适度缩小。

## 三、卫星站选址建议（启发式规则）

基于主导用户 **私家车(纯电)_Band3_P2**：
- 平均活动半径：11.4 km
- 日均行驶里程：46 km
- 主要流出去向：L2GM05-GXD005（东向）、L2GM04-GM009（西向）

**建议选址**：在场站 **5~8 km** 范围内，优先沿 **东向** 布局卫星站。

**选址逻辑**：
- 该用户群体平均活动半径 11.4km，但考虑充电便利半径修正系数 0.6，实际有效覆盖范围约 5~8km
- 东向网格 L2GM05-GXD005 是主要流出去向

> ⚠️ 距离系数为初版假设，需结合实际充电行为数据校准。

## 四、用户行为洞察

| 用户类型 | 核心洞察 | 运营建议 |
|---------|---------|---------|
| 私家车(纯电) | 占位严重（5.4倍），充满不走 | 充满后30分钟免费，超时占位费0.5元/分钟 |
| 营运车 | 充电紧迫度高（SOC 48%），日均127km | 设置专用快充通道，推出夜间谷段包月套餐 |
| 私家车(混动) | SOC 72%，多为顺便充电，价格敏感 | 午间11:00-14:00推出"混动车主专属折扣" |
```

---

## 九、下一步行动

1. **立即**：在本地环境运行 `python merge_all_to_grid.py` + `python merge_grid_to_station.py`
2. **今日**：编写 `compute_derived_metrics.py`，计算衍生指标（占位比、错配分数、焦虑指数）
3. **明日**：按 Phase B/C 增强 RAG 索引和诊断接口
4. **验证**：选取 3-5 个典型场站，人工验证五维画像和建站建议的合理性

---

*计划版本: v001-rev2*  
*评审回应: 已回应数据流水线衔接、D5 迁移数据来源、Prompt 长度控制、错配算法精度、选址系数、焦虑阈值、占位诊断、MVP 范围、Mock 降级、索引重建时间等 10 项评审意见*  
*下次评审: 代码运行验证后*
