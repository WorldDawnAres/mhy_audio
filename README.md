# 目录

**[English](README_en.md) | [简体中文](README.md)**

- [目录](#目录)
  - [下载地址](#下载地址)
  - [功能](#功能)
  - [程序结构](#程序结构)
  - [介绍](#介绍)
  - [安装和运行方式](#安装和运行方式)
    - [安装python库](#安装python库)
    - [运行程序](#运行程序)
      - [方法一](#方法一)
      - [方法二](#方法二)
      - [方法三](#方法三)
  - [免责声明🛡️](#免责声明️)

## 下载地址

[点击此处进行下载](https://github.com/WorldDawnAres/mhy_audio/releases)
>
> releases中.exe使用Python3.10.11版本打包，可能不支持Windows7以下系统使用
>
> Linux二进制文件则使用Python3.9.13版本打包。
>
> 喜欢这个项目吗？请给我留个星 ⭐，让更多人看到它！感谢你的支持！

## 功能

- [x] 支持自定义选择原神角色
- [x] 可选择中文，英文，日文，韩文
- [x] 支持Windows和Linux
- [x] 日志显示功能
- [x] 文本文件合并
- [x] 自定义采样率转换wav文件
- [x] 支持自定义选择崩铁角色
- [x] 支持深色模式

## 程序结构

```bash
mhy_audio
├── /mhy_audio
│   ├── /icon
│   │   ├── icon.ico
│   │   ├── icon1.ico
│   │   ├── icon2.ico
│   │   └── icon3.ico
│   ├── /txt
│   │   ├── characters_bentie.txt
│   │   └── characters_yuan.txt
│   ├── /fonts
│   │   └── SourceHanSansTC-Light.ttf
│   ├── /tools
│   │   ├── character_selector.py
│   │   ├── text_merger.py
│   │   ├── audio_converter.py
│   │   ├── audio_download.py
│   │   ├── proxy_manager.py
│   │   ├── config.py
│   │   ├── log_stream.py
│   │   ├── ui.py
│   │   └── LogWidget.py
│   ├── /tool
│   │   ├── ffmpeg.exe
│   ├── main.py
└── /README.md
```

## 介绍

>本程序用于下载和转换音频，并合并文本，以便于为AI模型训练提供MHY游戏角色的语音数据。
>
>用户可以选择自定义选择原神角色，崩铁角色，支持选择中文，英文，日文，韩文
>
>在下载后，将音频文件自定义转换为wav格式，合并文字文件

![Screenshot 1](./Pictures/1.png "可选标题")
>
>用户可以通过菜单选择功能，当前版本若不选择角色则默认全部下载
>
>在音频下载，音频转换，文字合并功能中根据程序需要的参数选择并执行
>
>程序的GUI界面支持日志显示,便于用户查看操作记录。

![Screenshot 1](./Pictures/2.png "可选标题")

![Screenshot 1](./Pictures/3.png "可选标题")

![Screenshot 1](./Pictures/4.png "可选标题")

>此外支持深色模式，用户可以根据自己的喜好选择使用深色模式或浅色模式

![Screenshot 1](./Pictures/5.png "可选标题")

>程序字体使用SourceHanSansTC-Light.ttf，用户可以根据自己的喜好选择使用其他字体打包
>
>将文件放在/fonts文件夹下并自行修改config.py中的字体路径即可
>
[点击下载本程序使用字体原地址](https://github.com/adobe-fonts/source-han-serif)

## 安装和运行方式

### 安装python库

>使用以下命令安装所需的Python库:

```bash
pip install aiohttp beautifulsoup4 PySide6 qasync requests cloudscraper
pip install PyInstaller(可选)
```

### 运行程序

>你可以使用以下任一方式来运行程序：

#### 方法一

>使用 PyInstaller 打包程序：
>
>1.你需要在ffmpeg官网下载ffmpeg(以下方法适用于windows)

[点击此处下载ffmpeg](https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-7.0.2-full_build.7z)
>2.在上面链接下载后将压缩包解压并找到bin里的ffmpeg.exe解压到/mhy_audio/tool/ 目录下(若没有创建文件夹则自行创建)
>
>3.然后使用以下命令打包程序：

```bash
PyInstaller -F --add-data "./txt/*;txt" --add-data "./icon/*;icon" --add-data "./tool/*;tool" -w -i ./icon/icon.ico main.py
```

>最后在 dist 目录下找到可执行文件。
>
>以下方法适用于Linux
>
>Linux如果需要打包ffmpeg则需要将解压的二进制文件全部放在/mhy_audio/tool/ 目录下打包

[点击此处查看下载适用于Linux-ffmpeg方法](https://blog.csdn.net/weixin_43667077/article/details/122276284)

#### 方法二

>直接运行 Python 脚本：
>
>需要安装相应库然后完成下载ffmpeg步骤后直接运行main.py即可(适用于windows)
>
>在Linux上可以通过命令安装ffmpeg后运行main.py

```bash
python main.py
```

#### 方法三

>windows用户可以直接下载releases中的exe文件直接运行
>
>Linux用户下载releases中的二进制文件直接运行(带图形界面)
>
>在linux非图形化界面中可安装x11等图形化界面库后运行(针对SSH远程来说)
>
>操作方式如下：

```bash
sudo apt-get update
sudo apt-get install libgl1 libegl1 libxcb-icccm4 libxcb-cursor0 libxcb-keysyms1 libxcb-shape0 libxkbcommon-x11-0
```

## 免责声明🛡️

>本项目仅用于学习和个人交流目的。所有程序下载的音频及文本内容的版权归原版权所有者所有。
>
>请勿将本程序用于任何商业用途或违法用途。
>
>请合理使用本程序，因使用造成的任何风险与后果（如 IP 被封或其他问题），开发者概不负责。
>
>如果您是内容权利方并认为本项目涉及侵权，请通过 issue 或邮件联系，开发者将第一时间处理。
>
>感谢您的理解与支持！
