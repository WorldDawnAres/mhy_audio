import os
from threading import Thread
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox,
    QWidget, QVBoxLayout,QStyleFactory
)
from PySide6.QtGui import QAction, QIcon,QPalette, QColor
from qasync import asyncSlot
from functools import partial
from PySide6.QtCore import Qt

from tools.character_selector import CharacterSelector
from tools.audio_converter import AudioConverter
from tools.config import get_resource_path,CHARACTER_FILE_YUAN,CHARACTER_FILE_BENTIE,URL_PATH
from tools.LogWidget import LogWidget
from tools.text_merger import TextMerger
from tools.audio_download import download_all as download_all_audio
from tools.proxy_manager import check_proxies

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音下载器")
        self.resize(700, 500)
        self.set_dark_mode()

        self.setWindowIcon(QIcon(get_resource_path("icon/icon.ico")))

        self.selected_characters = []
        self.log_widget = LogWidget()
        self.init_ui()
        self.init_menu()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.log_widget)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def init_menu(self):
        menubar = self.menuBar()
        def on_game_selected(game_key):
            self.open_character_selector(game_key)

        self.selected_game = None
        self.selected_characters = []

        select_menu = menubar.addMenu("选择角色")

        games = {
            "原神": "yuan",
            "崩铁": "bentie",
        }

        for game_label, game_key in games.items():
            action = QAction(game_label, self)
            action.triggered.connect(partial(on_game_selected, game_key))
            select_menu.addAction(action)

        download_menu = menubar.addMenu("下载语音")

        zh_action = QAction("中文", self)
        zh_action.triggered.connect(lambda: self.download_selected_characters("zh"))
        download_menu.addAction(zh_action)

        en_action = QAction("英文", self)
        en_action.triggered.connect(lambda: self.download_selected_characters("en"))
        download_menu.addAction(en_action)

        jp_action = QAction("日文", self)
        jp_action.triggered.connect(lambda: self.download_selected_characters("ja"))
        download_menu.addAction(jp_action)

        ko_action = QAction("韩文", self)
        ko_action.triggered.connect(lambda: self.download_selected_characters("ko"))
        download_menu.addAction(ko_action)

        tool_menu = menubar.addMenu("工具")
        
        convert_audio_action = QAction("音频转换", self)
        convert_audio_action.triggered.connect(self.open_audio_converter)
        tool_menu.addAction(convert_audio_action)

        merge_text_action = QAction("合并文本", self)
        merge_text_action.triggered.connect(self.open_text_merger)
        tool_menu.addAction(merge_text_action)

        merge_proxy_action = QAction("代理检测", self)
        merge_proxy_action.triggered.connect(self.text_proxy_merger)
        tool_menu.addAction(merge_proxy_action)

        self.use_proxy_action = QAction("启用代理", self)
        self.use_proxy_action.setCheckable(True)
        self.use_proxy_action.setChecked(False)
        tool_menu.addAction(self.use_proxy_action)

        theme_menu = menubar.addMenu("主题")

        light_action = QAction("浅色模式", self)
        light_action.triggered.connect(self.set_light_mode)
        theme_menu.addAction(light_action)

        dark_action = QAction("深色模式", self)
        dark_action.triggered.connect(self.set_dark_mode)
        theme_menu.addAction(dark_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        menubar.addAction(about_action)
    
    def open_audio_converter(self):
        self.audio_converter_window = AudioConverter()
        self.audio_converter_window.setWindowModality(Qt.ApplicationModal)
        self.audio_converter_window.show()
    
    def set_dark_mode(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

        QApplication.instance().setPalette(dark_palette)
        QApplication.instance().setStyle(QStyleFactory.create("Fusion"))

    def set_light_mode(self):
        light_palette = QPalette()
        light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
        light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        light_palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
        light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        light_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        light_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        app = QApplication.instance()
        app.setPalette(light_palette)
        app.setStyle(QStyleFactory.create("Fusion"))
    
    def open_text_merger(self):
        self.text_merger_window = TextMerger()
        self.text_merger_window.show()
    
    def text_proxy_merger(self):
        urls = self.load_character_list(URL_PATH)
        urls_to_use = [u.split('|')[0] if '|' in u else u for u in urls]
        if not urls_to_use:
            print("⚠️ 没有可用 URL 进行代理测试")
            return
        url = urls_to_use[0].rstrip('/')
        base= f"{url}/Honkai:_Star_Rail_Wiki"
        def task():
            stable_proxies = check_proxies(url_to_test=base, log_func= print, rounds=5)
            for p in stable_proxies:
                print(p)
        Thread(target=task, daemon=True).start()

    def open_character_selector(self, game_name):
        self.selected_game = game_name
        dialog = CharacterSelector(self.receive_selection, self.selected_game)
        dialog.exec()

    def receive_selection(self, selected):
        self.selected_characters = selected
        QMessageBox.information(self, "角色已选择", f"已选择 {len(selected)} 个角色")

    @asyncSlot(str)
    async def download_selected_characters(self, language="zh"):
        if not self.selected_game:
            self.log_widget.append_text("⚠️ 请先选择游戏！")
            return

        if not self.selected_characters:
            reply = QMessageBox.question(
                self,
                "未选择角色",
                "你尚未选择任何角色，程序将默认下载当前指定游戏的全部角色，是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

            if self.selected_game == "yuan":
                character_file = CHARACTER_FILE_YUAN
            elif self.selected_game == "bentie":
                character_file = CHARACTER_FILE_BENTIE
            else:
                self.log_widget.append_text(f"⚠️ 不支持的游戏类型: {self.selected_game}")
                return

            self.selected_characters = self.load_character_list(character_file)

        urls = self.load_character_list(URL_PATH)
        use_proxy = self.use_proxy_action.isChecked()

        try:
            await download_all_audio(
                character_names=self.selected_characters,
                urls=urls,
                language=language,
                game=self.selected_game,
                log_func=self.log_widget.append_text,
                use_proxy=use_proxy
            )
            QMessageBox.information(self, "完成", "所有下载任务完成！")
        except Exception as e:
            self.log_widget.append_text(f"⚠️ 下载过程中出现错误：{e}")
    
    def load_character_list(self, character_file):
        if not os.path.exists(character_file):
            return []
        with open(character_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def show_about(self):
        QMessageBox.information(
            self,
            "关于",
            "本程序用于下载原神,崩铁角色语音。\n版本：v0.6\n\n"
            "免责声明：\n"
            "本程序仅用于学习和交流目的，所有语音及文字内容的版权归原始版权所有者所有。\n"
            "请勿将本程序用于任何商业用途或违法行为。\n"
            "开发者不对因使用本程序造成的任何后果负责。"
        )
