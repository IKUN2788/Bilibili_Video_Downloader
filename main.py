import sys
import os
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QProgressBar, QTextEdit, QFrame, QMessageBox, 
                             QComboBox, QDialog)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage

from style import MAIN_STYLE
from download_manager import DownloadThread, VideoInfoThread
from login_dialog import LoginDialog

class BilibiliDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilibili 视频下载器")
        self.resize(800, 650)
        
        # 应用样式
        self.setStyleSheet(MAIN_STYLE)
        
        # 主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        
        self.init_ui()
        
        self.download_thread = None
        self.info_thread = None

    def init_ui(self):
        # 1. 顶部栏 (标题 + 登录)
        top_layout = QHBoxLayout()
        
        title_label = QLabel("Bilibili Video Downloader")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setStyleSheet("margin-bottom: 0;") # 覆盖原有 margin
        
        self.login_btn = QPushButton("扫码登录")
        self.login_btn.setObjectName("SecondaryBtn")
        self.login_btn.setFixedWidth(100)
        self.login_btn.clicked.connect(self.show_login_dialog)
        
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.login_btn)
        
        self.main_layout.addLayout(top_layout)
        self.main_layout.addSpacing(10)

        # 2. 输入区域
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入 B 站视频链接 (例如: https://www.bilibili.com/video/BV...)")
        self.url_input.setClearButtonEnabled(True)
        self.url_input.returnPressed.connect(self.start_analysis)
        
        self.analyze_btn = QPushButton("解析视频")
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.setFixedWidth(120)
        self.analyze_btn.clicked.connect(self.start_analysis)
        
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.analyze_btn)
        self.main_layout.addWidget(input_container)

        # 3. 视频信息卡片 (默认隐藏)
        self.info_card = QFrame()
        self.info_card.setObjectName("InfoCard")
        self.info_card.setVisible(False)
        info_layout = QHBoxLayout(self.info_card)
        
        # 封面
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 90)
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setStyleSheet("background-color: #eee; border-radius: 4px;")
        
        # 文字信息容器
        text_info_container = QWidget()
        text_info_layout = QVBoxLayout(text_info_container)
        text_info_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_title = QLabel("视频标题")
        self.video_title.setObjectName("VideoTitle")
        self.video_title.setWordWrap(True)
        
        self.video_uploader = QLabel("UP主: -")
        self.video_uploader.setObjectName("VideoInfo")
        
        # 清晰度选择与下载
        action_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.setMinimumWidth(200)
        
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setFixedWidth(100)
        self.download_btn.clicked.connect(self.start_download)
        
        action_layout.addWidget(QLabel("选择清晰度:"))
        action_layout.addWidget(self.format_combo)
        action_layout.addStretch()
        action_layout.addWidget(self.download_btn)
        
        text_info_layout.addWidget(self.video_title)
        text_info_layout.addWidget(self.video_uploader)
        text_info_layout.addSpacing(10)
        text_info_layout.addLayout(action_layout)
        text_info_layout.addStretch()
        
        info_layout.addWidget(self.thumbnail_label)
        info_layout.addSpacing(15)
        info_layout.addWidget(text_info_container)
        
        self.main_layout.addWidget(self.info_card)

        # 4. 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.main_layout.addWidget(self.progress_bar)

        # 5. 状态/日志
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("等待任务开始...")
        self.log_area.setMaximumHeight(150)
        self.main_layout.addWidget(self.log_area)

        # 底部留白
        self.main_layout.addStretch()

        # 检查登录状态
        self.check_login_status()

    def check_login_status(self):
        if os.path.exists('cookies.json'): # 简单检查
             self.login_btn.setText("已登录")
             self.login_btn.setEnabled(False) # 暂时不支持登出

    def show_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.login_btn.setText("已登录")
            self.login_btn.setEnabled(False)
            self.log("登录成功！")

    def start_analysis(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入视频链接！")
            return

        self.analyze_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.info_card.setVisible(False)
        self.log_area.clear()
        self.log("正在解析视频信息...")

        self.info_thread = VideoInfoThread(url)
        self.info_thread.info_signal.connect(self.update_info_ui)
        self.info_thread.formats_signal.connect(self.update_formats_ui)
        self.info_thread.error_signal.connect(self.on_analysis_error)
        self.info_thread.start()

    def start_download(self):
        url = self.url_input.text().strip()
        format_data = self.format_combo.currentData()
        
        format_id = format_data['format_id'] if format_data else None
        
        self.download_btn.setEnabled(False)
        self.format_combo.setEnabled(False)
        self.log("正在初始化下载...")

        self.download_thread = DownloadThread(url, format_id)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.status_signal.connect(self.update_status)
        self.download_thread.finished_signal.connect(self.on_finished)
        self.download_thread.start()

    @pyqtSlot(dict)
    def update_info_ui(self, info):
        self.info_card.setVisible(True)
        self.video_title.setText(info['title'])
        self.video_uploader.setText(f"UP主: {info['uploader']}")
        
        # 异步加载封面
        if info['thumbnail']:
            try:
                response = requests.get(info['thumbnail'])
                image = QImage()
                image.loadFromData(response.content)
                self.thumbnail_label.setPixmap(QPixmap.fromImage(image))
            except Exception as e:
                self.log(f"封面加载失败: {e}")

    @pyqtSlot(list)
    def update_formats_ui(self, formats):
        self.format_combo.clear()
        if not formats:
            self.format_combo.addItem("自动选择最佳画质", None)
        else:
            for f in formats:
                self.format_combo.addItem(f['display'], f)
            # 默认选中第一个（通常是最好的）
            self.format_combo.setCurrentIndex(0)
        
        self.analyze_btn.setEnabled(True)
        self.url_input.setEnabled(True)
        self.log("解析完成，请选择清晰度并下载。")

    @pyqtSlot(str)
    def on_analysis_error(self, err):
        self.analyze_btn.setEnabled(True)
        self.url_input.setEnabled(True)
        QMessageBox.critical(self, "错误", f"解析失败: {err}")
        self.log(f"解析失败: {err}")

    @pyqtSlot(float)
    def update_progress(self, val):
        self.progress_bar.setValue(int(val))

    @pyqtSlot(str)
    def update_status(self, text):
        self.log(text)

    @pyqtSlot(bool, str)
    def on_finished(self, success, msg):
        self.download_btn.setEnabled(True)
        self.format_combo.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "完成", msg)
            self.log(f"任务结束: {msg}")
        else:
            # 这里的 msg 已经包含了 FFmpeg 相关的友好提示
            QMessageBox.critical(self, "错误", msg)
            self.log(f"任务失败: {msg}")

    def log(self, text):
        self.log_area.append(text)
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.End)
        self.log_area.setTextCursor(cursor)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BilibiliDownloader()
    window.show()
    sys.exit(app.exec_())
