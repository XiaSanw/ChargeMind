# ⚡ ChargeMind

> **算法硬数据 × LLM泛化直觉** — 为充电场站运营商打造的思维碰撞式诊断平台。

---

## 项目愿景

充电场站运营商面临的核心困境：**"我知道建站在这里，但不知道为什么收益不好，更不知道怎么才能盈利。"**

ChargeMind 不做"黑箱式的一键出报告"。我们相信，真正有价值的诊断来自**两股力量的交叉校验**：

- **🔧 算法引擎** — 基于深圳全域场站数据训练的预测模型，给出量化的收益预测与优化参数
- **🧠 RAG 知识库** — 将深圳全域场站信息向量化存储，让 LLM 从相似案例中泛化出算法写死了参数和权重的盲区

两股力量在 **交叉校验节点** 中碰撞：冲突点被标注、共识点被强化，最终输出一份**每句话都可追溯来源**的优化建议报告。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **双引擎诊断** | 算法预测 + RAG 知识检索并行执行，非单一路径 |
| **思维碰撞可视化** | 前端实时展示算法与 RAG 的冲突与调和过程 |
| **来源可追溯** | 每条建议标注来源：`[算法预测]` / `[知识库类比]` / `[LLM推理]` |
| **置信度系统** | 算法置信度 × RAG 相关度 → 综合建议权重 |
| **流式报告生成** | WebSocket 实时推送诊断进度与报告内容 |
| **好看** | 暗色主题、数据可视化、专业级 UI |

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Web Frontend (React 18 + TS)              │
│              场站录入 → 流程可视化 → 报告渲染                    │
└─────────────────────────────────────────────────────────────┘
                              │ WebSocket / HTTP
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              API Backend (FastAPI + Python 3.11+)           │
│                   LangGraph 诊断流程编排                      │
│                                                             │
│   [extract] → [enrich] → [algorithm] → [rag] → [cross]     │
│                ↓              ↓           ↓        ↓        │
│           数据库查询      预留接口    向量检索   碰撞校验      │
│                                                             │
│   [generate] → [format]                                      │
│       ↓                                                      │
│   流式报告输出                                                │
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

### 技术栈

| 层级 | 选型 |
|------|------|
| 前端 | React 18 + TypeScript + TailwindCSS + shadcn/ui + ECharts |
| 后端 | FastAPI + LangGraph + SQLAlchemy 2.0 |
| 向量库 | ChromaDB |
| 数据清洗 | Pandas + Pydantic |
| LLM | Kimi (OpenAI 兼容接口) |
| 桌面端 | Tauri / PySide6 + WebView (Phase 5) |

---

## 项目结构

```
cwhdapp/
├── archive/                  # 旧项目备份 (Demo 阶段)
│
├── backend/                  # FastAPI 后端
│   ├── api/                  # REST API 路由 + Pydantic Schema
│   ├── core/                 # LangGraph 诊断引擎
│   │   ├── graph/            # 流程图定义 (State + Builder + Nodes)
│   │   ├── prompts/          # Prompt 模板
│   │   └── models/           # 外部模型封装 (Kimi)
│   ├── data/                 # 数据层
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── repository/       # 数据访问层
│   │   └── pipeline/         # ETL 清洗流水线
│   ├── rag/                  # RAG 知识库
│   │   └── indexers/         # 数据源索引器
│   └── utils/                # 工具函数
│
├── frontend/                 # React 前端
│   └── src/
│       ├── components/       # UI 组件
│       ├── pages/            # 页面
│       ├── hooks/            # 自定义 Hooks
│       ├── types/            # TypeScript 类型
│       └── lib/              # API 客户端 + 工具
│
├── data/                     # 数据文件 (raw/ 目录 gitignored)
│   ├── raw/                  # 原始场站数据
│   ├── cleaned/              # 清洗后数据
│   └── schema/               # 数据 Schema 定义
│
├── docs/                     # 项目文档
├── .env.example              # 环境变量模板
├── pyproject.toml            # Python 依赖管理
└── README.md                 # 本文件
```

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- (可选) uv / pip

### 1. 克隆与配置

```bash
git clone <repo-url>
cd cwhdapp

# 复制环境变量模板
cp .env.example .env
# 编辑 .env，填入 Kimi API Key 等配置
```

### 2. 启动后端

```bash
cd backend

# 安装依赖 (推荐用 uv)
uv pip install -e .

# 启动服务
uvicorn main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问

打开浏览器访问 `http://localhost:5173`

---

## 数据准备

### 清洗深圳场站数据

```bash
cd backend

# 将原始数据放入 data/raw/
# 执行清洗流水线
python -m data.pipeline.ingest --source ../data/raw/shenzhen_stations.csv

# 验证入库
python -m data.pipeline.verify
```

### 构建 RAG 知识库

```bash
# 索引场站数据到 ChromaDB
python -m rag.indexers.station_indexer --source ../data/cleaned/stations.csv

# 验证检索
python -m rag.verify --query "南山区日均充电量5000度的快充站"
```

---

## 开发指南

### 添加新的诊断节点

1. 在 `backend/core/graph/nodes/` 下创建节点文件
2. 实现 `def node_name(state: DiagnosisState) -> DiagnosisState:` 函数
3. 在 `backend/core/graph/builder.py` 中注册节点与边
4. 更新 `DiagnosisState` 类型定义（如需新增字段）

### 修改 Prompt 模板

Prompt 文件统一放在 `backend/core/prompts/` 目录下，以 `.txt` 结尾，支持 Jinja2 语法变量替换。

### 前端组件规范

- 所有组件使用 TypeScript，定义 Props 接口
- UI 组件优先使用 shadcn/ui，自定义样式用 TailwindCSS
- 数据可视化统一用 ECharts

---

## 实施路线图

| 阶段 | 目标 | 状态 |
|------|------|------|
| **Phase 0** | 项目基础设施：目录结构、前后端骨架、联调 | 🚧 进行中 |
| **Phase 1** | 数据工程：清洗深圳场站数据、Schema、入库 | ⏳ 待开始 |
| **Phase 2** | 核心引擎：LangGraph 双引擎流程、流式输出 | ⏳ 待开始 |
| **Phase 3** | RAG 知识库：ChromaDB、索引、检索优化 | ⏳ 待开始 |
| **Phase 4** | Web 前端：React 界面、可视化、暗色主题 | ⏳ 待开始 |
| **Phase 5** | 桌面端：Tauri / PySide6 封装 | ⏳ 待开始 |
| **Phase 6** | 算法模型：特征工程、训练、替换 Stub | ⏳ 待开始 |

---

## 设计决策 (ADR)

- **ADR-001**: 先 Web 后桌面 — React 生态在 UI 表现力上远胜 PySide6
- **ADR-002**: 使用 LangGraph — 节点化设计天然匹配"双引擎碰撞"抽象
- **ADR-003**: 算法先 Stub — 不阻塞产品开发，模型训练与工程并行推进

---

## 贡献者

- 课题组：电网调度 / 车网互动重点项目
- 数据支持：深圳全域充电场站数据

---

*项目启动日期: 2026-04-21*  
*当前阶段: Phase 0 — 基础设施搭建*
