import sys
import time
import qrcode
import requests
import json
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage

class LoginThread(QThread):
    qr_signal = pyqtSignal(QPixmap, str) # 二维码图片, url
    status_signal = pyqtSignal(str)      # 状态文本
    success_signal = pyqtSignal(dict)    # 登录成功，返回 cookies 字典
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/'
        }

    def run(self):
        try:
            # 1. 获取二维码 URL 和 key
            self.status_signal.emit("正在获取登录二维码...")
            res = self.session.get('https://passport.bilibili.com/x/passport-login/web/qrcode/generate', headers=self.headers)
            data = res.json()
            if data['code'] != 0:
                self.status_signal.emit(f"获取二维码失败: {data['message']}")
                return

            url = data['data']['url']
            qrcode_key = data['data']['qrcode_key']

            # 2. 生成二维码图片
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为 QPixmap
            import io
            buffer = io.BytesIO()
            img.save(buffer)
            qimg = QImage.fromData(buffer.getvalue())
            pixmap = QPixmap.fromImage(qimg)
            
            self.qr_signal.emit(pixmap, url)
            self.status_signal.emit("请使用 Bilibili 手机客户端扫码登录")

            # 3. 轮询登录状态
            while self.running:
                time.sleep(2)
                check_res = self.session.get(
                    f'https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={qrcode_key}',
                    headers=self.headers
                )
                check_data = check_res.json()
                
                code = check_data['data']['code']
                
                if code == 0: # 登录成功
                    self.status_signal.emit("登录成功！")
                    # 获取 cookies
                    cookies = self.session.cookies.get_dict()
                    self.success_signal.emit(cookies)
                    break
                elif code == 86101: # 未扫码
                    pass 
                elif code == 86090: # 已扫码未确认
                    self.status_signal.emit("已扫码，请在手机上确认")
                elif code == 86038: # 二维码失效
                    self.status_signal.emit("二维码已失效，请重新打开")
                    break
                else:
                    self.status_signal.emit(f"未知状态: {check_data['data']['message']}")

        except Exception as e:
            self.status_signal.emit(f"发生错误: {str(e)}")

    def stop(self):
        self.running = False

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("扫码登录 Bilibili")
        self.setFixedSize(300, 400)
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { font-size: 14px; color: #333; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(200, 200)
        self.qr_label.setStyleSheet("border: 1px solid #eee; background-color: #f5f5f5;")
        self.qr_label.setAlignment(Qt.AlignCenter)
        
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        
        layout.addWidget(self.qr_label)
        layout.addSpacing(20)
        layout.addWidget(self.status_label)
        
        self.login_thread = LoginThread()
        self.login_thread.qr_signal.connect(self.update_qr)
        self.login_thread.status_signal.connect(self.update_status)
        self.login_thread.success_signal.connect(self.on_success)
        self.login_thread.start()
        
        self.cookies = None

    def update_qr(self, pixmap, url):
        self.qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def update_status(self, text):
        self.status_label.setText(text)

    def on_success(self, cookies):
        self.cookies = cookies
        self.save_cookies_to_netscape_format(cookies)
        QMessageBox.information(self, "成功", "登录成功！")
        self.accept()

    def save_cookies_to_netscape_format(self, cookies):
        # yt-dlp 支持 Netscape 格式的 cookies.txt
        # 这里简单处理，将 key=value 写入 cookies.txt
        # 注意：这只是一个简化的写入，标准的 Netscape 格式更复杂
        # 但 yt-dlp 也可以通过 --cookies-from-browser 读取，或者我们可以直接传 cookie header
        # 为了兼容性，我们这里保存一个 json 文件方便程序读取
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f)

    def closeEvent(self, event):
        self.login_thread.stop()
        super().closeEvent(event)
