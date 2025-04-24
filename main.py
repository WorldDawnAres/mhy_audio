import sys, os, asyncio, importlib
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QTextEdit,
    QWidget, QVBoxLayout, QMenu
)
from PySide6.QtGui import QFont, QAction, QIcon
from qasync import QEventLoop, asyncSlot

from tool.character_selector import CharacterSelector
from tool.config import CHARACTER_FILE,get_resource_path
from tool.LogWidget import LogWidget

def load_all_characters():
    if not os.path.exists(CHARACTER_FILE):
        return []
    with open(CHARACTER_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音下载器主程序")
        self.resize(700, 500)

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

        select_action = QAction("选择角色", self)
        select_action.triggered.connect(self.open_character_selector)
        menubar.addAction(select_action)

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

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        menubar.addAction(about_action)

    def open_character_selector(self):
        selector = CharacterSelector(selected_callback=self.receive_selection)
        selector.exec()

    def receive_selection(self, selected):
        self.selected_characters = selected
        QMessageBox.information(self, "角色已选择", f"已选择 {len(selected)} 个角色")

    @asyncSlot(str)
    async def download_selected_characters(self, language="zh"):
        if not self.selected_characters:
            reply = QMessageBox.question(
                self,
                "未选择角色",
                "你尚未选择任何角色，是否下载全部角色？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.selected_characters = load_all_characters()
            else:
                return

        self.log_widget.append_text(f"开始下载语音文件（语言：{language}）...")

        if language == 'zh':
            import yuan.yuan_audio_download_zh as download_module
        elif language == 'en':
            import yuan.yuan_audio_download_en as download_module
        elif language == 'jp':
            import yuan.yuan_audio_download_jp as download_module
        elif language == 'ko':
            import yuan.yuan_audio_download_ko as download_module
        else:
            self.log_widget.append_text(f"不支持的语言：{language}")
            return

        try:
            await download_module.download_all(self.selected_characters, log_func=self.log_widget.append_text)
            self.log_widget.append_text("所有下载任务完成！")
            QMessageBox.information(self, "完成", "下载完成！")
        except Exception as e:
            self.log_widget.append_text(f"下载过程中出现错误：{e}")


    def show_about(self):
        QMessageBox.information(
            self,
            "关于",
            "本程序用于下载原神角色语音。\n版本：v0.1\n\n"
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
