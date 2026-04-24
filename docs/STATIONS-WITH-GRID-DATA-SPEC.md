# stations_with_grid.jsonl 数据规格说明

> **文件路径**: `temp_output/stations_with_grid.jsonl`  
> **格式**: JSON Lines（每行一个独立 JSON 对象）  
> **总记录数**: 10,942 条  
> **文件大小**: ~981 MB  
> **生成时间**: 2026-04-24  
> **生成脚本**: `merge_grid_to_station.py`（读取 `grid_profiles.jsonl` + `stations.jsonl` 合并）

---

## 一、数据概览

每行记录代表一个充电场站，包含三类数据：

| 数据层级 | 说明 | 覆盖率 |
|---------|------|--------|
| **场站基础信息** | 运营商、位置、功率配置、土地属性等 | 100% |
| **网格车辆画像** | 该场站所在网格的周边车辆行为数据 | 93.2% (10,197 / 10,942) |
| **五维分型画像** | 按 5 个维度拆分的车流/充电/行为画像 | 93.2% (含于网格画像中) |

> 约 6.8% (745) 的场站因 `grid_code` 未在网格画像中匹配到而未包含网格数据。

---

## 二、字段总览

### 2.1 场站基础信息字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `station_id` | `str` | 场站唯一标识 |
| `station_name` | `str` | 场站名称 |
| `operator_id` | `str` | 运营商 ID |
| `station_lng` | `float` | 经度 |
| `station_lat` | `float` | 纬度 |
| `total_installed_power` | `float` | 总装机功率 (kW) |
| `total_power` | `float` | 总功率（另一种统计口径） |
| `land_property` | `float` | 土地属性编码 |
| `land_property_desc` | `str` | 土地属性描述 |
| `is_public` | `float` | 是否公共场站 (1=是, 0=否) |
| `station_status` | `float` | 场站状态编码 |
| `station_status_desc` | `str` | 场站状态描述 |
| `service_car_types` | `str` | 服务车型编码串 |
| `service_car_types_desc` | `list[str]` | 服务车型描述列表 |
| `business_type` | `list` | 业务类型（当前为空列表） |

### 2.2 场站功率配置字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `le_30kw_count` | `int` | ≤30kW 充电桩数量 |
| `gt_30_le_120kw_count` | `int` | 30~120kW 充电桩数量 |
| `gt_120_le_360kw_count` | `int` | 120~360kW 充电桩数量 |
| `gt_360kw_count` | `int` | ≥360kW 充电桩数量 |
| `power_lt_30kw` | `float` | <30kW 功率值 |
| `power_30_120kw` | `float` | 30~120kW 功率值 |
| `power_120_360kw` | `float` | 120~360kW 功率值 |
| `power_gte_360kw` | `float` | ≥360kW 功率值 |

### 2.3 场站业务信息字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `busine_hours` | `str` | 营业时间描述 |
| `charger_type` | `null` | 充电桩类型（当前全为 null） |
| `electricity_fee_parsed` | `dict` | 电费结构 `{periods, avg_price, min_price, max_price}` |
| `service_fee_parsed` | `dict` | 服务费结构 `{periods, avg_price, min_price, max_price}` |

### 2.4 网格关联字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `grid_code` | `str` | 网格编码（如 `L2GM05-GXD003`） |
| `region` | `str` | 所属行政区 |
| `avg_daily_energy_kwh` | `float` | 网格日均充电量 (kWh) |
| `avg_utilization` | `float` | 网格平均利用率 |
| `peak_hour` | `str` | 高峰时段 |
| `valley_hour` | `str` | 低谷时段 |

### 2.5 时间序列统计字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `season_stats` | `dict` | 四季统计 `{spring_festival, summer, national_day, winter}` |
| `has_timeseries_data` | `bool` | 是否有时间序列数据 |
| `metrics_estimated` | `bool` | 指标是否为估算值 |

---

## 三、网格车辆画像（`grid_vehicle_profile`）

当场站匹配到网格时，该字段为 `dict`，包含以下子字段：

### 3.1 流量与活跃度

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `grid_code` | `str` | 网格编码 | `L2GM05-GXD003` |
| `avg_daily_car_trips` | `float` | 网格日均车辆通行车次 | `25719.72` |
| `peak_hour_car_trips` | `float` | 高峰时段（17-20点）车次 | `5724.0` |

### 3.2 充电行为总览

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `avg_daily_energy_kwh` | `float` | 网格日均总充电量 (kWh) | `11194.76` |
| `avg_soc` | `float` | 平均起始 SOC (%) | `64.7` |
| `avg_daily_charge_times` | `float` | 网格日均充电次数 | — |
| `avg_parking_minutes` | `float` | 平均停车时长 (分钟) | `32.5` |
| `avg_charging_minutes` | `float` | 平均充电时长 (分钟) | `8.2` |
| `avg_charging_power_kw` | `float` | 平均充电功率 (kW) | `45.3` |

### 3.3 车辆类型构成

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `vehicle_type_mix` | `dict[str, float]` | 各用途车型占比（车次比例），共 15 类 |
| `power_level_mix` | `dict[str, float]` | 各功率等级占比，共 4 档：`<30kW`, `30-120kW`, `120-360kW`, `≥360kW` |

**vehicle_type_mix 包含的 15 种用途：**
```
公交车、公务车、公路车、出租车、工程车、旅游车、
物流轻卡、物流重卡、环卫车、私家车(混动)、私家车(纯电)、
租赁车、营运车、通勤车、邮政车
```

### 3.4 车辆活动半径

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `avg_run_radius_m` | `float` | 平均行驶半径（米） | `11520.08` |

> **数据来源**：step07（活动半径）为标签级全局数据，按各标签在网格内的车流量占比加权计算得到网格级平均值。

### 3.5 迁移态势

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `migration` | `dict` | 净流入/流出统计 | `{outflow_count, inflow_count, net_migration}` |
| `primary_inflow_from` | `list[str]` | 主要流入来源（Top-3 网格编码） | `["L2GM05-GXD002", ...]` |
| `primary_outflow_to` | `list[str]` | 主要流出去向（Top-3 网格编码） | `["L2GM05-GXD004", ...]` |

> **数据来源**：step08 原始数据粒度为 `用途_功率`（D4），不含品牌维度。D5（最细标签）的迁移数据按 D4 平铺（同一用途_功率下的所有品牌共享相同迁移数据）。

### 3.6 最细标签全局画像

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `vehicle_tag_global_profile` | `dict[str, dict]` | 93 个最细标签（如 `Chuzu_P1`, `Sijiacd_Band3_P2`）的全局画像 |

每个标签包含：`avg_run_radius_m`, `avg_daily_mileage_km`, `avg_battery_capacity_kwh`, `avg_charging_power_kw`, `sample_count`

> **用途**：为 RAG 检索提供相似场站的标签级对比数据。

---

## 四、五维分型画像（`dimensional_profiles`）

`dimensional_profiles` 是 `grid_vehicle_profile` 的子字段，包含 5 个维度的拆分画像。每个维度下，按该维度的分型聚合网格内车辆的行为指标。

### 4.1 维度定义

| 维度键 | 名称 | 分型粒度 | 分型数量 | 原始数据来源 |
|--------|------|---------|:-------:|-------------|
| `by_purpose` | 只分用途 | `用途` | 15 | step01~12 |
| `by_power` | 只分功率 | `功率等级` | 4 | step01~12 |
| `by_purpose_power` | 用途_功率 | `用途_功率` | 45 | step01~12（表08原生粒度） |
| `by_purpose_band` | 用途_品牌 | `用途_品牌` | 15 | step01~12 |
| `by_full_tag` | 最细标签 | 完整 `veh_tag` | 93 | step01~12 |

### 4.2 每个分型包含的指标

```json
{
  "trip_ratio": 0.0713,           // 该分型在网格内的车次占比
  "daily_energy_kwh": 320.5,      // 该分型日均充电量 (kWh)
  "avg_soc": 49.0,                // 该分型平均起始 SOC (%)
  "daily_charge_times": 12.8,     // 该分型日均充电次数
  "avg_parking_minutes": 26.6,    // 该分型平均停车时长 (分钟)
  "avg_charging_minutes": 1.0,    // 该分型平均充电时长 (分钟)
  "avg_run_radius_m": 8200,       // 该分型平均活动半径 (米)
  "avg_charging_power_kw": 15.3   // 该分型平均充电功率 (kW)
}
```

> **注**：部分分型因样本量不足可能缺少某些指标（如 `daily_energy_kwh` 或 `daily_charge_times` 为 `null`）。使用时建议检查字段是否存在。

### 4.3 数据计算方式

各维度的指标计算逻辑如下：

| 指标 | 计算方式 |
|------|---------|
| `trip_ratio` | 该维度分型在网格内的车次 / 网格总车次（来自 step01 `tag_ratio` 按维度聚合） |
| `daily_energy_kwh` | step02 维度拆分数据直接读取 |
| `avg_soc` | step03 维度拆分数据直接读取 |
| `daily_charge_times` | step05 维度拆分数据直接读取 |
| `avg_parking_minutes` / `avg_charging_minutes` | step11 维度拆分数据直接读取 |
| `avg_run_radius_m` | step07 标签级全局数据 × step01 `tag_ratio` 加权平均 |
| `avg_charging_power_kw` | step12 标签级功率分布 × step01 `tag_ratio` 加权平均 |

### 4.4 抽样示例

**by_purpose_power（用途_功率）— 最精细的迁移数据粒度：**

```json
{
  "出租车_P1": {
    "trip_ratio": 0.0713,
    "daily_energy_kwh": 320.5,
    "avg_soc": 49.0,
    "daily_charge_times": 12.8,
    "avg_parking_minutes": 26.6,
    "avg_charging_minutes": 1.0,
    "avg_run_radius_m": 8200,
    "avg_charging_power_kw": 15.3
  },
  "私家车(纯电)_P2": {
    "trip_ratio": 0.213,
    "daily_energy_kwh": 580.2,
    "avg_soc": 65.0,
    "daily_charge_times": 8.5,
    "avg_parking_minutes": 38.0,
    "avg_charging_minutes": 7.0,
    "avg_run_radius_m": 11400,
    "avg_charging_power_kw": 42.6
  }
}
```

**by_full_tag（最细标签）— 标签级画像（含里程/电池容量）：**

```json
{
  "Gongwu_P2": {
    "trip_ratio": 0.0675,
    "daily_energy_kwh": 1446.16,
    "avg_soc": 64.43,
    "daily_charge_times": 53.85,
    "avg_parking_minutes": 29.32,
    "avg_charging_minutes": 24.21,
    "avg_run_radius_m": 13022.52,
    "avg_charging_power_kw": 48.78
  }
}
```

---

## 五、RAG 上下文文本（`grid_context_text`）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `grid_context_text` | `str` | 网格画像的自然语言摘要，用于 Embedding 检索 |

**文本长度**：平均 380 字符，最大 393，最小 347。

**示例**：
```
该场站位于网格 L2GM05-GXD003。网格周边日均车辆通行约 25720 车次，
高峰时段（17-20点）约 5724 车次。周边车辆类型以 私家车(纯电)(35.3%)、
私家车(混动)(25.8%)、公务车(14.2%) 为主。功率等级以 120-360kW(45.2%)、
30-120kW(30.1%) 为主。平均起始 SOC 为 64.7%，平均停车时长 32.5 分钟，
平均充电时长 8.2 分钟。充电净流出 89 车次/日，主要流向 L2GM05-GXD005。
```

---

## 六、数据缺失与注意事项

### 6.1 网格匹配缺失

- **未匹配场站**: 745 个 (6.8%)
- **主要原因**: 场站 `grid_code` 不在 1337 个网格画像的覆盖范围内
- **区域分布**: "未知" 585 个，南山区 39 个，前海 37 个，宝安区 29 个...

### 6.2 维度内样本稀疏

- `by_full_tag` 的 93 个分型中，部分分型在单个网格内的 `trip_ratio` 极低（<0.001），指标可能受噪声影响
- 建议设置 `trip_ratio` 阈值（如 ≥0.01）过滤低置信度分型

### 6.3 品牌维度（D3）数据局限

- `by_purpose_band` 中品牌仅存在于 `Yunying`/`Sijiacd`/`Sijiahd` 等标签
- 其他用途（如 `公交车`、`环卫车`）无品牌维度，其 `by_purpose_band` 分型等同于 `by_purpose`

### 6.4 迁移数据粒度

- step08 原始数据为 `用途_功率`（D4）粒度，不含品牌
- D5（最细标签）的迁移指标按 D4 平铺，**不区分品牌**
- 如需品牌级迁移分析，需额外假设或数据补充

### 6.5 活动半径数据来源

- step07 为标签级全局平均值，非网格特异性数据
- 网格级 `avg_run_radius_m` 通过 `tag_ratio` 加权计算，反映该网格内活跃标签的半径特征
- 某些网格可能缺乏特定标签的数据，导致该维度下该分型无 `avg_run_radius_m`

---

## 七、使用建议

### 7.1 RAG 检索场景

```python
# 1. 用 grid_context_text 做 Embedding 相似度检索
doc = station["grid_context_text"]

# 2. 检索结果附带轻量 metadata（区域、利用率、主导车型等）
metadata = {
    "region": station["region"],
    "avg_utilization": station["avg_utilization"],
    "grid_code": station["grid_code"],
}

# 3. 详细五维画像从 stations_with_grid.jsonl 按需加载
profile = station["grid_vehicle_profile"]["dimensional_profiles"]
```

### 7.2 诊断分析场景

```python
# 功率配置错配检测：对比场站功率供给 vs 周边 by_power 需求
gt_360_count = station["gt_360kw_count"]
power_demand = station["grid_vehicle_profile"]["dimensional_profiles"]["by_power"]

# 充电焦虑分析：按 by_purpose_power 中的 SOC + 日均里程计算
for user_type, data in station["grid_vehicle_profile"]["dimensional_profiles"]["by_purpose_power"].items():
    soc = data.get("avg_soc", 50)
    # ... 计算焦虑指数

# 建站建议：取 by_full_tag Top-3 的活动半径和主要流出去向
top_users = sorted(
    station["grid_vehicle_profile"]["dimensional_profiles"]["by_full_tag"].items(),
    key=lambda x: x[1].get("trip_ratio", 0),
    reverse=True
)[:3]
```

### 7.3 数据加载性能

- 文件大小 ~981 MB，10,942 条记录
- **建议**：按 `station_id` 建立内存索引（`dict`），避免逐行扫描
- 或按 `grid_code` 预聚类，批量加载同网格场站

---

## 八、版本历史

| 版本 | 时间 | 变更 |
|------|------|------|
| v1.0 | 2026-04-24 | 初始版本，含五维分型画像（D1~D5） |

---

*文档维护：当 `merge_all_to_grid.py` 或 `merge_grid_to_station.py` 的输出结构变更时，需同步更新本文档。*
