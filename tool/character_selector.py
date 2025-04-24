from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton,
    QGridLayout, QWidget, QScrollArea, QHBoxLayout, QLineEdit, QLabel
)
import os
from tool.config import CHARACTER_FILE_YUAN, CHARACTER_FILE_BENTIE

class CharacterSelector(QDialog):
    def __init__(self, selected_callback,game_name,parent=None):
        super().__init__(parent)
        self.selected_callback = selected_callback
        self.game_name = game_name
        self.setWindowTitle("选择角色")
        self.resize(600, 400)

        self.all_characters = self.load_character_list(self.game_name)
        self.checkboxes = {}

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索角色:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.update_filter)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn = QPushButton("全不选")
        deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        layout.addLayout(button_layout)

        save_btn = QPushButton("确定选择")
        save_btn.clicked.connect(self.save_and_close)
        layout.addWidget(save_btn)

        self.filtered_characters = self.all_characters.copy()
        self.create_checkboxes()
    
    def load_character_list(self, game_name):
            if game_name == "yuan":
                CHARACTER_FILE = CHARACTER_FILE_YUAN
            elif game_name == "bentie":
                CHARACTER_FILE = CHARACTER_FILE_BENTIE
            else:
                CHARACTER_FILE = CHARACTER_FILE_YUAN
            if not os.path.exists(CHARACTER_FILE):
                return []
            with open(CHARACTER_FILE, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]

    def update_filter(self):
        keyword = self.search_input.text().lower()
        self.filtered_characters = [c for c in self.all_characters if keyword in c.lower()]
        self.create_checkboxes()

    def create_checkboxes(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.checkboxes.clear()
        for index, name in enumerate(self.filtered_characters):
            cb = QCheckBox(name)
            cb.setChecked(True)
            self.grid_layout.addWidget(cb, index // 4, index % 4)
            self.checkboxes[name] = cb

    def select_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(True)

    def deselect_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def save_and_close(self):
        selected = [name for name, cb in self.checkboxes.items() if cb.isChecked()]
        if self.selected_callback:
            self.selected_callback(selected)
        self.accept()
