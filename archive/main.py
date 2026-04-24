import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 可以在这里设置全局字体，尽管在 QSS 里也设置了
    font = app.font()
    font.setFamily("Microsoft YaHei")
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()