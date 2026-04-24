GLOBAL_QSS = """
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 14px;
    color: #333333;
}

/* 卡片样式 */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E4E7ED;
    border-radius: 8px;
}

QFrame#card_title_bg {
    background-color: #F8F9FA;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border-bottom: 1px solid #E4E7ED;
}

QLabel#card_title {
    font-weight: bold;
    font-size: 15px;
    color: #2C3E50;
    padding: 8px;
}

/* 文本框样式 */
QTextEdit {
    border: 1px solid #DCDFE6;
    border-radius: 4px;
    background-color: #F8F9FA; /* 只读状态用灰色背景 */
    color: #333333;
    padding: 8px;
    line-height: 1.5;
}

/* 按钮样式 */
QPushButton {
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton#btn_primary {
    background-color: #409EFF;
    color: white;
    border: none;
}
QPushButton#btn_primary:hover {
    background-color: #66B1FF;
}
QPushButton#btn_primary:disabled {
    background-color: #A0CFFF;
}

QPushButton#btn_default {
    background-color: #FFFFFF;
    color: #606266;
    border: 1px solid #DCDFE6;
}
QPushButton#btn_default:hover {
    color: #409EFF;
    border-color: #C6E2FF;
    background-color: #ECF5FF;
}

/* 诊断卡片内样式 */
QLabel#profit_label {
    font-size: 12px;
    color: #909399;
}
QLabel#profit_val_gray {
    font-size: 24px;
    font-weight: bold;
    color: #606266;
}
QLabel#profit_val_red {
    font-size: 24px;
    font-weight: bold;
    color: #F56C6C;
}
QLabel#profit_val_green {
    font-size: 24px;
    font-weight: bold;
    color: #67C23A;
}

/* 动作标签 */
QLabel#tag_blue {
    background-color: #ECF5FF;
    color: #409EFF;
    border: 1px solid #D9ECFF;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 12px;
}
QLabel#tag_orange {
    background-color: #FEF0F0;
    color: #F56C6C;
    border: 1px solid #FDE2E2;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 12px;
}
"""