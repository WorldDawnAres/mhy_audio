import os,sys,platform,shutil

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_ffmpeg_path():
    system = platform.system()
    if system == "Windows":
        return get_resource_path("tool/ffmpeg.exe")
    elif system == "Linux":
        internal_ffmpeg = get_resource_path("tool/ffmpeg")
        if os.path.isfile(internal_ffmpeg) and os.access(internal_ffmpeg, os.X_OK):
            return internal_ffmpeg
        else:
            ffmpeg = shutil.which("ffmpeg")
            if ffmpeg:
                return ffmpeg
            else:
                raise FileNotFoundError("未找到 ffmpeg，请安装 ffmpeg 或提供 tool/ffmpeg。")
    else:
        raise OSError("不支持的操作系统")

CHARACTER_FILE_YUAN = get_resource_path("txt/characters_yuan.txt")
CHARACTER_FILE_BENTIE = get_resource_path("txt/characters_bentie.txt")
FFMPEG_PATH = get_ffmpeg_path()
FONTS_PATH = get_resource_path("fonts/SourceHanSansTC-Light.ttf")
URL_PATH = get_resource_path("txt/url.txt")
