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
【双引擎并行诊断】
    ├──→ 算法 Stub（基于规则的预测）← 标记为"算法预测"
    └──→ RAG 引擎（相似场站检索 + LLM 分析）← 标记为"知识库类比"
    ↓
综合报告（展示冲突与共识 + 优化建议）
```

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
| RAG 数据层 | ✅ 完成 | 10,942 条场站已索引到 ChromaDB（78MB）|
| 算法 Stub | ✅ 完成 | 基于区域均值×业态系数，标记 `is_stub: true` |
| 诊断接口 | ✅ 完成 | `/extract` `/enrich` `/diagnose` 三端点 |
| 双 API 配置 | ✅ 完成 | Kimi Embedding + DeepSeek v4-pro Chat |
| 向量数据库 | ✅ 已提交git | `backend/chroma_db/`，团队成员无需重建 |
| **前端** | ⏳ **待开始** | 需要选型并初始化 |
| 报告生成模块 | ⏳ 待开始 | `core/report.py` 待抽取 |
| 前后端联调 | ⏳ 待开始 | 待前端完成后进行 |

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

- 加载动画："双引擎诊断中..." + 进度条
- 双引擎对比面板（左右分栏）：
  ```
  ┌─────────────┬─────────────┐
  │ 🔧 算法预测   │ 🧠 知识库类比 │
  │ (Stub)       │ (RAG)        │
  ├─────────────┼─────────────┤
  │ 预测利用率    │ 相似场站Top3  │
  │ 预测年利润    │ 优化建议     │
  │ 置信度: 低   │ 相关度: 高   │
  └─────────────┴─────────────┘
  ```
- 综合建议区：Markdown 渲染，每条建议带来源标签
- "重新诊断"按钮

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

## 六、算法 Stub 详细设计

**明确声明**：此为基于规则的模拟预测，非真实机器学习模型。

```python
# backend/core/stub.py

REGION_AVG_UTIL = {
    "南山区": 0.0739, "福田区": 0.0467, "宝安区": 0.0311,
    "龙岗区": 0.0303, "龙华区": 0.0121, "罗湖区": 0.0467,
    "光明区": 0.0311, "坪山区": 0.0121, "盐田区": 0.0739,
    "大鹏新区": 0.0121, "前海": 0.0739, "未知": 0.0453,
}

BIZ_FACTOR = {
    "交通枢纽": 1.3, "商业区": 1.0, "办公区": 0.9,
    "住宅区": 0.7, "工业区": 1.1, "旅游景区": 0.6,
}

def algorithm_stub(profile: dict) -> dict:
    region = profile.get("region", "未知")
    biz_types = profile.get("business_type", [])
    total_power = profile.get("total_installed_power", 100)
    pile_count = profile.get("pile_count", 10)
    monthly_rent = profile.get("monthly_rent", 50000)
    staff_count = profile.get("staff_count", 3)
    price = profile.get("avg_price", 0.6)

    base = REGION_AVG_UTIL.get(region, 0.0453)
    factor = max(BIZ_FACTOR.get(b, 1.0) for b in biz_types) if biz_types else 1.0
    predicted_util = base * factor

    daily_kwh = total_power * predicted_util * 24
    annual_revenue = daily_kwh * 365 * price
    annual_cost = monthly_rent * 12 + staff_count * 80000

    return {
        "predicted_utilization": round(predicted_util, 3),
        "annual_revenue": round(annual_revenue, 2),
        "annual_cost": round(annual_cost, 2),
        "annual_profit": round(annual_revenue - annual_cost, 2),
        "confidence": 0.3,
        "is_stub": True,
        "note": "基于区域基准与业态系数的规则预测，非真实模型"
    }
```

---

## 七、RAG 流程详细设计

### 检索策略：三层漏斗 + 多路召回

**核心决策**：
- 业态：**可以放宽**（不严格限定，LLM 能看到跨业态创新做法）
- 区域：**分层**（先同区，不够再扩全市）
- 对标数量：**5-8 条**

```
用户描述 → 【第一层：精确匹配】
            region=用户区 AND biz_type 包含用户业态
            → 如果 ≥5 条，进入向量排序
            
            如果 < 5 条 → 【第二层：放宽业态】
            region=用户区 AND biz_type 放宽（近似业态）
            → 如果 ≥5 条，进入向量排序
            
            如果还 < 5 条 → 【第三层：去掉区域限制】
            biz_type 包含用户业态（全市范围）
            → 一定够（10,000+ 数据）
            
            ↓
            【向量排序】按语义相似度排序，取 Top-5~8
```

### 给 LLM 的输入格式

不是文字段落，而是一张**结构化对比表**，LLM 像领域专家一样读数据找规律。

| 组别 | 字段 | 说明 |
|------|------|------|
| **身份定位** | 场站名称、区域、业态类型、数据可信度 | 让 LLM 知道"这是谁" |
| **规模配置** | 装机总功率、充电桩数、快充桩数、慢充桩数、快充占比、功率段分布 | "硬件配得对不对" |
| **运营效率** | 利用率、日均充电量、单桩日均充电量、高峰时段、低谷时段 | "赚得够不够" |
| **经济模型** | 平均电价、峰谷价差、服务费 | "花得值不值" |

> ⚠️ **表头字段待数据完备后更新**：当前为初版设计，等所有数据清洗入库后，根据实际可用字段调整对比表结构。

### LLM 提升点发现模式（示例）

| 对比发现 | LLM 输出 |
|---------|---------|
| 用户利用率 3% vs 对标A 9% | "利用率有 3 倍提升空间" |
| 用户快充占比 90% vs 对标C 55% | "快充配比过高，参考对标C放慢充提升周转" |
| 用户高峰 14:00（电价高）vs 对标B 低谷 03:00 | "峰谷结构可优化，引导夜间充电降低成本" |
| 用户单桩日均 40度 vs 对标A 77度 | "单桩效率偏低，建议检查桩位布局或引流策略" |

---

## 八、产出清单

### 后端

| 文件 | 说明 |
|------|------|
| `backend/main.py` | FastAPI 入口 |
| `backend/config.py` | 配置管理 |
| `backend/requirements.txt` | 依赖 |
| `backend/api/diagnosis.py` | 诊断接口（extract / enrich / diagnose）|
| `backend/core/stub.py` | 算法 Stub（基于规则）|
| `backend/core/report.py` | 报告合并与格式化 |
| `backend/rag/indexer.py` | 场站数据向量化索引 |
| `backend/rag/retriever.py` | 相似场站检索 |

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
| `backend/core/stub.py` | 接入真实机器学习模型（课题组训练）|
| `backend/rag/` | 升级为混合检索（向量 + 关键词 + 重排序）|
| `backend/api/diagnose` | 接入 LangGraph 完整流程编排 |
| 前端页面 | 增加数据看板、历史记录、导出功能 |

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

## 报告输出 Prompt 规范（基于嘉老师需求）

### 分析目标

- 全年充电量与收益评估现状
- 潜在盈利提升空间及实现概率/比例分布
- 不同场景、不同手段下的提升空间分析
- **排除**：人员成本、运维成本等间接支出
- **聚焦**：场站运营直接回报（return）

### 报告三层结构

```
第一部分：现实评估
├── 当前运营绩效量化
├── 全年充电量估算
├── 全年收益评估
└── 关键指标一览（利用率、日均充电量、高峰时段等）

第二部分：潜力空间测算
├── 外部因素分析（周边场站布局、规模化车队、车辆停驶习惯）
├── 潜在引流特征识别
├── 不同手段的提升空间估算（附概率/比例）
└── 地理位置经济潜力评估

第三部分：提升路径建模
├── 路径A：成本优化
│   └── 参与电力现货市场 / 与运营商签订补充协议降低建设成本
└── 路径B：效率提升
    └── 引流机制设计 → 提升充电利用率 → 提升整体运营效率
```

### LLM Prompt 模板

```
你是一位充电场站运营效益分析专家。

【用户场站画像】
{station_profile}

【算法预测结果】
{algorithm_result}

【RAG 相似场站对标数据】
{rag_similar_stations}

【RAG 知识库分析】
{rag_analysis}

【输出要求】
请严格按照以下三层结构输出分析报告，使用 Markdown 格式：

## 第一部分：现实评估
1. 基于用户场站数据，估算全年充电量（度）和全年收益（元）
2. 列出关键运营指标：当前利用率、日均充电量、高峰时段
3. 与相似场站对比，定位当前运营水平（落后/平均/领先）

## 第二部分：潜力空间测算
1. 分析周边潜在需求：
   - 周边场站竞争格局（是否饱和）
   - 规模化车队行为（是否有固定大客户）
   - 车辆停驶习惯（夜间/午间充电潜力）
2. 给出不同提升手段的潜在空间：
   | 手段 | 提升空间 | 实现概率 | 测算依据 |
   |------|---------|---------|---------|
   | ...  | ...     | ...     | ...     |
3. 地理位置经济潜力评估

## 第三部分：提升路径建模
### 路径A：成本优化
- 是否适合参与电力现货市场？
- 是否与运营商有补充协议空间？
- 预计可降低多少建设/运营成本？

### 路径B：效率提升（引流机制）
- 峰谷电价优化建议
- 时段营销策略（午间套餐、夜间优惠等）
- 客群定位与精准引流
- 预计可提升多少利用率？

【约束】
- 不考虑人员成本、运维成本
- 聚焦直接回报（return）
- 所有数字需标注来源：[算法预测] / [知识库类比] / [行业规律推断]
- 初版允许基于描述性输入做合理推断
```

---

*版本: v1.2*  
*日期: 2026-04-24*  
*标注: 算法 Stub 版本，RAG 索引完成，前端待启动，Prompt 规范已定义*
