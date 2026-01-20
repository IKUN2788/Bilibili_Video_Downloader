# 手把手教你用 Python + PyQt5 打造高颜值 B 站视频下载器

![Bilibili Downloader Cover](https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=1000&auto=format&fit=crop)

## 🎯 前言

作为一个 B 站重度用户，经常遇到想要收藏的视频。虽然市面上有很多下载工具，但要么界面简陋，要么广告满天飞，或者不支持高清画质下载。

作为一名程序员，为什么不自己动手做一个呢？今天我就带大家用 Python + PyQt5 + yt-dlp 开发一个**界面美观、支持扫码登录、可选画质**的 B 站视频下载器。

## ✨ 核心功能预览

在开始写代码之前，我们先明确一下这个工具需要具备哪些功能：

1.  **现代化 UI**：告别原生丑陋的界面，使用 QSS 进行美化。
2.  **多线程下载**：下载过程不卡顿界面，实时显示进度和速度。
3.  **扫码登录**：支持 B 站扫码登录，获取更高画质（1080P+ / 4K）。
4.  **清晰度选择**：自动解析视频所有可用格式，让用户选择。
5.  **自动合并**：自动处理音视频分离问题，合并导出 MP4。

## 🛠️ 技术栈选择

*   **GUI 框架**: [PyQt5](https://pypi.org/project/PyQt5/) - 强大的桌面应用开发框架。
*   **下载引擎**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) - youtube-dl 的最强分支，对 B 站支持极佳。
*   **二维码生成**: `qrcode` - 用于生成登录二维码。
*   **环境依赖**: `imageio-ffmpeg` - 自动管理 FFmpeg 环境，免去用户手动配置的麻烦。

## 💡 核心实现细节

### 1. 界面设计 (UI Design)

为了让界面看起来不那么"古老"，我们采用了扁平化设计风格。通过 QSS (Qt Style Sheets) 来定义样式，类似于网页开发中的 CSS。

```python
# style.py 部分代码
MAIN_STYLE = """
QMainWindow {
    background-color: #f0f2f5;
}
QPushButton {
    background-color: #3498db;
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
}
/* ...更多样式 */
"""
```

我们使用了卡片式布局 (`QFrame`) 来展示视频信息，圆角输入框和进度条，整体色调清新舒适。

### 2. 解决界面卡顿 (Threading)

GUI 开发的大忌就是在主线程执行耗时操作。下载视频是一个典型的耗时任务，如果直接写在按钮点击事件里，界面会瞬间假死。

我们使用 `QThread` 将下载任务移至后台线程：

```python
class DownloadThread(QThread):
    progress_signal = pyqtSignal(float)  # 进度信号
    status_signal = pyqtSignal(str)      # 状态信号

    def run(self):
        # 在这里执行 yt-dlp 的下载逻辑
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
```

通过 `pyqtSignal` 信号槽机制，子线程将进度和日志发送回主线程更新 UI，保证了界面的流畅响应。

### 3. 扫码登录实现 (QR Login)

B 站的高清画质（1080P60, 4K）通常需要登录甚至大会员权限。我们通过调用 B 站的 Passport API 实现了扫码登录：

1.  **获取二维码**：请求 `qrcode/generate` 接口拿到 URL。
2.  **展示二维码**：使用 `qrcode` 库生成图片并在 PyQt 界面显示。
3.  **轮询状态**：后台线程每隔 2 秒请求 `qrcode/poll` 接口检查扫码状态。
4.  **保存 Cookie**：登录成功后，将 Cookies 保存为 JSON/Netscape 格式，供 `yt-dlp` 调用。

### 4. 解决 FFmpeg 依赖难题

`yt-dlp` 下载高清视频时，通常会将视频流（无声）和音频流分开下载，最后需要 FFmpeg 进行合并。普通用户很难配置好 FFmpeg 环境变量。

我们引入了 `imageio-ffmpeg` 库，它自带了编译好的 FFmpeg 可执行文件。我们在代码中动态获取其路径并注入环境变量：

```python
import imageio_ffmpeg

# 自动配置 FFmpeg 路径
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
os.environ['PATH'] += os.pathsep + os.path.dirname(ffmpeg_path)
```

这样用户下载即用，无需任何额外配置！

## 🚀 如何运行本项目

### 第一步：克隆代码
```bash
git clone https://github.com/your-repo/bilibili-downloader.git
cd bilibili-downloader
```

### 第二步：安装依赖
```bash
pip install -r requirements.txt
```

### 第三步：运行
```bash
python main.py
```

## 📝 总结

通过这个项目，我们不仅学习了 PyQt5 的界面开发，还深入了解了多线程编程、网络请求处理以及外部工具(`yt-dlp`, `ffmpeg`)的集成。

这个下载器目前已经可以满足日常使用，未来我们还可以考虑加入：
*   **批量下载**：支持下载整个收藏夹或播放列表。
*   **历史记录**：保存下载过的视频记录。
*   **自动转码**：支持导出 MP3 音频。

如果你对代码感兴趣，欢迎在评论区留言交流！
