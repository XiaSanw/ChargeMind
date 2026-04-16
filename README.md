# AI驱动充电桩智能诊断平台 (Demo)

本项目是一个基于 PyQt6 (PySide6) 构建的充电桩智能诊断平台演示应用。它结合了预设的诊断规则引擎和外部 LLM 能力，为充电桩场站提供模拟的经营分析和优化建议。

## 目录结构说明

- `main.py`: 应用程序的主入口文件，用于启动整个 GUI 应用。
- `constants.py`: 存放项目中的全局常量和基础配置参数。
- `requirements.txt`: Python 环境依赖清单。
- `core/`: **核心业务逻辑层**
  - `diagnosis.py`: 场站诊断引擎的伪算法层，基于规则进行测算。
  - `kimi_api.py`: 负责与外部大语言模型 (Kimi 等 API) 交互的模块。
  - `worker.py`: 处理耗时后台任务的工作线程模块，防止界面卡顿。
- `ui/`: **用户界面层 (PySide6)**
  - `main_window.py`: 定义主窗口布局、组件逻辑及用户交互。
  - `styles.py`: 集中管理界面的 QSS 样式表，控制视觉外观。
- `docs/`: **项目文档与需求库** (由原根目录 Markdown 整理入此文件夹)
  - `PRD-v0.1.md`, `PRD-v0.2.md`: 产品的各个版本的需求文档，记录了从构想到落地的收敛过程。
  - `DEMO-SPEC-v1.md`: 针对当前 Demo 演示版的详细技术与功能规格说明。
  - `ui设计.md`: 关于产品 UI 界面交互与展示设计的详细描述。
  - `迭代手册.md`: 项目的迭代规划和开发记录。
  - `输出诊断约束.md`: 规范诊断引擎和 LLM 报告输出格式、逻辑的约束条件。
  - `CLAUDE.md`, `GEMINI-PROMPT.md`, `geminimemory.md`: 给 AI 的提示词 (Prompt)、记忆上下文或开发规范说明文件。
- `assets/`: **静态资源目录** (存放图片等)
  - 存放项目相关的截图、展示图片或 UI 素材。

## 运行方式

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行主程序：
```bash
python main.py
```