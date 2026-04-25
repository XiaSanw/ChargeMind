# ChargeMind 前端界面开发进度

> 更新日期：2026-04-25

## 一、技术栈

- **框架**：React 19 + Vite + TypeScript
- **样式**：Tailwind CSS
- **动画**：Framer Motion
- **图表**：Recharts
- **Markdown 渲染**：react-markdown + remark-gfm
- **图标**：Lucide React

## 二、页面结构

| 页面 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 落地页 | `LandingPage.tsx` | ✅ 完成 | ChargeMind 品牌介绍 + 开始诊断入口 |
| 信息补充 | `EnrichPage.tsx` | ✅ 完成 | 多步骤问卷（select/multiselect/number/multi-number） |
| 报告页 | `ReportPage.tsx` | ✅ 完成 | 完整诊断报告展示 |

**数据流**：LandingPage → ConsultDialog（自然语言输入）→ EnrichPage（补全画像）→ ReportPage（展示报告）

## 三、报告页组件清单

### Dashboard 核心组件

| 组件 | 文件 | 功能 |
|------|------|------|
| Headline | `Headline.tsx` | 一句话痛点诊断 |
| RadarChart | `RadarChart.tsx` | 五维雷达图（地段/硬件/定价/运营/饱和度） |
| KPICards | `KPICards.tsx` | 4张KPI卡片（均衡利用率/年收益/基准价差/高峰时段） |

### 分析卡片（三栏布局）

| 组件 | 文件 | 功能 |
|------|------|------|
| PowerMismatchCard | `PowerMismatchCard.tsx` | TVD功率错配 + 供需对比条 + 主导错配 + 电池容量建议 |
| BrandAnalysisCard | `BrandAnalysisCard.tsx` | 品牌条形图 + CR3/CR5 + 专用桩洞察引导 + **区域品牌画像与用户场站对比** |
| CompetitivePositionCard | `CompetitivePositionCard.tsx` | Summary + 容量份额vs实际份额 + 基准价差 + **价格结构对比** + 均衡利用率 |

> 注：竞品价格对标（min/avg/max 三档）已合并到竞争定位卡片中，不再独立展示。

### 其他组件

| 组件 | 文件 | 功能 |
|------|------|------|
| DetailSection | `DetailSection.tsx` | 详细分析（Markdown，杂志编辑风格排版） |
| PathCards | `PathCards.tsx` | 提升路径卡片 |
| BenchmarkChart | `BenchmarkChart.tsx` | 竞品对比图表 |

## 四、已完成功能

### 1. 多步骤问卷（EnrichPage）
- [x] 支持 `text` / `number` / `select` / `multiselect` / `multi-number` 五种题型
- [x] `pile_breakdown`：慢充/快充/超充三台数量输入
- [x] `has_brand_pile` + `brand_piles`：品牌专用桩有无判断 + 各品牌数量输入
- [x] 条件追问：`brand_piles` 仅在 `has_brand_pile == "有"` 时追问
- [x] 进度条 + 阶段文字提示

### 2. 功率错配分析（PowerMismatchCard）
- [x] TVD 分数 + 错配等级
- [x] 4档功率供需对比条（慢充/快充/超充/极充）
- [x] 主导错配展示
- [x] **区域功率画像与用户场站对比**（pile_breakdown 三段式）
- [x] 电池容量建议

### 3. 品牌专用桩对比（BrandAnalysisCard）
- [x] 品牌条形图（含"非自有桩品牌"）
- [x] CR3/CR5 集中度
- [x] **三段式品牌对比**（区域需求画像 → 用户供给结构 → 供需诊断）
- [x] 排除 OtherBand 后的需求占比计算
- [x] 用户选"无"品牌桩也进行分析

### 4. 竞争定位分析（CompetitivePositionCard）
- [x] 容量份额 vs 实际份额（超额吸引/份额流失/基本匹配）
- [x] 竞争基准价差（全天均价）
- [x] **价格结构对比**（低谷/均价/高峰三档 + 峰谷比）
- [x] 均衡利用率区间推演

### 5. 详细分析（DetailSection）
- [x] Markdown 渲染（h2/h3/p/ul/li/blockquote/table/strong/hr）
- [x] 杂志编辑风格排版（装饰竖线、小横线列表、暗色表格、引用块）
- [x] 可折叠展开

## 五、待开发 / 计划中

- [ ] **加载界面动画**：电池充电动画 + 电流脉冲网络（方案 A+B）
- [ ] 报告导出（PDF）
- [ ] 诊断历史记录

## 六、Terminology 统一

所有用户面向文案中：
- `grid` → `区域`
- 功率档：`低速/中速/快充/超充` → `慢充/快充/超充/极充`
