import sys, os, asyncio
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox,
    QWidget, QVBoxLayout,QStyleFactory
)
from PySide6.QtGui import QAction, QIcon,QPalette, QColor
from qasync import QEventLoop, asyncSlot
from functools import partial
from PySide6.QtCore import Qt

from tools.character_selector import CharacterSelector
from tools.audio_converter import AudioConverter
from tools.config import get_resource_path,CHARACTER_FILE_YUAN,CHARACTER_FILE_BENTIE
from tools.LogWidget import LogWidget
from tools.text_merger import TextMerger

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
        jp_action.triggered.connect(lambda: self.download_selected_characters("jp"))
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

    def open_character_selector(self, game_name):
        self.selected_game = game_name
        dialog = CharacterSelector(self.receive_selection, self.selected_game)
        dialog.exec()

    def receive_selection(self, selected):
        self.selected_characters = selected
        QMessageBox.information(self, "角色已选择", f"已选择 {len(selected)} 个角色")

    @asyncSlot(str)
    async def download_selected_characters(self, language="zh"):
        if not self.selected_characters:
            reply = QMessageBox.question(
                self,
                "未选择角色",
                "你尚未选择任何角色，程序将默认下载原神全部角色，是否下载全部角色？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if self.selected_game == "yuan":
                    CHARACTER_FILE = CHARACTER_FILE_YUAN
                elif self.selected_game == "bentie":
                    CHARACTER_FILE = CHARACTER_FILE_BENTIE
                else:
                    CHARACTER_FILE = CHARACTER_FILE_YUAN

                self.selected_characters = self.load_character_list(CHARACTER_FILE)
            else:
                return

        self.log_widget.append_text(f"开始下载语音文件（游戏：{self.selected_game}，语言：{language}）...")

        if not self.selected_game:
            self.log_widget.append_text("请先选择游戏！")
            return

        try:
            if self.selected_game == "yuan":
                if language == 'zh':
                    import yuan.yuan_audio_download_zh as download_module
                elif language == 'en':
                    import yuan.yuan_audio_download_en as download_module
                elif language == 'jp':
                    import yuan.yuan_audio_download_jp as download_module
                elif language == 'ko':
                    import yuan.yuan_audio_download_ko as download_module
                else:
                    raise ImportError("语言不支持")
            elif self.selected_game == "bentie":
                if language == 'zh':
                    import bentie.bentie_audio_download_zh as download_module
                elif language == 'en':
                    import bentie.bentie_audio_download_en as download_module
                elif language == 'jp':
                    import bentie.bentie_audio_download_jp as download_module
                elif language == 'ko':
                    import bentie.bentie_audio_download_ko as download_module
                else:
                    raise ImportError("语言不支持")
            else:
                raise ImportError("未知游戏标记")

        except ImportError as e:
            self.log_widget.append_text(f"导入下载模块失败：{e}")
            return
        
        try:
            await download_module.download_all(self.selected_characters, log_func=self.log_widget.append_text)
            self.log_widget.append_text("所有下载任务完成！")
            QMessageBox.information(self, "完成", "下载完成！")
        except Exception as e:
            self.log_widget.append_text(f"下载过程中出现错误：{e}")
    
    def load_character_list(self, character_file):
        if not os.path.exists(character_file):
            return []
        with open(character_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def show_about(self):
        QMessageBox.information(
            self,
            "关于",
            "本程序用于下载原神,崩铁角色语音。\n版本：v0.5\n\n"
            "免责声明：\n"
            "本程序仅用于学习和交流目的，所有语音及文字内容的版权归原始版权所有者所有。\n"
            "请勿将本程序用于任何商业用途或违法行为。\n"
            "开发者不对因使用本程序造成的任何后果负责。"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()
