# 现代化 UI 样式表

MAIN_STYLE = """
QMainWindow {
    background-color: #f0f2f5;
}

QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 14px;
}

/* 标题栏区域 */
QLabel#TitleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 20px;
}

/* 输入框 & 下拉框 */
QLineEdit, QComboBox {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 8px 10px;
    background-color: white;
    selection-background-color: #3498db;
    color: #333;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #3498db;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

/* 按钮 */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #2573a7;
}

QPushButton:disabled {
    background-color: #bdc3c7;
    color: #ecf0f1;
}

/* 次要按钮（如登录） */
QPushButton#SecondaryBtn {
    background-color: #95a5a6;
}
QPushButton#SecondaryBtn:hover {
    background-color: #7f8c8d;
}

/* 进度条 */
QProgressBar {
    border: none;
    background-color: #e0e0e0;
    border-radius: 6px;
    text-align: center;
    color: white;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #2ecc71;
    border-radius: 6px;
}

/* 视频信息卡片 */
QFrame#InfoCard {
    background-color: white;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
}

QLabel#VideoTitle {
    font-size: 16px;
    font-weight: bold;
    color: #333;
}

QLabel#VideoInfo {
    color: #666;
    font-size: 12px;
}

/* 日志区域 */
QTextEdit {
    background-color: #2c3e50;
    color: #ecf0f1;
    border-radius: 8px;
    padding: 10px;
    font-family: Consolas, monospace;
    font-size: 12px;
    border: none;
}
"""
