# ChargeMind — 从Demo到完整产品实施计划

## 1. 项目愿景

构建一个**"算法预测 + RAG知识库双引擎"**的思维碰撞平台，面向充电场站运营商，解决"为什么收益不好、如何盈利"的核心痛点。

**核心差异化**：
- 不只是LLM生成报告，而是**算法硬数据**与**LLM泛化直觉**的交叉校验
- 每个建议都可追溯到来源（算法预测 / 知识库类比 / LLM推理）
- 可视化展示两股"力量"的博弈过程

---

## 2. 技术架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                   Web Frontend (React 18 + TS)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 场站录入     │  │ 诊断流程可视化│  │ 报告渲染 + 数据看板  │  │
│  │ (表单/NLP)   │  │ (LangGraph步骤│  │ (Markdown + ECharts)│  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │ WebSocket / HTTP
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              API Backend (FastAPI + Python 3.11+)           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              LangGraph 诊断流程编排                      │  │
│  │                                                         │  │
│  │   [extract] → [enrich] → [algorithm] → [rag] → [cross] │  │
│  │                ↓              ↓           ↓        ↓    │  │
│  │           数据库查询      预留接口    向量检索   碰撞校验  │  │
│  │                                                         │  │
│  │   [generate] → [format]                                  │  │
│  │       ↓                                                  │  │
│  │   流式报告输出                                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
   ┌─────────────┐  ┌─────────────────┐  ┌─────────────┐
   │  Data Layer │  │ Algorithm Stub  │  │   RAG Core  │
   │  SQLite/PG  │  │  (预留模型接口)   │  │  ChromaDB   │
   │  清洗后数据  │  │  当前: LLM代理   │  │  深圳全域知识 │
   └─────────────┘  └─────────────────┘  └─────────────┘
```

### 2.1 技术栈选型

| 层级 | 选型 | 理由 |
|------|------|------|
| 前端框架 | React 18 + TypeScript | 生态成熟，TypeScript保证可维护性 |
| UI组件库 | shadcn/ui + TailwindCSS | 好看、可定制、暗色主题支持好 |
| 图表可视化 | ECharts + recharts | 数据看板、对比图表 |
| 后端框架 | FastAPI | Python原生，与LangGraph/LangChain生态无缝 |
| 流程编排 | LangGraph | 节点化诊断流程，支持条件分支、人工审核、流式输出 |
| ORM | SQLAlchemy 2.0 | 异步支持，模型定义清晰 |
| 向量数据库 | ChromaDB | 轻量、本地优先、LangChain原生支持 |
| 数据清洗 | Pandas + pydantic | 字段校验 + 数据转换 |
| LLM接口 | OpenAI SDK (Kimi兼容) | 复用现有代码，切换成本低 |
| 桌面端(后续) | Tauri / PySide6+WebView | 复用Web前端，减少重复开发 |

---

## 3. 项目目录结构（目标态）

```
cwhdapp/
├── README.md                          # 项目说明
├── pyproject.toml                     # Python依赖管理
├── .env.example                       # 环境变量模板
│
├── frontend/                          # Web前端 (React)
│   ├── package.json
│   ├── src/
│   │   ├── main.tsx                   # 入口
│   │   ├── App.tsx                    # 根组件
│   │   ├── components/                # 通用组件
│   │   │   ├── StationInputForm.tsx   # 场站信息录入
│   │   │   ├── DiagnosisFlow.tsx      # 诊断流程可视化
│   │   │   ├── ReportViewer.tsx       # 报告渲染
│   │   │   ├── DataDashboard.tsx      # 数据看板
│   │   │   └── ConfidenceBadge.tsx    # 置信度标识
│   │   ├── pages/
│   │   │   └── HomePage.tsx           # 主页面
│   │   ├── hooks/
│   │   │   └── useDiagnosis.ts        # 诊断流程WebSocket Hook
│   │   ├── types/
│   │   │   └── diagnosis.ts           # 类型定义
│   │   └── lib/
│   │       └── api.ts                 # API客户端
│   └── public/
│
├── backend/                           # FastAPI后端
│   ├── main.py                        # 应用入口
│   ├── config.py                      # 配置管理
│   ├── pyproject.toml                 # 后端独立依赖
│   │
│   ├── api/                           # REST API层
│   │   ├── routes/
│   │   │   ├── diagnosis.py           # 诊断接口 (WebSocket流式)
│   │   │   ├── stations.py            # 场站CRUD
│   │   │   └── knowledge.py           # 知识库管理
│   │   └── schemas/
│   │       ├── station.py             # Pydantic模型
│   │       └── diagnosis.py           # 诊断相关Schema
│   │
│   ├── core/                          # 核心诊断引擎 (LangGraph)
│   │   ├── graph/                     # 流程图定义
│   │   │   ├── __init__.py
│   │   │   ├── state.py               # DiagnosisState定义
│   │   │   ├── builder.py             # 图构建器
│   │   │   └── nodes/                 # 节点实现
│   │   │       ├── extract.py         # 参数提取
│   │   │       ├── enrich.py          # 数据增强
│   │   │       ├── algorithm_stub.py  # 算法预留接口
│   │   │       ├── retrieve_rag.py    # RAG检索
│   │   │       ├── analyze_rag.py     # RAG洞察分析
│   │   │       ├── cross_validate.py  # 交叉校验
│   │   │       └── generate_report.py # 报告生成
│   │   ├── prompts/                   # Prompt模板
│   │   │   ├── extract.txt
│   │   │   ├── rag_analyze.txt
│   │   │   └── report.txt
│   │   └── models/                    # 外部模型封装
│   │       └── kimi_client.py         # Kimi API封装 (复用现有)
│   │
│   ├── data/                          # 数据层
│   │   ├── models/                    # SQLAlchemy模型
│   │   │   ├── station.py             # 场站表
│   │   │   ├── station_metrics.py     # 场站指标表
│   │   │   └── region_stats.py        # 区域统计表
│   │   ├── repository/                # 数据访问层
│   │   │   └── station_repo.py
│   │   └── pipeline/                  # ETL流水线
│   │       ├── clean.py               # 清洗逻辑
│   │       ├── validate.py            # 校验逻辑
│   │       └── ingest.py              # 入库逻辑
│   │
│   ├── rag/                           # RAG知识库
│   │   ├── embeddings.py              # 嵌入模型
│   │   ├── vector_store.py            # ChromaDB封装
│   │   ├── chunker.py                 # 文档切分
│   │   └── indexers/                  # 不同数据源索引器
│   │       ├── station_indexer.py     # 场站数据索引
│   │       └── policy_indexer.py      # 政策/电价索引
│   │
│   └── utils/                         # 工具函数
│       └── json_safe.py               # JSON安全解析 (复用现有)
│
├── data/                              # 原始数据与清洗数据
│   ├── raw/                           # 原始深圳场站数据 (gitignored)
│   ├── cleaned/                       # 清洗后数据
│   └── schema/                        # 数据Schema定义
│       └── station_schema.yaml
│
├── docs/                              # 项目文档 (已规范命名)
│   ├── prd-v0.2.md                    # 产品需求
│   ├── spec-demo-v1.md                # 技术规格
│   ├── design-ui-v0.1.md              # UI设计
│   ├── guide-roadmap.md               # 迭代手册
│   ├── constraint-output.md           # 输出约束
│   ├── context-claude.md              # Claude上下文
│   └── context-gemini-prompt.md       # Gemini提示词
│
└── desktop/                           # 桌面端 (Phase 5)
    └── (后续从Web端复用)
```

---

## 4. LangGraph 双引擎流程设计

### 4.1 State定义

```python
class DiagnosisState(TypedDict):
    # ====== 输入层 ======
    user_input: str                          # 用户原始输入
    station_id: Optional[str]               # 已知场站ID
    
    # ====== 数据层 ======
    raw_params: dict                         # LLM提取参数
    station_record: Optional[dict]          # 数据库场站记录
    region_benchmarks: Optional[dict]       # 区域基准数据
    
    # ====== 引擎层 ======
    algorithm_result: Optional[dict]        # 算法预测结果
    algorithm_confidence: float             # 算法置信度 (0-1)
    
    rag_chunks: List[dict]                  # RAG原始检索块
    rag_analysis: Optional[dict]           # RAG洞察分析
    rag_relevance: float                    # RAG相关度 (0-1)
    
    # ====== 碰撞层 ======
    cross_validation: Optional[dict]       # 交叉校验结果
    conflicts: List[dict]                   # 冲突点列表
    consensus: List[dict]                   # 共识点列表
    engine_weights: dict                    # 引擎权重 {algorithm: 0.6, rag: 0.4}
    
    # ====== 输出层 ======
    report_sections: List[dict]            # 报告分节
    final_report: str                       # 最终报告Markdown
    executive_summary: str                  # 执行摘要
    
    # ====== 元数据 ======
    current_step: str                       # 当前步骤ID (用于前端进度)
    step_history: List[str]                # 步骤历史
    error: Optional[str]                   # 错误信息
    processing_time_ms: int                # 总处理时间
```

### 4.2 节点与边

```
                    ┌─────────────────┐
         ┌─────────→│   START         │
         │          └────────┬────────┘
         │                   │
         │          ┌────────▼────────┐
         │          │  extract_params │ ← LLM提取结构化参数
         │          │  (参数提取节点)  │
         │          └────────┬────────┘
         │                   │
         │          ┌────────▼────────┐
         │          │   enrich_data   │ ← 查数据库补全信息
         │          │  (数据增强节点)  │
         │          └────────┬────────┘
         │                   │
         │      ┌────────────┴────────────┐
         │      │                         │
         │      ▼                         ▼
         │ ┌────────────┐          ┌────────────┐
         │ │run_algorithm│          │retrieve_rag│ ← 并行执行
         │ │(算法预留接口)│          │(向量检索)   │
         │ └─────┬──────┘          └─────┬──────┘
         │       │                       │
         │       │          ┌────────────▼────────┐
         │       │          │   analyze_rag       │ ← LLM分析RAG结果
         │       │          │   (RAG洞察生成)      │
         │       │          └────────────┬────────┘
         │       │                       │
         │       └───────────┬───────────┘
         │                   │
         │          ┌────────▼────────┐
         │          │ cross_validate  │ ← 核心: 算法vs RAG碰撞
         │          │ (交叉校验节点)   │
         │          └────────┬────────┘
         │                   │
         │      ┌────────────┼────────────┐
         │      │            │            │
         │      ▼            ▼            ▼
         │  [高冲突]     [中冲突]      [低冲突]
         │      │            │            │
         │      │    ┌───────┘            │
         │      │    │                    │
         │      ▼    ▼                    ▼
         │ ┌────────────┐      ┌─────────────────┐
         │ │ human_review│      │ generate_report │ ← LLM综合生成
         │ │ (人工审核)  │      │ (报告生成节点)   │
         │ └─────┬──────┘      └────────┬────────┘
         │       │                      │
         │       └──────────┬───────────┘
         │                  │
         │         ┌────────▼────────┐
         │         │  format_output  │ ← 格式化最终输出
         │         │  (格式化节点)    │
         │         └────────┬────────┘
         │                  │
         │                  ▼
         │         ┌─────────────────┐
         └─────────│      END        │
                   └─────────────────┘
```

### 4.3 条件边逻辑

| 条件 | 行为 |
|------|------|
| `algorithm_confidence < 0.3` | 算法权重降为0.1，主要依赖RAG+LLM |
| `rag_relevance < 0.3` | RAG权重降为0.1，主要依赖算法+LLM |
| 冲突数量 > 3 | 进入 human_review 节点 (Phase 2) |
| 单条冲突利润差异 > 50% | 在报告中标注"需人工复核" |

---

## 5. 数据模型设计

### 5.1 场站主表 (stations)

```python
class Station(Base):
    __tablename__ = "stations"
    
    id: Mapped[str] = mapped_column(primary_key=True)  # 唯一标识
    name: Mapped[str]
    city: Mapped[str]          # 城市
    district: Mapped[str]      # 区县
    address: Mapped[str]
    
    # 物理参数
    pile_count: Mapped[int]
    pile_power_kw: Mapped[float]
    parking_count: Mapped[Optional[int]]
    
    # 经营参数
    daily_kwh: Mapped[float]           # 日均充电量
    price_peak: Mapped[float]          # 峰段电价
    price_flat: Mapped[float]          # 平段电价
    price_valley: Mapped[float]        # 谷段电价
    service_fee: Mapped[float]         # 服务费
    monthly_rent: Mapped[float]        # 月租金
    staff_count: Mapped[int]           # 运维人数
    
    # 市场参数
    competitor_count: Mapped[Optional[int]]
    customer_type: Mapped[Optional[str]]
    
    # 元数据
    data_source: Mapped[str]           # 数据来源
    data_quality_score: Mapped[float]  # 数据质量评分
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### 5.2 场站指标表 (station_metrics)

```python
class StationMetrics(Base):
    __tablename__ = "station_metrics"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id"))
    
    # 收益指标
    annual_revenue: Mapped[float]
    annual_cost: Mapped[float]
    annual_profit: Mapped[float]
    profit_margin: Mapped[float]       # 利润率
    
    # 效率指标
    utilization_rate: Mapped[float]    # 利用率
    avg_session_duration: Mapped[float] # 平均充电时长
    peak_flat_valley_ratio: Mapped[str] # 峰平谷占比 JSON
    
    # 计算时间
    calculated_at: Mapped[datetime]
```

### 5.3 区域统计表 (region_stats)

```python
class RegionStats(Base):
    __tablename__ = "region_stats"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city: Mapped[str]
    district: Mapped[str]
    
    # 区域基准
    avg_daily_kwh_per_pile: Mapped[float]  # 单桩日均充电量
    avg_service_fee: Mapped[float]
    avg_utilization: Mapped[float]
    station_density: Mapped[float]         # 场站密度(个/km²)
    
    # 统计周期
    period_start: Mapped[date]
    period_end: Mapped[date]
```

---

## 6. 前端关键界面设计

### 6.1 诊断流程可视化 (DiagnosisFlow)

参考LangGraph步骤，用垂直时间线展示：

```
┌────────────────────────────────────────┐
│  ⚡ 诊断流程                            │
│                                        │
│  ● 参数提取      ──────  ✅ 完成 (1.2s) │
│  │                                     │
│  ● 数据增强      ──────  ✅ 完成 (0.3s) │
│  │                                     │
│  ├─● 算法预测    ──────  ⚠️ 低置信度    │
│  │  └─ 年利润预测: -12.3万 (置信度28%)   │
│  │                                     │
│  ├─● RAG检索     ──────  ✅ 完成        │
│  │  └─ 找到3个相似场站 (相关度0.82)      │
│  │                                     │
│  ● 交叉校验      ──────  🔍 发现2处冲突 │
│  │  ├─ 算法: 建议减员1人 (+3.6万)       │
│  │  └─ RAG:  南山区域普遍4人 (+0万)     │
│  │     → 冲突! 已调和: 建议维持4人      │
│  │                                     │
│  ● 报告生成      ──────  ⏳ 流式输出中...│
│                                        │
└────────────────────────────────────────┘
```

### 6.2 双引擎对比面板

```
┌──────────────────────┬──────────────────────┐
│   🔧 算法引擎         │   🧠 RAG知识库        │
├──────────────────────┼──────────────────────┤
│ 预测年利润: -12.3万   │ 类比场站平均: -8.5万  │
│ 置信度: 28% ⚠️       │ 相关度: 82% ✅       │
│                      │                      │
│ 核心建议:            │ 区域洞察:            │
│ 1. 峰谷结构优化      │ 1. 南山科技园区竞争   │
│ 2. 夜间引流调价      │    激烈，需差异化     │
│ 3. 运维排班优化      │ 2. 周边企业通勤需求   │
│                      │    未被充分挖掘       │
└──────────────────────┴──────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│  🤝 思维碰撞结果                              │
│  权重分配: 算法30% + RAG70%                   │
│  调和冲突2处，共识3处                         │
└─────────────────────────────────────────────┘
```

---

## 7. 分阶段实施计划 (TODO)

### Phase 0: 项目基础设施 ✅ 前置

**目标**: 搭建完整的项目骨架，确定技术规范

| # | 任务 | 预估工时 | 产出物 |
|---|------|---------|--------|
| 0.1 | 创建 backend/ 目录结构，配置 FastAPI 项目 | 2h | `backend/main.py`, `pyproject.toml` |
| 0.2 | 创建 frontend/ 目录结构，配置 React + TS + Tailwind + shadcn | 2h | `frontend/package.json`, 基础配置 |
| 0.3 | 配置环境变量管理 (.env) | 0.5h | `.env.example`, `config.py` |
| 0.4 | 搭建前后端联调基础 (CORS, API客户端) | 1h | 可互通的Hello World |
| 0.5 | 编写 API Schema (Pydantic) | 2h | `api/schemas/*.py` |
| 0.6 | 更新根目录 README，说明新项目结构 | 1h | `README.md` |

**Phase 0 验收标准**: `cd backend && uvicorn main:app --reload` 和 `cd frontend && npm run dev` 同时运行，前端能调用后端API。

---

### Phase 1: 数据工程 🎯 当前优先

**目标**: 清洗深圳全域场站数据，建立可查询的数据层

| # | 任务 | 预估工时 | 产出物 |
|---|------|---------|--------|
| 1.1 | 定义数据Schema (YAML + SQLAlchemy模型) | 3h | `data/schema/station_schema.yaml`, `data/models/*.py` |
| 1.2 | 编写数据清洗Pipeline (Pandas) | 6h | `data/pipeline/clean.py`, `validate.py` |
| 1.3 | 编写数据入库Pipeline | 3h | `data/pipeline/ingest.py` |
| 1.4 | 清洗深圳场站数据并入库 | 4h | SQLite数据库文件 |
| 1.5 | 计算区域统计基准 (聚合分析) | 3h | `region_stats` 表数据 |
| 1.6 | 数据质量报告生成 | 2h | 清洗日志 + 质量评分 |
| 1.7 | 编写数据访问层 (Repository模式) | 3h | `data/repository/station_repo.py` |

**Phase 1 验收标准**: 
- 运行 `python -m data.pipeline.ingest --source raw/shenzhen_stations.csv` 成功入库
- SQLite中 stations 表有 >100 条记录
- 可查询任意场站的完整信息和区域基准对比

---

### Phase 2: 核心诊断引擎 (LangGraph)

**目标**: 实现双引擎诊断流程

| # | 任务 | 预估工时 | 产出物 |
|---|------|---------|--------|
| 2.1 | 定义 DiagnosisState 和类型 | 2h | `core/graph/state.py` |
| 2.2 | 实现 extract_params 节点 | 3h | `core/graph/nodes/extract.py` |
| 2.3 | 实现 enrich_data 节点 | 3h | `core/graph/nodes/enrich.py` |
| 2.4 | 实现 algorithm_stub 节点 (预留接口) | 2h | `core/graph/nodes/algorithm_stub.py` |
| 2.5 | 实现 retrieve_rag 节点 | 4h | `core/graph/nodes/retrieve_rag.py` |
| 2.6 | 实现 analyze_rag 节点 | 3h | `core/graph/nodes/analyze_rag.py` |
| 2.7 | 实现 cross_validate 节点 | 4h | `core/graph/nodes/cross_validate.py` |
| 2.8 | 实现 generate_report 节点 | 4h | `core/graph/nodes/generate_report.py` |
| 2.9 | 构建LangGraph流程图 + 条件边 | 3h | `core/graph/builder.py` |
| 2.10 | Prompt模板抽离与管理 | 2h | `core/prompts/*.txt` |
| 2.11 | 流式输出支持 (WebSocket) | 4h | `api/routes/diagnosis.py` |

**Phase 2 验收标准**:
- 运行完整流程: `curl -X POST /api/diagnosis` 返回完整诊断结果
- WebSocket `/ws/diagnosis` 实时推送每个步骤的进度
- 算法stub节点返回mock数据，结构完整

---

### Phase 3: RAG知识库

**目标**: 构建深圳全域场站知识库

| # | 任务 | 预估工时 | 产出物 |
|---|------|---------|--------|
| 3.1 | 选择/配置嵌入模型 (BAAI/bge-large-zh) | 2h | `rag/embeddings.py` |
| 3.2 | 搭建 ChromaDB 向量存储 | 2h | `rag/vector_store.py` |
| 3.3 | 实现场站数据索引器 (结构化数据→文档) | 4h | `rag/indexers/station_indexer.py` |
| 3.4 | 实现政策/电价索引器 | 2h | `rag/indexers/policy_indexer.py` |
| 3.5 | 批量索引深圳场站数据 | 2h | ChromaDB集合数据 |
| 3.6 | 检索策略优化 (混合检索: 向量+关键词) | 3h | 高相关度检索 |
| 3.7 | RAG结果可解释性 (展示来源场站) | 2h | 带来源标注的chunks |

**Phase 3 验收标准**:
- 输入场站参数，RAG返回3-5个相似场站，相关度>0.7
- 每个chunk带来源场站名称和关键指标
- 检索时间 < 500ms

---

### Phase 4: Web前端

**目标**: 构建好看、可交互的Web界面

| # | 任务 | 预估工时 | 产出物 |
|---|------|---------|--------|
| 4.1 | 搭建页面框架 (Layout + 路由) | 2h | `App.tsx`, 导航 |
| 4.2 | 场站信息录入表单 | 4h | `StationInputForm.tsx` |
| 4.3 | 诊断流程可视化组件 | 6h | `DiagnosisFlow.tsx` |
| 4.4 | 双引擎对比面板 | 4h | 算法 vs RAG 展示 |
| 4.5 | 报告渲染组件 (Markdown + 高亮) | 4h | `ReportViewer.tsx` |
| 4.6 | 数据看板 (ECharts图表) | 6h | 利润对比、趋势图 |
| 4.7 | WebSocket连接管理 Hook | 3h | `useDiagnosis.ts` |
| 4.8 | 响应式布局 + 暗色主题 | 4h | 移动端适配 |
| 4.9 | 加载状态与错误处理 | 2h | Skeleton + Error Boundary |

**Phase 4 验收标准**:
- 用户在表单输入场站信息，点击诊断，看到流程可视化
- 实时看到每个步骤的进度和结果
- 最终报告美观、可阅读、可导出
- 暗色主题下无视觉问题

---

### Phase 5: 桌面端

**目标**: 复用Web前端，打包为桌面应用

| # | 任务 | 预估工时 | 产出物 |
|---|------|---------|--------|
| 5.1 | 调研桌面端方案 (Tauri vs Electron vs PySide6+WebView) | 2h | 选型文档 |
| 5.2 | 集成桌面端壳 | 4h | 可运行的桌面应用 |
| 5.3 | 本地数据存储适配 | 2h | SQLite本地路径处理 |
| 5.4 | 打包与签名 | 2h | 安装包 |

---

### Phase 6: 算法模型接入

**目标**: 将算法stub替换为真实预测模型

| # | 任务 | 预估工时 | 产出物 |
|---|------|---------|--------|
| 6.1 | 特征工程接口设计 | 3h | `algorithm/features.py` |
| 6.2 | 模型训练管线 (sklearn/xgboost) | 8h | `algorithm/train.py` |
| 6.3 | 模型推理服务封装 | 4h | `algorithm/inference.py` |
| 6.4 | 模型效果评估与校准 | 4h | 评估报告 |
| 6.5 | 替换 algorithm_stub 节点 | 2h | 真实模型接入 |
| 6.6 | A/B测试框架 (算法 vs 规则) | 3h | 效果对比 |

---

## 8. 关键设计决策记录 (ADR)

### ADR-001: 为什么先Web后桌面？

- **上下文**: 用户要求"好看"
- **决策**: 先用React+Tailwind构建Web前端，桌面端后续用Tauri或WebView封装
- **理由**: Web技术栈在UI表现力、组件生态、图表库方面远胜PySide6
- **代价**: 需要维护两套运行时（浏览器+后端服务）

### ADR-002: 为什么用LangGraph？

- **上下文**: 需要多步骤、条件分支、流式输出的诊断流程
- **决策**: 使用LangGraph编排
- **理由**: 
  - 节点化设计天然匹配"双引擎碰撞"的抽象
  - 支持条件边（高冲突→人工审核）
  - 内置状态管理，前端可实时订阅
  - 与LangChain生态无缝，RAG组件即插即用
- **代价**: 引入依赖，团队需学习LangGraph概念

### ADR-003: 为什么算法先Stub？

- **上下文**: 当前没有训练好的预测模型
- **决策**: 预留algorithm_stub接口，先用LLM+规则代理
- **理由**: 
  - 不阻塞产品其他功能的开发
  - 可并行进行模型训练（Phase 6）
  - 接口稳定后，替换实现即可
- **Stub行为**: 返回基于规则的预测 + 低置信度标记，触发RAG高权重补偿

---

## 9. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 深圳数据质量差 | 高 | 高 | Phase 1预留足够时间；建立数据质量评分体系 |
| LangGraph学习曲线 | 中 | 中 | 先实现核心3个节点，再扩展 |
| RAG检索效果差 | 中 | 高 | 混合检索策略；人工调优embedding |
| 前端开发进度慢 | 中 | 中 | 使用shadcn/ui减少自定义组件；MVP先核心流程 |
| LLM API成本/稳定性 | 中 | 高 | 流式输出减少重试；本地缓存相似查询 |

---

## 10. 下一步行动

用户确认本计划后，按以下顺序执行：

1. **立即**: 创建 `backend/` 和 `frontend/` 目录结构 (Phase 0)
2. **本周**: 完成数据Schema定义和清洗Pipeline (Phase 1 开始)
3. **下周**: 接入第一批清洗后的深圳数据，验证数据层
4. **并行**: 搭建LangGraph骨架，实现 extract + enrich 节点 (Phase 2 开始)

---

*计划版本: v1.0*  
*制定时间: 2026-04-21*  
*下次评审: Phase 1 完成后*
