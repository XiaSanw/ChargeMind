# 充电桩智能诊断 Demo 项目

## 项目定位

为充电桩运营商提供一个 AI 咨询工具的演示版本。用户输入场站描述，系统提取参数、运行诊断算法、生成降本增效报告。当前阶段是 demo，算法用规则+公式替代，后续可替换为真实模型。

## 核心架构

三步串行 pipeline：

```
固定输入文本 → [Kimi API] 提取结构化参数 → [本地Python] 黑箱算法计算 → [Kimi API 流式] 生成报告
```

- LLM：Kimi（Moonshot AI），OpenAI 兼容接口，`base_url="https://api.moonshot.cn/v1"`，模型 `moonshot-v1-8k`
- 桌面框架：PySide6，左右分栏布局（40%/60%）
- 打包目标：PyInstaller 打包为 Windows EXE（`pyinstaller --onefile --windowed main.py`）

## 文件清单与角色

| 文件 | 状态 | 用途 |
|------|------|------|
| `context-gemini-prompt.md` | **给 Gemini 的开发指令** | 包含完整代码规格，已经过 review 和 bug 修复，可直接使用 |
| `spec-demo-v1.md` | 设计基准 | 首版 demo 精简落地规格书（prompt、算法、界面） |
| `prd-v0.1-deprecated.md` | **已废弃** | 不要参考 |
| `prd-v0.2.md` | 远期参考 | 详尽字段表和场景模板，留作后续迭代 |
| `design-ui-v0.1.md` | **已过时** | 已被 context-gemini-prompt 中的界面规格取代 |
| `*.png` | 参考 | 项目总览图，对外 pitch 用 |

## 关键决策记录

1. **首版 scope 极简**：固定输入、不支持用户自由编辑参数、不支持多场景模板、不做离线模式
2. **两次 LLM 调用**：第一次非流式提取参数（temperature=0.1），第二次流式生成报告（temperature=0.7）
3. **黑箱算法**：纯四则运算，假设峰平谷占比 40/35/25，优化后 25/35/40，充电量提升 15%，排班减 0.5 人。三条动作的 profit_delta 按比例缩放确保加总 = profit_improvement
4. **界面布局**：左右分栏，用 QHBoxLayout + stretch 固定比例，不用 QSplitter
5. **API Key 管理**：菜单栏入口输入，保存到 config.json 持久化，启动时自动读取
6. **JSON 解析容错**：先尝试直接解析，失败后用正则 `re.search(r'\{.*\}', raw, re.DOTALL)` 提取再解析
7. **null 值防护**：diagnose() 中所有参数用 `.get() or 默认值` 兜底
8. **UI 不卡顿**：所有 Kimi 调用在 QThread 中执行，通过 Signal 通知主线程更新

## context-gemini-prompt.md 已修复的 bug

Gemini 在编辑 context-gemini-prompt.md 时引入了几个问题，已由 Claude 修复：
- `__init__` 中 `_setup_ui()` 和 `_build_ui()` 重复调用 → 合并为 `_build_ui()`
- `_build_menu()` 被调用两次 → 改为一次
- `self._report_text = ""` 初始化丢失 → 补回
- `import json` / `import re` 在函数内重复 → 移到文件顶部

## 代码结构（Gemini 生成中）

```
cwhdapp/
├── main.py              # 入口：python main.py 启动
├── constants.py         # DEMO_INPUT 演示文本、FIELD_LABELS 字段中文映射
├── config.json          # 运行时生成，存 API Key
├── core/
│   ├── kimi_api.py      # set_api_key() / extract_params() / generate_report_stream()
│   ├── diagnosis.py     # diagnose() 黑箱算法
│   └── worker.py        # DiagnosisWorker(QThread)，信号: step_changed/params_extracted/diagnosis_ready/report_token/finished_all/error_occurred
├── ui/
│   ├── main_window.py   # MainWindow 左右分栏，4 区域(输入/参数/诊断/报告)
│   └── styles.py        # QSS 样式（浅色科技蓝白）
└── requirements.txt     # PySide6>=6.5, openai>=1.0
```

## 运行方式

```bash
pip install -r requirements.txt
python main.py
# 首次运行后在菜单「设置」→「配置 API Key」填入 Kimi API Key
```

打包为 EXE：
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
# 产物在 dist/main.exe
```

## 当前进度

- [x] 需求梳理（prd-v0.1-deprecated → prd-v0.2 → spec-demo-v1 收敛）
- [x] 提取 Prompt 设计完成
- [x] 黑箱算法逻辑设计完成（含数字自洽校验）
- [x] 报告生成 Prompt 设计完成
- [x] 界面布局规格完成（左右分栏 + 4 区域 + 状态流转）
- [x] Gemini 开发指令编写完成（context-gemini-prompt.md）
- [x] context-gemini-prompt.md review + bug 修复（null防护/JSON容错/API Key持久化/重复调用修复）
- [ ] Gemini 生成代码
- [ ] 代码调试与 Kimi API 联调
- [ ] PyInstaller 打包为 EXE
