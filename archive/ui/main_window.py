import os
import json
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGridLayout, QTextEdit, QPushButton, QLabel, QFrame, QInputDialog,
    QApplication, QScrollArea, QSplitter)
from PySide6.QtCore import Qt
from core.worker import DiagnosisWorker
from core.kimi_api import set_api_key
from constants import DEMO_INPUT, FIELD_LABELS
from ui.styles import GLOBAL_QSS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI驱动充电站智能诊断平台 · Demo")
        self.resize(1400, 900)
        self.setStyleSheet(GLOBAL_QSS)
        self._api_key = ""
        self._report_text = ""  # 存报告纯文本，用于复制
        self._build_ui()
        self._build_menu()
        self._load_api_key()

    def _build_menu(self):
        menu = self.menuBar().addMenu("设置")
        action = menu.addAction("配置 API Key...")
        action.triggered.connect(self._on_set_api_key)

    def _on_set_api_key(self):
        key, ok = QInputDialog.getText(self, "配置 Kimi API Key",
            "请输入 Moonshot AI API Key:", text=self._api_key)
        if ok and key.strip():
            self._api_key = key.strip()
            set_api_key(self._api_key)
            self.statusBar().showMessage("API Key 已配置", 3000)
            # 保存到 config.json
            try:
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump({"api_key": self._api_key}, f)
            except Exception as e:
                self.statusBar().showMessage(f"保存配置失败: {e}", 3000)

    def _load_api_key(self):
        # 尝试从 config.json 加载 API Key
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    key = config.get("api_key", "")
                    if key:
                        self._api_key = key
                        set_api_key(self._api_key)
                        self.statusBar().showMessage("API Key 已从配置加载", 3000)
            except Exception:
                pass

    def _build_ui(self):
        # 主部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # 使用 QSplitter 实现左右分栏
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧容器
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 右侧容器
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([560, 840]) # 默认 40% 60% 左右

        # ====== 左栏 A区：输入 ======
        a_card = QFrame()
        a_card.setObjectName("card")
        a_layout = QVBoxLayout(a_card)
        a_title = QLabel("A. 场站描述 (自动从第三方系统导入)")
        a_title.setObjectName("card_title")
        a_layout.addWidget(a_title)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("请加载演示案例或输入场站描述...")
        a_layout.addWidget(self.input_edit)

        btn_layout = QHBoxLayout()
        self.btn_demo = QPushButton("加载演示案例")
        self.btn_demo.setObjectName("btn_default")
        self.btn_demo.clicked.connect(self._on_load_demo)
        
        self.btn_start = QPushButton("开始智能诊断")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.clicked.connect(self._on_start)
        
        btn_layout.addWidget(self.btn_demo)
        btn_layout.addWidget(self.btn_start)
        a_layout.addLayout(btn_layout)

        left_layout.addWidget(a_card, stretch=4)

        # ====== 左栏 B区：参数提取结果 ======
        self.b_card = QFrame()
        self.b_card.setObjectName("card")
        b_layout = QVBoxLayout(self.b_card)
        b_title = QLabel("B. 参数提取结果")
        b_title.setObjectName("card_title")
        b_layout.addWidget(b_title)

        self.params_grid = QGridLayout()
        self.param_labels = {}  # 保存引用以便更新
        row, col = 0, 0
        for key, label_text in FIELD_LABELS.items():
            title_lbl = QLabel(f"{label_text}:")
            title_lbl.setStyleSheet("color: #909399;")
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet("font-weight: bold;")
            self.param_labels[key] = val_lbl

            self.params_grid.addWidget(title_lbl, row, col * 2)
            self.params_grid.addWidget(val_lbl, row, col * 2 + 1)
            
            col += 1
            if col > 1:  # 两列布局
                col = 0
                row += 1

        b_layout.addLayout(self.params_grid)
        self.b_card.setVisible(False)
        left_layout.addWidget(self.b_card, stretch=6)

        # 左下角状态提示
        self.step_label = QLabel("等待开始...")
        self.step_label.setStyleSheet("color: #909399; font-style: italic;")
        self.step_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.step_label.setWordWrap(True)
        left_layout.addWidget(self.step_label)

        # ====== 右栏 C区：诊断数据 ======
        self.c_card = QFrame()
        self.c_card.setObjectName("card")
        c_layout = QVBoxLayout(self.c_card)
        c_title = QLabel("C. 经营诊断与优化测算")
        c_title.setObjectName("card_title")
        c_layout.addWidget(c_title)

        # 利润对比
        profit_layout = QHBoxLayout()
        # 当前
        cur_layout = QVBoxLayout()
        cur_lbl = QLabel("当前年利润预估")
        cur_lbl.setObjectName("profit_label")
        self.lbl_cur_profit = QLabel("—")
        self.lbl_cur_profit.setObjectName("profit_val_gray")
        cur_layout.addWidget(cur_lbl)
        cur_layout.addWidget(self.lbl_cur_profit)
        # 优化后
        opt_layout = QVBoxLayout()
        opt_lbl = QLabel("优化后年利润预估")
        opt_lbl.setObjectName("profit_label")
        self.lbl_opt_profit = QLabel("—")
        self.lbl_opt_profit.setObjectName("profit_val_green")
        opt_layout.addWidget(opt_lbl)
        opt_layout.addWidget(self.lbl_opt_profit)

        profit_layout.addLayout(cur_layout)
        profit_layout.addLayout(opt_layout)
        c_layout.addLayout(profit_layout)

        # 动作列表
        actions_lbl = QLabel("建议优化动作:")
        actions_lbl.setStyleSheet("margin-top: 10px; font-weight: bold;")
        c_layout.addWidget(actions_lbl)
        
        self.actions_layout = QVBoxLayout()
        c_layout.addLayout(self.actions_layout)
        
        self.c_card.setVisible(False)
        right_layout.addWidget(self.c_card, stretch=4)

        # ====== 右栏 D区：报告区 ======
        self.d_card = QFrame()
        self.d_card.setObjectName("card")
        d_layout = QVBoxLayout(self.d_card)
        d_title_layout = QHBoxLayout()
        d_title = QLabel("D. 智能诊断报告")
        d_title.setObjectName("card_title")
        
        self.btn_copy = QPushButton("复制报告")
        self.btn_copy.setObjectName("btn_default")
        self.btn_copy.clicked.connect(self._on_copy_report)
        
        d_title_layout.addWidget(d_title)
        d_title_layout.addStretch()
        d_title_layout.addWidget(self.btn_copy)
        d_layout.addLayout(d_title_layout)

        self.report_edit = QTextEdit()
        self.report_edit.setReadOnly(True)
        # Markdown 渲染，PySide6 会自动识别简单的 HTML 标签，纯文本通过 append 会保留格式
        d_layout.addWidget(self.report_edit)
        
        self.d_card.setVisible(False)
        right_layout.addWidget(self.d_card, stretch=6)
        
        # 底部状态栏
        self.statusBar().showMessage("引擎版本: demo-rule-v1 | LLM: Kimi")

    def _on_load_demo(self):
        self.input_edit.setPlainText(DEMO_INPUT)

    def _on_start(self):
        if not self._api_key:
            self.step_label.setText("请先在「设置」菜单中配置 API Key")
            self.step_label.setStyleSheet("color: #F56C6C;")
            return
            
        user_input = self.input_edit.toPlainText().strip()
        if not user_input:
            self.step_label.setText("请输入场站描述")
            self.step_label.setStyleSheet("color: #F56C6C;")
            return

        # 重置 UI
        self.step_label.setStyleSheet("color: #409EFF; font-weight: bold;")
        self._report_text = ""
        self.report_edit.clear()
        self.btn_start.setEnabled(False)
        self.input_edit.setReadOnly(True)
        
        self.b_card.setVisible(False)
        self.c_card.setVisible(False)
        self.d_card.setVisible(False)

        # 启动线程
        self.worker = DiagnosisWorker(user_input)
        self.worker.step_changed.connect(self.step_label.setText)
        self.worker.params_extracted.connect(self._on_params)
        self.worker.diagnosis_ready.connect(self._on_diagnosis)
        self.worker.report_token.connect(self._on_report_token)
        self.worker.finished_all.connect(self._on_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _on_params(self, params: dict):
        for key, val_lbl in self.param_labels.items():
            val = params.get(key)
            val_lbl.setText(str(val) if val is not None else "—")
        self.b_card.setVisible(True)

    def _on_diagnosis(self, result: dict):
        # 利润
        cur_profit = result["current"]["annual_profit"]
        opt_profit = result["optimized"]["annual_profit"]
        
        self.lbl_cur_profit.setText(f"{cur_profit} 万元")
        if cur_profit < 0:
            self.lbl_cur_profit.setObjectName("profit_val_red")
        else:
            self.lbl_cur_profit.setObjectName("profit_val_gray")
        self.lbl_cur_profit.setStyleSheet(self.lbl_cur_profit.styleSheet()) # force update

        self.lbl_opt_profit.setText(f"{opt_profit} 万元")
        
        # 清空旧动作
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 渲染新动作
        for action in result["actions"]:
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0, 4, 0, 4)
            
            tag = QLabel(action["type"])
            tag.setObjectName("tag_blue" if action["type"] == "降本" else "tag_orange")
            
            name = QLabel(action["name"])
            name.setStyleSheet("font-weight: bold;")
            
            detail = QLabel(action["detail"])
            detail.setStyleSheet("color: #606266; font-size: 13px;")
            detail.setWordWrap(True)
            
            delta = QLabel(f"+{action['profit_delta']}万/年")
            delta.setStyleSheet("color: #67C23A; font-weight: bold;")
            
            l.addWidget(tag)
            l.addWidget(name)
            l.addWidget(detail, stretch=1)
            l.addWidget(delta)
            
            self.actions_layout.addWidget(w)

        self.c_card.setVisible(True)
        self.d_card.setVisible(True)

    def _on_report_token(self, token: str):
        self._report_text += token
        cursor = self.report_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self.report_edit.setTextCursor(cursor)
        self.report_edit.ensureCursorVisible()

    def _on_finished(self):
        # 流式结束后一次性转 markdown 渲染
        try:
            import markdown2
            html = markdown2.markdown(self._report_text, extras=["tables"])
            self.report_edit.setHtml(
                f"<div style='color:#333333;font-family:Microsoft YaHei,PingFang SC,sans-serif;'>{html}</div>"
            )
        except ImportError:
            pass  # 没装 markdown2 就保留纯文本
        self.step_label.setStyleSheet("color: #67C23A; font-weight: bold;")
        self.btn_start.setEnabled(True)
        self.input_edit.setReadOnly(False)

    def _on_error(self, err: str):
        self.step_label.setText(f"发生错误: {err}")
        self.step_label.setStyleSheet("color: #F56C6C; font-weight: bold;")
        self.btn_start.setEnabled(True)
        self.input_edit.setReadOnly(False)

    def _on_copy_report(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._report_text)
        self.statusBar().showMessage("报告已复制到剪贴板", 2000)