import os,sys

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

CHARACTER_FILE_YUAN = get_resource_path("txt/characters_yuan.txt")
CHARACTER_FILE_BENTIE = get_resource_path("txt/characters_bentie.txt")
FFMPEG_PATH = get_resource_path("tool/ffmpeg.exe")
