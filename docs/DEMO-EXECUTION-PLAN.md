# ChargeMind 黑客松 Demo 执行计划

> **前提声明**：本 Demo 暂无真实算法预测模型。算法通道为基于规则的 Stub，后续由课题组训练模型后替换。RAG 知识库为轻量版，基于已有清洗数据构建。
>
> **目标**：48-72 小时内产出可演示的完整产品。

---

## 一、Demo 核心体验

```
用户输入场站描述
    ↓
系统引导追问（补充关键信息）
    ↓
【三引擎并行诊断】
    ├──→ 竞争定位分析（硬数据硬算：基准价、价差、份额错配、功率错配 TVD）
    ├──→ RAG 引擎（相似场站检索 + Chat 重排序 + LLM 分析）
    └──→ LLM 异常识别（功率/电价/利用率异常检测与解释）
    ↓
可视化仪表盘报告（5 维雷达图 + 图表 + 可信度标签 + 提升路径卡片）
```

> **核心设计原则**：硬数据硬算，LLM 只做叙事包装 + 异常检测，不生成数字。每个数据点带可信度标签（⭐⭐⭐实测 / ⭐⭐推演 / ⭐估算 / ⚠️异常）。

---

## 二、技术架构（极简版）

```
┌─────────────────────────────────────────────┐
│  前端：React + TypeScript + Tailwind + shadcn/ui │
│  页面1：场站描述输入                            │
│  页面2：引导问卷（追问关键信息）                 │
│  页面3：诊断报告（双引擎对比 + 建议）            │
└─────────────────────────────────────────────┘
                      │ HTTP
                      ▼
┌─────────────────────────────────────────────┐
│  后端：FastAPI + Python 3.9                   │
│  POST /api/extract    → LLM 解析为结构化画像  │
│  POST /api/enrich     → 追问缺失字段          │
│  POST /api/diagnose   → 双引擎并行 → 综合报告 │
│                      ↑ ChromaDB 本地向量库    │
└─────────────────────────────────────────────┘
```

---

## 当前进度（实时更新）

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端骨架（FastAPI） | ✅ 完成 | `main.py` + `config.py` + CORS |
| RAG 数据层 | ✅ 完成 | 10,942 条场站已索引到 ChromaDB（78MB），含 grid 生态策略 |
| Chat 重排序 | ✅ 完成 | `core/reranker.py` — DeepSeek 精排 Top-5，附 similarity_reason |
| 诊断接口 | ✅ 完成 | `/extract` `/enrich` `/diagnose` 三端点 |
| 双 API 配置 | ✅ 完成 | Kimi Embedding + DeepSeek v4-pro Chat |
| 向量数据库 | ✅ 已提交git | `backend/chroma_db/`，团队成员无需重建 |
| **前端** | 🚧 **进行中** | React + TS + Tailwind v4，三页面条件渲染，Context 状态管理 |
| 前端对接手册 | ✅ 完成 | `前端对接手册.md` — API schema + TS 类型 + UI 建议 |
| 输出方向技术评审 | ✅ 完成 | `输出方向技术评审.md` — 融合方案已确定 |
| 竞争定位分析模块 | ⏳ 待开始 | 硬算指标：基准价、价差、份额错配、功率错配 TVD |
| 功率错配 + 电池容量分析 | ⏳ 待开始 | TVD + 车型-功率交叉矩阵 + 电池容量建议 |
| 品牌构成 + 季节波动 | ⏳ 待开始 | vehicle_tag_global_profile 解析 |
| 竞品价格对标 | ⏳ 待开始 | 同 grid 竞品分时段价格对比 |
| LLM 异常识别 | ⏳ 待开始 | 替代 mock RAG analysis |
| 报告生成模块 | ⏳ 待开始 | `core/report.py` 待抽取 |

---

## 三、关键假设与约束

| 项 | 现状 | Demo 策略 |
|---|---|---|
| 算法模型 | ❌ 无 | **Stub**：基于规则的预测，低置信度标记 |
| RAG 知识库 | ✅ 有 10,942 条场站数据 | ChromaDB + 轻量嵌入 |
| LLM | ✅ Kimi API 可用 | 解析输入、分析相似场站、生成报告 |
| 前端 | ⚠️ 需新建 | React + shadcn/ui，暗色主题 |

### LLM 配置

```bash
# .env 文件
KIMI_API_KEY=sk-xxx
KIMI_BASE_URL=https://api.kimi.com/coding/v1
DEFAULT_MODEL=kimi-latest
```

> **备注**：当前仓库为 **私有仓库**，`.env` 文件已提交 git 供团队共享。
>
> ⚠️ **TODO: 仓库转 public 前必须删除 `.env` 文件或清空 KEY**，避免 API Key 泄露。

### 数字策略约束（Demo 阶段）

报告中的数字分三层处理，防止评委 argue：

| 层级 | 给什么 | 不给什么 | 被追问时的回应 |
|------|--------|---------|--------------|
| **诊断层** ⭐⭐⭐ | 点估计（TVD 0.871、价差 ¥0.13、份额差距 +6.9%） | 宽区间 | "公式：0.5×Σ\|P-Q\|，数据在这" |
| **推演层** ⭐⭐ | **窄区间**+强标注（`[6%, 10%]`，弹性 1.5-2.5） | 宽区间如"3%-15%"、单点"~8%" | "行业弹性 1.5-2.5，base_util 取容量份额" |
| **建议层** ⭐⭐ | 公式透明的数字（峰谷优化 ¥3.2万 = 240×40%×0.9×365） | 概率、无依据收益 | "公式在这，假设是峰谷价差不变" |
| **不给** — | — | "概率 70%""提升利用率 8%" | "目前没有历史干预数据，算不了" |

**核心原则**：能讲清楚公式来源的数字 → 可以给；讲不清楚的 → 坚决不给。

---

## 四、三阶段实施

### Phase A：后端骨架 + RAG（目标 4h）

#### A1. 初始化 FastAPI（30min）

**产出**：
- `backend/main.py` — FastAPI 入口 + CORS
- `backend/requirements.txt` — fastapi, uvicorn, chromadb, openai
- `backend/config.py` — 配置管理（Kimi API Key 等）

**验收**：`uvicorn main:app --reload` 启动成功，`GET /health` 返回 `{"status":"ok"}`

#### A2. RAG 数据层（1h）

**产出**：
- `backend/rag/indexer.py` — 读取 `stations.jsonl`，每条转自然语言文档，生成 embedding，存入 ChromaDB
- `backend/rag/retriever.py` — 根据场站画像检索 Top-5 相似场站

**场站文档模板**（每条场站转成一段文字）：
```
{station_name}位于{region}，属于{business_type}，装机功率{total_installed_power}kW，
日均充电量{avg_daily_energy_kwh}度，利用率{avg_utilization}，高峰时段{peak_hour}。
电价结构：{electricity_fee_desc}。服务车型：{service_car_types_desc}。
```

**验收**：运行 `python backend/rag/indexer.py`，ChromaDB 成功索引 10,000+ 条记录，检索测试返回相关结果。

#### A3. 算法 Stub（30min）

**产出**：`backend/core/stub.py`

**逻辑**：
```python
def predict(station_profile):
    # 利用率 = 区域均值 × 业态系数 × 规模系数（纯规则，无模型）
    base_util = REGION_AVG_UTIL.get(station_profile.region, 0.05)
    biz_factor = BIZ_FACTOR.get(station_profile.biz_type, 1.0)
    predicted_util = base_util * biz_factor

    # 收益 = 充电量 × 电价 - 成本（简化公式）
    daily_kwh = station_profile.total_power * predicted_util * 24
    annual_revenue = daily_kwh * 365 * 0.6  # 假设平均电价+服务费 0.6元/度
    annual_cost = station_profile.monthly_rent * 12 + station_profile.staff_count * 80000

    return {
        "predicted_utilization": round(predicted_util, 3),
        "annual_profit": round(annual_revenue - annual_cost, 2),
        "confidence": 0.3,  # 明确标记低置信度
        "note": "基于区域基准的规则预测，非真实模型输出"
    }
```

#### A4. 诊断接口（2h）

**产出**：`backend/api/diagnosis.py` — 三个 POST 端点

| 端点 | 功能 | 说明 |
|------|------|------|
| `POST /api/extract` | LLM 解析用户自然语言输入 | 输出结构化场站画像 |
| `POST /api/enrich` | 判断缺失字段，生成追问 | 返回下一个问题 |
| `POST /api/diagnose` | 双引擎并行诊断 | Stub + RAG → 综合报告 |

**验收**：curl 三个接口均返回预期结构。

---

### Phase B：前端（目标 6h）

#### B1. 初始化项目（30min）

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install @radix-ui/react-* class-variance-authority clsx tailwind-merge lucide-react
```

**产出**：可运行的 React + TS + Tailwind 项目骨架。

#### B2. 页面1：场站描述输入（1.5h）

**产出**：`frontend/src/pages/StationInputPage.tsx`

- 大标题 + 副标题
- 大文本输入框（placeholder：示例描述）
- "使用示例"按钮
- 提交按钮 → 调用 `/api/extract` → 跳转到问卷页

#### B3. 页面2：引导问卷（2h）

**产出**：`frontend/src/pages/EnrichPage.tsx`

- 进度条：Step 2/3
- 卡片式问题，一次一题，淡入动画
- 问题列表：
  1. 场站位置（区/街道）
  2. 充电桩数量
  3. 装机总功率（kW）
  4. 周边主要业态（住宅/办公/商业/工业）
  5. 当前电价（峰/平/谷）
  6. 月租金（元）
  7. 运维人员数
- "跳过"按钮（用默认值）
- 全部完成后 → 调用 `/api/diagnose` → 跳转到报告页

#### B4. 页面3：诊断报告（2h）

**产出**：`frontend/src/pages/ReportPage.tsx`

**设计**：可视化仪表盘，不是 Markdown 文字报告。详见 [`输出界面.md`](./输出界面.md)。

```
首屏  │ 🏆 称号 + 5维雷达图 + 一句话痛点诊断               │
      │ "大炮打蚊子——地段极佳，装了一堆超快充，但周边车用不上" │
      │                                                    │
二屏  │ 4 张 KPI 卡片（带可信度标签）                       │
      │ 均衡利用率区间(⭐⭐) | 年收益预估(⭐⭐) | 竞争基准价差(⭐⭐⭐) | 高峰时段(⭐⭐⭐) │
      │                                                    │
三屏  │ ⚡ 功率错配 + 电池容量分析（双屏联动）               │
      │ 左: 供给 vs 需求 柱状图 + TVD 分数                  │
      │ 右: 电池容量分布 + 精准功率建议                     │
      │                                                    │
四屏  │ 💰 竞品价格对标 + 品牌构成                          │
      │ 你的分时段价格 vs 同 grid 竞品                      │
      │ 周边私家车品牌构成                                  │
      │                                                    │
五屏  │ 📊 标杆场站对比卡片（RAG + Chat 重排）              │
      │ 每条带可信度标签 + similarity_reason + key_comparison │
      │                                                    │
六屏  │ 📈 趋势推演折线图（含季节波动修正）                 │
      │ 三情景 × 12 个月                                    │
      │                                                    │
七屏  │ 💡 提升路径卡片                                    │
      │ 只给"公式透明"的数字，不给概率/无依据的收益预测    │
      │ 例: 峰谷优化 ¥3.2万/年（公式: 240度×40%×¥0.9×365） │
      │                                                    │
八屏  │ 📝 LLM 异常识别 + 竞争定位详情（可折叠）            │
```

**依赖**：`recharts`（图表库）+ `lucide-react`（图标库），纯 Tailwind CSS 手写组件（不使用 shadcn/ui CLI）。

**验收**：能从 `/api/diagnose` 返回的 JSON 正确渲染所有图表模块。

---

### Phase C：联调 + 美化（目标 2h）

- 前后端联调（1h）
- 动画效果：进度条、打字机、淡入（30min）
- 暗色主题统一（15min）
- 移动端适配（15min）

---

## 五、时间线（假设连续开发）

| 时间 | 任务 |
|------|------|
| 0:00 - 0:30 | Phase A1：FastAPI 骨架 |
| 0:30 - 1:30 | Phase A2：RAG 索引 + 检索 |
| 1:30 - 2:00 | Phase A3：算法 Stub |
| 2:00 - 4:00 | Phase A4：诊断接口（extract/enrich/diagnose）|
| 4:00 - 4:30 | Phase B1：前端项目初始化 |
| 4:30 - 6:00 | Phase B2：输入页 |
| 6:00 - 8:00 | Phase B3：问卷页 |
| 8:00 - 10:00 | Phase B4：报告页 |
| 10:00 - 12:00 | Phase C：联调 + 美化 |

**总计：约 12 小时**

---

## 六、竞争定位分析（替代原算法 Stub）

> **设计决策**：原 `algorithm_stub` 单点预测（`predicted_utilization = 0.042`）被替换为竞争定位分析——全部基于硬数据硬算，零模型假设。详见 [`输出方向技术评审.md`](./输出方向技术评审.md)。

### 6.1 硬算指标（⭐ 级实测，零假设）

| 输出 | 计算方式 | 标签 |
|------|---------|------|
| 竞争基准价 | 同 grid 竞品服务费按桩数加权平均 | ⭐⭐⭐ 实测 |
| 你的价差 | 你的服务费 − 基准价 | ⭐⭐⭐ 实测 |
| 容量份额 vs 实际份额 | 你的功率占比 vs 你的充电量占比 | ⭐⭐⭐ 实测 |
| 功率错配 TVD | 供给功率分布 vs 需求功率分布（power_level_mix） | ⭐⭐⭐ 实测 |

### 6.2 弹性假设推演（需诚实标注）

| 输出 | 计算方式 | 标签 |
|------|---------|------|
| 均衡利用率区间 | 假设弹性 ε ∈ [1.5, 2.5] 的窄区间推演，波动控制 2 倍以内 | ⭐⭐ 推演（标注"基于行业平均弹性假设"）|

### 6.3 示例输出

```
你在网格 GXD003:
  竞争基准价 ¥0.32/度 → 你收 ¥0.45 → 价差 +41%
  你装了网格 20.3% 的容量 → 只吃到 0.19% 的充电量
  你的桩型偏大（76% ≥120kW）→ 但 95% 的车只需要 120kW 以下
  → 容量换不来量——极严重的过度投资
```

### 6.4 新增数据维度（P0，数据已就绪）

基于 `vehicle_tag_global_profile`（93 标签，10,197 站全覆盖）：

| 模块 | 数据来源 | 标签 |
|------|---------|------|
| 品牌构成矩阵 | 标签名 Band 解析，限定"私家车市场竞争格局" | ⭐⭐⭐ |
| 电池容量集中度 → 精准功率建议 | battery_capacity 14 档分布 | ⭐⭐⭐ |
| 季节波动分析 | total_cars_by_date_type（夏季/冬季/国庆/春节）| ⭐⭐⭐ |

> **注意**：品牌分析仅覆盖 52/93 标签（有 Band 信息的私家车/营运车），41 个无品牌标签（出租车、公交车等）不参与品牌统计。前端标题必须写"私家车市场竞争格局"。

### 6.5 后端产出文件

| 文件 | 说明 |
|------|------|
| `backend/core/positioning.py` | 竞争定位分析（硬算指标） |
| `backend/core/elasticity.py` | 弹性假设推演（均衡利用率区间） |
| `backend/core/brand_analysis.py` | 品牌构成 + 电池容量 + 季节波动解析 |

---

## 七、RAG 流程详细设计

### 当前检索策略：向量粗检 + Chat 精排

```
用户画像
    ↓
【向量检索 Top-15】→ 基于 grid 生态 + 区域 + 功率配置（Kimi Embedding）
    ↓
【Chat 重排序】→ DeepSeek v4-pro 从运营视角评估对比价值，精排 Top-5
    ↓
【附带解释】→ 每条相似场站带 similarity_reason + key_comparison + rerank_score
```

> 详见 `backend/core/reranker.py`（Chat 重排序器）和 `前端对接手册.md`（similar_stations 新字段）。

### 检索文档构建策略

以**需求侧真实生态（grid 数据）为核心**，供给侧配置为辅助。利用率/日均充电量等估算指标不参与检索。

> 详见 `backend/rag/indexer.py` → `build_station_doc()`

---

## 八、产出清单

### 后端

| 文件 | 说明 |
|------|------|
| `backend/main.py` | FastAPI 入口 |
| `backend/config.py` | 配置管理 |
| `backend/requirements.txt` | 依赖 |
| `backend/api/diagnosis.py` | 诊断接口（extract / enrich / diagnose）|
| `backend/core/stub.py` | 算法 Stub（基于规则，待替换）|
| `backend/core/reranker.py` | Chat 重排序器（DeepSeek 精排 Top-5）|
| `backend/core/positioning.py` | 竞争定位分析（硬算指标）|
| `backend/core/brand_analysis.py` | 品牌构成 + 电池容量 + 季节波动 |
| `backend/core/report.py` | 报告合并与格式化 |
| `backend/rag/indexer.py` | 场站数据向量化索引（grid 生态策略）|
| `backend/rag/retriever.py` | 相似场站检索 + Chat 重排候选集 |

### 前端

| 文件 | 说明 |
|------|------|
| `frontend/src/App.tsx` | 路由 |
| `frontend/src/pages/StationInputPage.tsx` | 场站描述输入 |
| `frontend/src/pages/EnrichPage.tsx` | 引导问卷 |
| `frontend/src/pages/ReportPage.tsx` | 诊断报告 |
| `frontend/src/lib/api.ts` | API 客户端 |
| `frontend/src/types/diagnosis.ts` | TypeScript 类型定义 |

---

## 九、后续替换路径

| Demo 组件 | 后续替换 |
|-----------|---------|
| `backend/core/stub.py` | 已被竞争定位分析替代，保留作为参考 |
| 竞争定位分析 | 接入真实博弈模型（需历史面板数据估计弹性系数）|
| `backend/rag/` | 升级为混合检索（向量 + 关键词 + 重排序）|
| `backend/api/diagnose` | 接入 LangGraph 完整流程编排 |
| 前端页面 | 增加数据看板、历史记录、导出功能 |
| 品牌分析 | 扩展覆盖无品牌标签（出租车、公交车等）的42个标签 |

---

---

## 前端方案选型

### 目标

- **好看**：暗色主题、现代化 UI、数据可视化
- **好交互**：多页面流程（输入→问卷→报告）、动画过渡、实时反馈
- **内容能传到 API**：表单数据通过 HTTP POST 提交到后端

### 技术栈

| 技术 | 用途 | 理由 |
|------|------|------|
| **React 18** | UI 框架 | 生态成熟，组件化开发 |
| **TypeScript** | 类型安全 | 减少运行时错误，提升开发体验 |
| **Vite** | 构建工具 | 启动快（秒级），HMR 快 |
| **Tailwind CSS** | 样式 | 原子化 CSS，暗色主题支持好，不写 CSS 文件 |
| **shadcn/ui** | 组件库 | 基于 Radix UI， accessibility 好，暗色主题默认支持，组件好看 |
| **React Router** | 路由 | 三页面跳转（/input → /enrich → /report）|
| **Axios** | HTTP 客户端 | API 调用，拦截器统一处理 |

### 页面设计

**页面1：`/input` 场站描述输入**
- 大标题 + 副标题
- 大文本输入框（placeholder 放示例文案）
- "使用示例"按钮（一键填入）
- 提交按钮 → 调用 `/api/extract` → 跳转到问卷页

**页面2：`/enrich` 引导问卷**
- 顶部进度条："Step 2/3：补充关键信息"
- 卡片式问题，一次一题，淡入动画
- 问题列表：区域、业态、装机功率、桩数、月租金、人员、电价
- "跳过"按钮（用默认值）
- 全部完成后 → 调用 `/api/diagnose` → 跳转到报告页

**页面3：`/report` 诊断报告**
- 加载动画："双引擎诊断中..." + 进度条
- 双引擎对比面板（左右分栏）：
  - 左：算法 Stub 预测（利用率、年利润）
  - 右：RAG 分析（相似场站、优化建议）
- 综合建议区：Markdown 渲染，每条建议带来源标签
- "重新诊断"按钮

### 与后端的交互流程

```
页面1 /input
  用户输入描述 → POST /api/extract → 获取结构化画像
  → 跳转到 /enrich?profile=xxx

页面2 /enrich
  读取 URL 参数中的 profile
  调用 POST /api/enrich → 获取下一个问题
  用户回答 → 更新 profile
  循环直到 complete=true
  → POST /api/diagnose → 获取诊断结果
  → 跳转到 /report?result=xxx

页面3 /report
  读取 URL 参数中的 result
  渲染双引擎对比 + 建议报告
```

---

## 报告输出 Prompt 与前端界面设计

> 📄 详见 **[输出界面.md](./输出界面.md)**  
> 包含：LLM 结构化 JSON Prompt 模板 + 可视化仪表盘组件设计 + 完整 TypeScript 类型 + 前端图表选型

---

*版本: v1.4*
*日期: 2026-04-25*
*标注: 竞争定位分析替代算法 Stub，三引擎架构确立，新增品牌/电池容量/季节波动维度，可视化仪表盘方案确认*

---

## 更新记录

### 2026-04-24 前端开发启动

**技术决策调整（基于评审报告 + 实施权衡）：**

| 议题 | 评审方案 | 实际执行方案 | 理由 |
|------|---------|-------------|------|
| 状态管理 | Zustand | React Context + useState | 线性三页面流程，Context 足够，少一依赖 |
| 路由 | React Router | 条件渲染 (`useState` 控制 page) | 严格线性流程，省掉路由配置 |
| shadcn/ui | CLI 初始化 | 手动 Tailwind v4 + copy 组件源码 | 避免 Tailwind v4 / React 19 兼容性风险 |
| Mock 兜底 | 未提及 | 前端内置 mock 数据 | 保证 Demo 不因 LLM API 故障而中断 |

**开发启动检查清单：**
- [ ] 安装依赖（Tailwind v4 + react-markdown + remark-gfm）
- [ ] 清理模板文件
- [ ] 配置 Vite 代理 + 路径别名
- [ ] 三页面实现（输入 / 问卷 / 报告）
- [ ] 前后端联调

**目标**：5-6 小时内产出可演示的完整前端。

---

## 十、顶层设计：十维数据源检索架构（2026-04-24 更新）

### 核心原则

> **"异常数据不做数值分析，但交给 LLM 分析其潜在含义。"**

算法层只处理可信的结构化数据（grid 生态、区域、价格结构）。
异常/低质量数据（利用率、功率异常值等）原样传给 DeepSeek，由 LLM 做语义级原因推断。

### 十维数据源

| 维度 | 字段 | 数据质量 | 处理方式 | 检索权重 |
|------|------|---------|---------|---------|
| **1. 区域定位** | `region` | ⭐⭐⭐ 高 | 精确匹配，同片区优先 | 🔴 最高 |
| **2. Grid 车辆生态** | `grid_vehicle_profile` | ⭐⭐⭐ 高（93.2%覆盖） | 核心检索维度 | 🔴 最高 |
| **3. 场站功率配置** | `le_30kw_count` / `gt_360kw_count` 等 | ⭐⭐ 中 | 辅助对比，异常值（>10万kW）不纳入计算 | 🟡 中 |
| **4. 电价结构** | `electricity_fee_parsed` | ⭐⭐⭐ 高（94.5%覆盖） | 竞品价格对标核心 | 🔴 最高 |
| **5. 服务费结构** | `service_fee_parsed` | ⭐⭐⭐ 高（94.5%覆盖） | 竞品价格对标核心 | 🔴 最高 |
| **6. 服务车型** | `service_car_types_desc` | ⭐⭐ 中 | 客群匹配 | 🟡 中 |
| **7. 土地属性** | `land_property_desc` | ⭐⭐ 中 | 成本结构参考 | 🟢 低 |
| **8. 营业时间** | `busine_hours` | ⭐⭐ 中 | 运营策略参考 | 🟢 低 |
| **9. 周边竞品价格** | 同 grid / 2km 内其他场站价格 | ⭐⭐⭐ 高（基于现有数据计算） | 价格竞争力分析 | 🔴 最高 |
| **10. 季节波动** | `season_stats` | ⭐⭐ 中（部分场站缺失） | 趋势参考，异常季节标记给 LLM | 🟡 中 |

### 数据分层处理策略

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: 可信数据层（算法直接计算）                          │
│  ├── grid_vehicle_profile（车流量、车型、SOC、迁移）           │
│  ├── electricity_fee_parsed / service_fee_parsed（价格结构）  │
│  └── region（区域匹配）                                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 辅助数据层（参与检索，不做数值计算）                 │
│  ├── 功率配置（异常值过滤后使用）                              │
│  ├── 服务车型、土地属性、营业时间                             │
│  └── 季节统计（缺失场站跳过）                                 │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 异常数据层（原样给 LLM，不做任何计算）              │
│  ├── avg_utilization（19.6% < 1%，数据质量差）               │
│  ├── avg_daily_energy_kwh（网格级平均，非场站实际）           │
│  └── total_installed_power 异常值（>10万kW）                  │
└─────────────────────────────────────────────────────────────┘
```

### 异常值 → LLM 语义分析流程

```python
def analyze_anomalies(station_data: dict) -> dict:
    """
    识别异常值，交给 DeepSeek 分析潜在原因。
    不做数值修正，只做语义级解释。
    """
    anomalies = []
    
    # 功率异常
    power = station_data.get("total_installed_power", 0)
    if power > 100000:
        anomalies.append({
            "field": "total_installed_power",
            "value": power,
            "anomaly_type": "极端高值",
            "question": "该场站装机功率为何远超常规？"
        })
    
    # 利用率异常
    util = station_data.get("avg_utilization")
    if util is not None and util < 0.01:
        anomalies.append({
            "field": "avg_utilization",
            "value": util,
            "anomaly_type": "接近零值",
            "question": "该场站利用率几乎为零，可能原因是什么？"
        })
    
    # 日均充电量异常低
    energy = station_data.get("avg_daily_energy_kwh", 0)
    if energy > 0 and energy < 10:
        anomalies.append({
            "field": "avg_daily_energy_kwh",
            "value": energy,
            "anomaly_type": "异常低值",
            "question": "日均充电量极低，该场站是否新建或处于特殊状态？"
        })
    
    # 电价异常
    ef = station_data.get("electricity_fee_parsed", {})
    avg_price = ef.get("avg_price", 0)
    if avg_price > 50:  # 充美某些场站电费高达 75+ 元/度（明显异常）
        anomalies.append({
            "field": "electricity_fee_parsed.avg_price",
            "value": avg_price,
            "anomaly_type": "极端高值",
            "question": "电费均价异常高，是否为数据单位错误或特殊计费模式？"
        })
    
    # 调用 DeepSeek 分析异常原因
    if anomalies:
        llm_insights = _deepseek_analyze_anomalies(station_data, anomalies)
        return {
            "has_anomalies": True,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "llm_insights": llm_insights,
        }
    
    return {"has_anomalies": False}


def _deepseek_analyze_anomalies(station_data: dict, anomalies: list) -> str:
    """
    DeepSeek Chat 分析异常值的潜在原因。
    不修正数据，只提供语义级解释。
    """
    prompt = f"""
你是一位充电行业数据分析师。以下场站数据中存在异常值，请分析这些异常的可能原因。
不要修正数据，只需给出最可能的原因推断。

场站名称：{station_data.get('station_name', '未知')}
区域：{station_data.get('region', '未知')}

异常字段：
"""
    for a in anomalies:
        prompt += f"\n- {a['field']}: {a['value']}（{a['anomaly_type']}）→ {a['question']}"
    
    prompt += """

请用 1-2 句话简洁说明每个异常的最可能原因。格式：
1. [字段名]: [原因推断]
2. [字段名]: [原因推断]
"""
    
    # 调用 DeepSeek API
    ...
```

### 周边竞品价格对标（第九维）

基于现有 10,942 条数据，无需外部 API：

```python
def get_competitor_price_benchmark(station: dict, radius_km: float = 2.0) -> dict:
    """
    获取周边竞品价格对标数据。
    基于 Haversine 距离计算，纯数据计算，无需 LLM。
    """
    # 1. 同 grid 内竞品（最精准）
    same_grid = find_same_grid_competitors(station)
    
    # 2. 半径 2km 内竞品（直接竞品）
    nearby = find_nearby_competitors(station, radius_km=2.0)
    
    # 3. 计算价格统计
    my_price = get_total_avg_price(station)
    grid_avg = mean([get_total_avg_price(s) for s in same_grid])
    nearby_avg = mean([get_total_avg_price(s) for s in nearby])
    
    return {
        "my_avg_price": my_price,           # 我：电费+服务费均价
        "same_grid_avg": grid_avg,           # 同网格竞品均价
        "nearby_2km_avg": nearby_avg,        # 2km 竞品均价
        "same_grid_count": len(same_grid),   # 同网格竞品数量
        "nearby_2km_count": len(nearby),     # 2km 竞品数量
        "price_position": my_price / nearby_avg if nearby_avg else None,
        "is_price_leader": my_price < nearby_avg * 0.9,  # 低价领导者
        "is_price_premium": my_price > nearby_avg * 1.1, # 高价溢价
    }
```

### 检索流程更新

```
用户画像
    ↓
【向量检索】→ 基于 grid 生态 + 区域 + 功率（弱化）
    ↓
【Chat 重排序】→ DeepSeek 精排 Top-5，附 similarity_reason
    ↓
【异常分析】→ DeepSeek 分析检索结果中的异常值
    ↓
【竞品对标】→ 纯数据计算，周边 2km 价格对比
    ↓
【综合诊断】→ Stub（可信数据）+ RAG（十维分析）+ 异常解释
```

---

## 十一、更新记录

### 2026-04-25 输出方向技术评审 + 方案融合

| 变更 | 说明 |
|------|------|
| 算法 Stub → 竞争定位分析 | 放弃单点预测，改为 4 项硬算指标 + 弹性窄区间推演（ε∈[1.5,2.5]） |
| 双引擎 → 三引擎 | 新增 LLM 异常识别作为第三引擎 |
| 雷达图 6→5 维 | 地段禀赋/硬件适配/定价精准/运营产出/需求饱和度 |
| 新增数据维度 | 品牌构成（P0）、电池容量（P0）、季节波动（P0）、充电紧迫度（P1）|
| 可信度标签系统 | ⭐⭐⭐实测 / ⭐⭐推演 / ⭐估算 / ⚠️异常，全前端覆盖 |
| 报告页 | 从双面板 Markdown 改为 8 屏可视化仪表盘 |
| 博弈模型 | 降级为竞争定位分析，纳什均衡等面板数据到位后再议 |
| 单站聚焦验证 | 全部模块紧扣单场站诊断，分析单元为 grid |

> 详见 [`输出方向技术评审.md`](./输出方向技术评审.md)

### 2026-04-24 顶层设计重构

| 变更 | 说明 |
|------|------|
| 检索策略 | 从"运营指标主导"改为"grid 生态主导" |
| 异常处理 | 新增 DeepSeek 异常值语义分析层 |
| 竞品价格 | 新增基于现有数据集的 geo 竞品对标（第九维） |
| 数据源 | 明确十维分层（可信/辅助/异常三层） |
| 文档 | `indexer.py` / `retriever.py` 已按新策略重构 |

### 2026-04-24 前端开发启动

**技术决策调整（基于评审报告 + 实施权衡）：**
...
