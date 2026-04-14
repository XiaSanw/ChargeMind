import json
import time
from PySide6.QtCore import QThread, Signal
from core.kimi_api import extract_params, generate_report_stream
from core.diagnosis import diagnose


class DiagnosisWorker(QThread):
    # --- 信号 ---
    step_changed = Signal(str)        # → 更新步骤提示文字
    params_extracted = Signal(dict)   # → 填充 B 区(参数表)
    diagnosis_ready = Signal(dict)    # → 填充 C 区(诊断数据)
    report_token = Signal(str)        # → 追加到 D 区(报告，逐token)
    finished_all = Signal()           # → 全部完成
    error_occurred = Signal(str)      # → 显示错误

    def __init__(self, user_input: str, parent=None):
        super().__init__(parent)
        self.user_input = user_input

    def run(self):
        try:
            # 步骤 1
            self.step_changed.emit("正在提取场站参数...")
            params = extract_params(self.user_input)
            self.params_extracted.emit(params)

            # 步骤 2
            self.step_changed.emit("正在运行诊断分析...")
            time.sleep(1.5)  # 人为延迟，让用户感受到"算法在处理"
            result = diagnose(params)
            self.diagnosis_ready.emit(result)

            # 步骤 3（最多重试 2 次）
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    self.step_changed.emit(
                        "正在生成诊断报告..."
                        + (f"（第{attempt+1}次重试）" if attempt > 0 else "")
                    )
                    # 精简 JSON：去掉 indent 减少 token 数
                    diagnosis_str = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
                    for token in generate_report_stream(
                        station_name=params.get("station_name", ""),
                        location=params.get("location", ""),
                        diagnosis_json=diagnosis_str,
                    ):
                        self.report_token.emit(token)
                    break  # 成功则跳出重试
                except Exception:
                    if attempt == max_retries:
                        raise  # 最后一次仍失败则抛出
                    self._report_text_reset = True
                    time.sleep(2)

            self.step_changed.emit("诊断完成")
            self.finished_all.emit()

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))