# B站视频下载器 (基于 PyQt5 & yt-dlp)

这是一个简单美观的 Bilibili 视频下载器，支持下载高清视频。

## 功能特点
- 🎥 支持 B 站视频下载
- 🖥️ 现代化扁平 UI 设计
- 📊 实时显示下载进度和速度
- 🖼️ 自动解析并显示视频封面和标题

## 环境要求
- Python 3.8+
- [FFmpeg](https://ffmpeg.org/download.html) (推荐安装，用于合并高质量音视频流)

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 注意事项
- 如果下载的视频没有声音或画质较低，请确保您的电脑上安装了 FFmpeg 并将其添加到了系统环境变量中。
- 本工具仅供学习交流使用。
