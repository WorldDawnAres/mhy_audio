import sys
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QTextCursor
from tools.log_stream import EmittingStream

class LogWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        
        sys.stdout = EmittingStream(text_edit=self)
        sys.stderr = EmittingStream(text_edit=self)

    def append_text(self, text: str):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text + '\n')
        self.ensureCursorVisible()
