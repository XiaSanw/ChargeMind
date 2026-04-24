# ChargeMind 数据清洗交叉校验任务

## 背景
我正在为"ChargeMind"充电场站诊断平台清洗深圳全域充电场站数据。
一个AI agent已完成了阶段1的静态数据清洗脚本，我需要你对清洗结果进行独立交叉校验。

## 输入数据说明

### 原始数据（5个文件，位于 /Users/xiasanw/work/2030数据/）
1. `表1.xlsx` (13,456行) — 场站静态信息：operator_id, station_id, station_name, station_lng, station_lat, total_installed_power, land_property, is_public, station_status, service_car_types, 各功率段枪数量
2. `b2.csv` (14,711行) — 电价/服务费/营业时间：含分时电价字符串（如"00:00~07:00,0.23;07:00~09:00,0.67"）和简单数字两种格式
3. `b4.csv` (13,290行) — 功率段装机功率：power_lt_30kw, power_30_120kw, power_120_360kw, power_gte_360kw, total_power
4. `场站网格/b1_with_grid_strict_polygon.csv` (13,456行) — 场站-网格关联：含"所属网格编号"（如L2BABC06-XX001）
5. `GPIP_M_GRID_L2_INFO.csv` (1,346行) — 网格几何信息

### 清洗脚本（位于 backend/data/pipeline/）
- `utils.py` — 工具函数（码表映射、电价解析、区域/业态推断）
- `clean_stations.py` — 主清洗脚本

### 清洗产出（位于 data/cleaned/）
- `stations_static.jsonl` — 10,942行清洗后的场站静态数据
- `stations_static_summary.csv` — 质量摘要

### 处理文档
- `data/schema/DATA-PIPELINE-v1.md` — 完整的数据处理方案

---

## 清洗规则（预期行为）

### 1. 去重规则
- 表1有13,456行但station_id有重复，去重后应为~10,942行
- 去重策略：按station_id分组，保留非空字段最多的行
- b2有14,711行也存在重复，去重后应为~11,923行
- 最终合并结果应为10,942行，无重复station_id

### 2. 电价解析规则
- b2的electricity_fee和service_fee有两种格式：
  - 简单数字（如"3.0000"）→ 解析为单一时段 00:00~24:00
  - 时段字符串（如"00:00~07:00,0.23;07:00~09:00,0.67"）→ 解析为多时段结构
- 解析结果应为JSON：{periods: [{start, end, price}], avg_price, min_price, max_price}
- 空值应保留为null，不应报错

### 3. 码表映射规则
- land_property: 1=国有用地, 2=集体用地, 3=私有用地, 4=租赁用地, 10=商业用地, 255=其他
- service_car_types: 逗号分隔数字，如"2,3,6"→["出租车","物流车","私家车"]
- station_status: 5=运营中, 50=运营中

### 4. b4聚合规则
- b4中同一个station_id可能对应多个operator_id
- 应按station_id分组，对各功率段求和
- 聚合后应有~10,815行

### 5. 网格关联规则
- 读取b1_with_grid_strict_polygon.csv的"所属网格编号"字段
- 按station_id左连接（注意去重，该文件有重复station_id）
- 网格编号前缀映射：L2NS=南山区, L2FT=福田区, L2LH=龙华区, L2LG=龙岗区, L2BABC=宝安区, L2GM=光明区, L2PS=坪山区, L2LYT=盐田区, L2LDP=大鹏新区, L2LSS=罗湖区

### 6. 区域推断规则
- 优先级1：从station_name关键词推断（南山→南山区, 福田→福田区...）
- 优先级2：从grid_code前缀推断
- 名称推断为空时，用网格推断填充

### 7. 业态推断规则
从station_name提取：
- 交通枢纽: 地铁站, 地铁, 公交总站, 车站, 机场, 港口
- 商业区: 商场, 购物中心, MALL, 商业街
- 办公区: 大厦, 中心, 广场, 科技园, 写字楼, 工业园
- 住宅区: 小区, 花园, 家园, 公寓, 村, 苑
- 工业区: 工厂, 工业区, 产业园, 物流园, 仓库
- 旅游景区: 公园, 景区, 酒店, 度假村

### 8. 充电桩类型推断
- "直流"/"快充"/"直流站" → 直流
- "交流"/"慢充"/"交流桩" → 交流
- 其余 → null

---

## 校验任务

请执行以下检查并输出报告：

### A. 数据量校验
1. 读取stations_static.jsonl，统计总行数和唯一station_id数
2. 验证是否为10,942行且无重复
3. 抽样检查几个station_id，确认去重策略是否正确

### B. 字段覆盖率校验
统计以下字段的非空比例：
- electricity_fee_parsed
- service_fee_parsed
- region
- grid_code
- business_type
- charger_type
- total_power
- land_property_desc
- service_car_types_desc

预期：电价~95%, 行政区~88%, 网格~93%, 功率~97%, 业态~47%, 充电桩~9%

### C. 电价解析校验
1. 抽样10条有electricity_fee_parsed的记录，人工验证解析是否正确
2. 检查是否有解析失败但原值非空的情况
3. 检查时段不连续的情况是否被正确标记

### D. 码表映射校验
1. 抽样检查land_property_desc、station_status_desc、service_car_types_desc是否正确
2. 检查是否有未映射的码值

### E. 网格关联校验
1. 检查grid_code字段是否存在
2. 抽样5条记录，验证grid_code前缀与region是否一致
3. 检查无grid_code的记录，region是否通过名称推断填充

### F. 业态推断校验
1. 抽样20条有business_type的记录，人工判断推断是否合理
2. 抽样20条无business_type的记录，分析名称是否确实无法推断
3. 统计各业态类型的分布数量

### G. 边界情况检查
1. 检查空值处理：busine_hours为空时是否填充为"00:00~24:00"
2. 检查异常值：total_installed_power为0或负数的情况
3. 检查经纬度：是否有超出深圳范围的坐标（深圳大致范围：lng 113.7-114.8, lat 22.4-22.9）

---

## 输出格式

请输出一份结构化校验报告，包含：

```
# 交叉校验报告

## 执行摘要
- 总体结论：[通过/有问题]
- 发现的问题数量：X个
- 严重级别问题：X个

## 逐项检查结果

### A. 数据量校验
- 预期：10,942行，无重复
- 实际：[你的统计结果]
- 结论：[通过/不通过]
- 备注：[如有问题请说明]

### B. 字段覆盖率校验
[表格展示各字段覆盖率，与预期对比]

### C-G. [同上格式]

## 问题清单
| 编号 | 严重程度 | 位置 | 问题描述 | 修复建议 |
|------|---------|------|---------|---------|
| 1 | 高/中/低 | clean_stations.py:XX行 | ... | ... |

## 建议
[整体评价和后续建议]

## 校验置信度
- 高置信度（已验证）：...
- 中置信度（抽样验证）：...
- 低置信度（无法验证）：...
```

---

## 附录：抽样检查建议
建议重点抽查以下station_id：
- "123"（壳牌深圳宝安机场超充站）— 含直流关键词、有电价、有网格
- "254"（公园大地45栋）— 住宅区、交流桩、有网格
- "4403061612010001"（青禾马家龙充电站直流）— 含直流后缀、有完整电价
- 任选3-5个无grid_code的记录 — 验证行政区是否通过名称推断
- 任选3-5个business_type为空的记录 — 验证名称确实无法推断业态

---

## 给你的权限
你可以：
1. 读取项目目录下的所有文件（backend/data/pipeline/*.py, data/schema/*.md, data/cleaned/*.jsonl）
2. 读取原始参考数据（/Users/xiasanw/work/2030数据/ 下的CSV和Excel文件）
3. 运行Python脚本进行统计和验证
4. 输出详细的校验报告

## 阶段2新增校验任务（时序聚合 + 区域填充）

### H. 时序聚合校验
1. 读取 `result_power_by_slot.csv`，统计总行数、唯一station_id数、日期范围
2. 验证 `compute_metrics.py` 的聚合逻辑：
   - 日均充电量 = 每天24小时功率之和的均值
   - 利用率 = 每小时功率 / 装机功率（已截断至1.0）
   - peak_hour/valley_hour = 按小时分组后平均功率的最高/最低时段
3. 抽样3-5个有真实时序数据的场站，手动计算验证指标

### I. 区域均值填充校验
1. 检查 `stations_raw.jsonl`：无时序数据的场站是否 avg_daily_energy_kwh=null
2. 检查 `stations.jsonl`：无时序数据的场站是否被填充，且 `metrics_estimated=True`
3. 验证填充策略优先级：
   - 优先同 region + 同 business_type
   - 次优先同 region
   - 兜底全市均值
4. 检查 `estimation_source` 字段是否正确标记填充来源
5. 验证 `season_stats` 是否也被正确填充（Demo版）

### J. 双版本一致性校验
1. 对比 `stations_raw.jsonl` 和 `stations.jsonl`，确认：
   - 有时序数据的场站两版本指标完全一致
   - 无时序数据的场站：raw版为null，demo版为填充值
   - 总记录数一致（10,942）

### K. 数据质量校验
1. 检查利用率分布：最大值是否 ≤1.0
2. 检查 avg_daily_energy_kwh 是否有异常负值
3. 检查 peak_hour/valley_hour 是否为合法的 00:00~23:00 格式
4. 统计 metrics_estimated 的分布（按 region）

---

## 注意
- 不要修改任何文件（只读）
- 如发现代码问题，在报告中指出位置和修复建议，但不要直接改代码
- 重点关注"规则是否被正确执行"，而非"规则是否合理"（规则合理性由人类评审）
