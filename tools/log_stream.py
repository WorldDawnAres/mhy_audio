from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextEdit

class EmittingStream(QObject):
    text_written = Signal(str, str)

    def __init__(self, text_edit: QTextEdit):
        super().__init__()
        self.text_edit = text_edit
        self.text_written.connect(self.write_to_output)

    def write(self, text):
        text = text.rstrip()
        if not text:
            return
        
        if "下载完成" in text or "转换成功" in text or "合并完成" in text:
            style = "success"
        elif "失败" in text or "放弃" in text or "错误" in text or "转换失败" in text:
            style = "error"
        else:
            style = "info"

        self.text_written.emit(text, style)

    def write_to_output(self, text, style):
        color = {
            "info": "orange",
            "error": "red",
            "success": "green",
        }.get(style, "black")

        self.text_edit.setTextColor(color)
        self.text_edit.append(text)
        self.text_edit.moveCursor(QTextCursor.End)

    def flush(self):
        pass
