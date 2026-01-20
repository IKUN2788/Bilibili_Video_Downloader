import os
import yt_dlp
import imageio_ffmpeg
import json
from PyQt5.QtCore import QThread, pyqtSignal

# 尝试自动设置 ffmpeg 路径
try:
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    if ffmpeg_dir not in os.environ['PATH']:
        os.environ['PATH'] += os.pathsep + ffmpeg_dir
except Exception:
    pass

class VideoInfoThread(QThread):
    info_signal = pyqtSignal(dict)       # 视频信息
    formats_signal = pyqtSignal(list)    # 格式列表
    error_signal = pyqtSignal(str)       # 错误信息

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            # 加载 cookies
            if os.path.exists('cookies.json'):
                with open('cookies.json', 'r') as f:
                    cookies = json.load(f)
                    # 将 cookies 转换为 Netscape 格式字符串或 header 并不容易直接传给 yt-dlp 
                    # 最简单的是将 json cookies 转换回 cookiejar 并保存为 cookies.txt 给 yt-dlp 用
                    # 或者直接构造 http_headers
                    pass

            # 更好的方式是如果存在 cookies.txt 则使用
            if os.path.exists('cookies.txt'):
                 ydl_opts['cookiefile'] = 'cookies.txt'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
                # 发送基本信息
                self.info_signal.emit({
                    'title': info.get('title', '未知标题'),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', '未知UP主'),
                    'duration': info.get('duration', 0)
                })

                # 发送格式列表
                formats = info.get('formats', [])
                # 过滤并整理格式
                video_formats = []
                seen_res = set()
                
                # 倒序遍历，通常最好的在后面
                for f in reversed(formats):
                    # 只要视频流或包含视频的文件
                    if f.get('vcodec') != 'none':
                        height = f.get('height')
                        note = f.get('format_note', '')
                        ext = f.get('ext', '')
                        filesize = f.get('filesize') or f.get('filesize_approx')
                        
                        if height:
                            display = f"{height}P - {note} ({ext})"
                            if filesize:
                                size_mb = filesize / 1024 / 1024
                                display += f" - {size_mb:.1f}MB"
                            
                            # 简单的去重逻辑，优先保留高质量
                            key = f"{height}P-{note}"
                            # if key not in seen_res:
                            video_formats.append({
                                'format_id': f['format_id'],
                                'display': display,
                                'height': height,
                                'ext': ext
                            })
                            # seen_res.add(key)
                
                self.formats_signal.emit(video_formats)

        except Exception as e:
            self.error_signal.emit(str(e))

class DownloadThread(QThread):
    # 信号定义
    progress_signal = pyqtSignal(float)  # 进度百分比
    status_signal = pyqtSignal(str)      # 状态文本
    finished_signal = pyqtSignal(bool, str) # 是否成功，消息

    def __init__(self, url, format_id=None, save_path="downloads"):
        super().__init__()
        self.url = url
        self.format_id = format_id
        self.save_path = save_path
        self.is_running = True
        
        # 确保下载目录存在
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def run(self):
        # yt-dlp 配置
        if self.format_id:
            # 如果指定了视频格式，则下载该视频 + 最佳音频
            format_str = f"{self.format_id}+bestaudio/best"
        else:
            format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        ydl_opts = {
            'format': format_str,
            'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'logger': self.Logger(self.status_signal),
            # 'quiet': True,
        }
        
        # 自动使用 ffmpeg (如果环境变量已设置)
        # 显式指定 ffmpeg 路径 (保险起见)
        try:
             ydl_opts['ffmpeg_location'] = imageio_ffmpeg.get_ffmpeg_exe()
        except:
             pass

        # 加载 Cookies
        if os.path.exists('cookies.txt'): # 优先使用 Netscape 格式
            ydl_opts['cookiefile'] = 'cookies.txt'
        elif os.path.exists('cookies.json'): # 尝试从 JSON 加载 (需要转换，这里暂略，推荐用户重新登录生成 cookies.txt)
             pass

        try:
            self.status_signal.emit("初始化下载引擎...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.status_signal.emit(f"开始下载 (格式: {self.format_id or '自动'})...")
                ydl.download([self.url])
                
            self.finished_signal.emit(True, "下载完成！")
            self.progress_signal.emit(100)
            
        except Exception as e:
            err_msg = str(e)
            if "ffmpeg" in err_msg.lower():
                err_msg = "未找到 FFmpeg，无法合并音视频。\n请尝试安装 FFmpeg 或选择不合并的低画质格式。"
            self.finished_signal.emit(False, f"下载出错: {err_msg}")

    def progress_hook(self, d):
        if not self.is_running:
            raise yt_dlp.utils.DownloadError("下载已取消")
            
        if d['status'] == 'downloading':
            try:
                # 计算进度
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                
                if total_bytes:
                    percentage = (downloaded / total_bytes) * 100
                    self.progress_signal.emit(percentage)
                
                # 构建状态信息
                speed = d.get('speed', 0)
                if speed:
                    speed_str = self.format_speed(speed)
                else:
                    speed_str = "Calculating..."
                    
                eta = d.get('eta', 0)
                self.status_signal.emit(f"下载中... 速度: {speed_str} | 剩余时间: {eta}s")
                
            except Exception:
                pass
                
        elif d['status'] == 'finished':
            self.status_signal.emit("下载完成，正在处理/合并文件...")
            self.progress_signal.emit(99)

    def stop(self):
        self.is_running = False

    @staticmethod
    def format_speed(bytes_per_sec):
        if bytes_per_sec > 1024 * 1024:
            return f"{bytes_per_sec / 1024 / 1024:.2f} MB/s"
        elif bytes_per_sec > 1024:
            return f"{bytes_per_sec / 1024:.2f} KB/s"
        else:
            return f"{bytes_per_sec:.2f} B/s"

    # 自定义 Logger 类用于捕获 yt-dlp 的输出
    class Logger:
        def __init__(self, signal):
            self.signal = signal

        def debug(self, msg):
            if not msg.startswith('[debug] '):
                # self.signal.emit(msg)
                pass

        def warning(self, msg):
            # self.signal.emit(f"Warning: {msg}")
            pass

        def error(self, msg):
            self.signal.emit(f"Error: {msg}")
