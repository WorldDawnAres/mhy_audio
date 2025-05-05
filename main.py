import asyncio,sys
from qasync import QEventLoop
from tools.ui import MainWindow
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase
from tools.config import FONTS_PATH

def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    font_path = FONTS_PATH
    font_id = QFontDatabase.addApplicationFont(font_path)
    
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_family, 10)
        app.setFont(font)
    else:
        print("字体加载失败，使用默认字体。")

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__": 
    main()
