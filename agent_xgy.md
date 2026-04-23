# Agent: xgy (项目Owner / 数据工程负责人)

> 本文件由 AI agent 在每次工作会话后更新，记录工作内容、决策和状态。
> 每次 git commit 前必须更新此文件。
> git pull 后必须读取 team/ 目录下其他 agent 文件，了解同事进展。

---

## 项目概述

**ChargeMind** — 深圳充电场站诊断平台

> **算法硬数据 × LLM泛化直觉** — 为充电场站运营商打造的思维碰撞式诊断平台。

核心闭环：算法 Stub + RAG 知识库检索 → 交叉校验 → 输出带来源标注的诊断报告。

当前阶段：Phase 0 — 基础设施搭建（数据清洗阶段1已完成，待阶段2时序聚合）

---

## 项目目录结构

```
cwhdapp/
├── archive/              # 旧项目备份（Demo阶段暂时不动）
│   ├── assets/           # 旧资源文件
│   ├── core/             # 旧核心逻辑
│   ├── docs/             # 旧文档
│   ├── legacy-docs/      # 更旧的文档
│   └── ui/               # 旧UI代码
│
├── backend/              # FastAPI 后端（Python）
│   ├── api/              # REST API 路由 + Pydantic Schema（待开发）
│   ├── core/             # LangGraph 诊断引擎（待开发）
│   │   ├── graph/        # 流程图定义（待开发）
│   │   ├── prompts/      # Prompt 模板（待开发）
│   │   └── models/       # 外部模型封装（待开发）
│   ├── data/             # 数据层
│   │   ├── models/       # SQLAlchemy ORM 模型（待开发）
│   │   ├── repository/   # 数据访问层（待开发）
│   │   └── pipeline/     # ETL 清洗流水线 ✅ 阶段1已完成
│   │       ├── utils.py              # 工具函数（码表、电价解析、推断）
│   │       ├── clean_stations.py     # 静态数据清洗脚本
│   │       └── compute_metrics.py    # 时序聚合脚本（待开发）
│   ├── rag/              # RAG 知识库
│   │   └── indexers/     # 数据源索引器（待开发）
│   └── utils/            # 工具函数
│
├── frontend/             # React 前端（待初始化）
│   ├── public/           # 静态资源
│   └── src/              # 源码（空）
│
├── data/                 # 数据文件
│   ├── raw/              # 原始数据（gitignored）
│   ├── cleaned/          # 清洗后数据 ✅
│   │   ├── stations_static.jsonl      # 阶段1产出：10,942条场站静态画像
│   │   └── stations_static_summary.csv # 质量摘要
│   └── schema/           # 数据Schema定义 ✅
│       ├── DATA-PIPELINE-v1.md        # 数据清洗方案
│       └── VALIDATION-PROMPT.md       # 交叉校验Prompt
│
├── docs/                 # 项目文档
│   ├── IMPLEMENTATION-PLAN-v1.md      # 实施计划
│   ├── STORYTELLING-FRAMEWORK.md      # 叙事框架
│   └── context-gemini-memory.md       # Gemini上下文记忆
│
├── reference/            # 参考资料
│   └── chargemind_evaluation.agent.final/  # 评估相关
│
├── agent_xgy.md          # ← 本文件（我的工作日志）
├── .gitignore
├── README.md             # 项目介绍
└── pyproject.toml        # Python依赖管理
```

---

## 我的职责

- **数据工程负责人**：数据清洗、RAG知识库构建、数据质量保障
- **项目Owner**：整体架构设计、方案决策、进度把控
- **当前重点**：完成数据清洗阶段1→阶段2，准备后端和前端Demo

---

## 工作记录

### 2026-04-23 数据清洗阶段1完成

**完成内容：**
- ✅ 编写 `data/schema/DATA-PIPELINE-v1.md`（592行）— 完整数据清洗方案
- ✅ 编写 `data/schema/VALIDATION-PROMPT.md`（190行）— 交叉校验Prompt
- ✅ 编写 `backend/data/pipeline/utils.py` — 工具函数（码表映射、电价解析、区域/业态/充电桩推断）
- ✅ 编写 `backend/data/pipeline/clean_stations.py` — 静态数据清洗脚本
- ✅ 产出 `data/cleaned/stations_static.jsonl` — 10,942条场站静态画像

**数据源：**
- 表1.xlsx（13,456行）→ 去重后10,942行
- b2.csv（14,711行）— 电价/服务费/营业时间
- b4.csv（13,290行）— 功率段装机分布
- 场站网格/b1_with_grid_strict_polygon.csv — 场站-网格关联

**产出字段覆盖率：**
| 字段 | 覆盖率 |
|------|--------|
| 电价(electricity_fee_parsed) | 94.8% |
| 行政区(region) | 87.8% |
| 网格编号(grid_code) | 93.2% |
| 功率结构(total_power) | 96.5% |
| 业态标签(business_type) | 46.7% |
| 充电桩类型(charger_type) | 8.6% |
| 营业时间(busine_hours) | 99.99% |
| 有效坐标 | 99.0% |

**关键决策：**
- 表1去重策略：保留非空字段最多的行（已修复为稳定排序 mergesort）
- 电价解析：支持简单数字和时段字符串两种格式
- 区域推断：名称关键词 + 网格编码前缀双重映射
- 无网格匹配场站（7%）：用行政区均值填充（方案A）
- 业态推断：基于场站名称关键词（住宅区/办公区/商业区/工业区/交通枢纽/旅游景区）

**交叉校验后修复：**
- 修复去重策略稳定性（quicksort → mergesort）
- 修复busine_hours空值填充（填充"00:00~24:00"）
- 修复坐标范围校验（深圳边界：lng 113.7-114.8, lat 22.4-22.9）
- 修复"公园大地"误判为旅游景区（加住宅区优先匹配）
- 修正文档覆盖率预期（去重后真实值）

**Git 提交记录：**
- Commit: `40aeefc`
- 时间: 2026-04-23
- 变更: 21 files, +13,666 lines
- 内容: 数据清洗阶段1完成 + 团队协作文档

---

### 2026-04-23 第二轮交叉校验 + 回归修复

**校验AI发现的新问题（第一轮修复引入）：**
| 编号 | 问题 | 根因 | 修复 |
|------|------|------|------|
| REG-1 | "广场"关键词从办公区规则丢失 | 重写rules列表时手滑漏掉 | 恢复"广场"到办公区规则 |

**影响量化：**
- 修复前：business_type 覆盖率 43.5%（4,759条）
- 修复后：business_type 覆盖率 **46.6%**（5,104条）✅
- 含"广场"且有biz：从28条恢复到**373条**✅

**第二轮复检结论：**
- 4项修复全部通过 ✅
- 1项回归bug已修复 ✅

**Git 提交记录：**
- Commit: `34d989d`
- 时间: 2026-04-23
- 变更: 3 files, +357/-357 lines
- 内容: 恢复办公区"广场"关键词（回归修复）

### 2026-04-23 阶段2完成：时序聚合 + 区域均值填充

**完成内容：**
- ✅ 编写 `backend/data/pipeline/compute_metrics.py` — 时序聚合脚本
- ✅ 读取 `result_power_by_slot.csv`（233万行），按场站聚合计算指标
- ✅ 计算字段：`avg_daily_energy_kwh`、`avg_utilization`、`peak_hour`、`valley_hour`、`season_stats`
- ✅ 利用率异常截断：66个场站原始值>100%，截断至1.0
- ✅ 生成双版本输出：
  - `stations_raw.jsonl`（原始版，缺失标记为null）
  - `stations.jsonl`（Demo版，区域均值填充）
- ✅ 填充策略：region+biz_type → region_only → city_wide
- ✅ 更新 `DATA-PIPELINE-v1.md` 和 `VALIDATION-PROMPT.md`

**核心指标：**
| 指标 | 数值 |
|------|------|
| 总场站数 | 10,942 |
| 有真实时序数据 | 7,013（64.1%）|
| 区域均值填充 | 3,929（35.9%）|
| 区域+业态组合组数 | 103 |
| 区域-only组数 | 12 |

**Git 提交记录：**
- Commit: `a75c1c8`
- 时间: 2026-04-23
- 变更: 6 files, +22,361 lines
- 内容: 阶段2时序聚合 + 区域均值填充

**待办 / 阻塞：**
- [ ] 阶段3：质量评分和pipeline_report.json生成
- [ ] 初始化React前端项目
- [ ] 搭建FastAPI后端骨架

---

## 同事工作区

> 每次 `git pull` 后读取以下文件，了解同事进展。

| 同事 | Agent文件 | 负责领域 |
|------|----------|---------|
| （待补充） | `agent_xxx.md` | （待分配）|

---

## 团队约定

1. **每次工作会话结束 → 更新本文件**（AI辅助生成更新内容）
2. **每次 git commit 前 → 确认本文件已更新**
3. **每次 git pull 后 → 读取 team/ 下所有 agent_*.md**
4. **命名规范**：`agent_{姓名缩写}.md`，放在项目根目录
5. **内容规范**：项目概述 → 职责 → 工作记录（时间线）→ 待办/阻塞
6. **⚠️ Git commit 必须用中文** — 所有 commit message 使用中文编写，便于团队阅读和历史追溯
