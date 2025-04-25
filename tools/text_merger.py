import os,re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject
from tools.config import get_resource_path


class Logger(QObject):
    log_signal = Signal(str)

class TextMerger(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文本合并工具")
        self.setWindowIcon(QIcon(get_resource_path("icon/icon3.ico")))
        self.resize(600, 300)

        self.logger = Logger()
        self.logger.log_signal.connect(self.log)

        self.parent_folder = os.path.join(os.getcwd(), "audio")
        self.output_folder = os.path.join(os.getcwd(), "output/text")

        layout = QVBoxLayout()

        self.folder_label = QLabel("输入文件夹: (默认 ./audio)")
        layout.addWidget(self.folder_label)

        folder_btn = QPushButton("选择合并文件夹")
        folder_btn.clicked.connect(self.select_folder)
        layout.addWidget(folder_btn)

        self.output_label = QLabel("输出文件夹: (默认 ./output/text)")
        layout.addWidget(self.output_label)

        output_btn = QPushButton("选择输出文件夹")
        output_btn.clicked.connect(self.select_output_folder)
        layout.addWidget(output_btn)

        merge_btn = QPushButton("开始合并")
        merge_btn.clicked.connect(self.merge)
        layout.addWidget(merge_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择父文件夹", os.getcwd())
        if folder:
            self.parent_folder = folder
            self.folder_label.setText(f"输入文件夹: {folder}")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹", os.getcwd())
        if folder:
            self.output_folder = folder
            self.output_label.setText(f"输出文件夹: {folder}")

    def clean_content(self, content):
        content = re.sub(r'[「」]', '', content)
        return content.replace('\n', ' ').replace('\r', ' ')

    def merge(self):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        for group_folder in os.scandir(self.parent_folder):
            if not group_folder.is_dir():
                continue

            group_name = group_folder.name
            group_output_folder = os.path.join(self.output_folder, group_name)
            os.makedirs(group_output_folder, exist_ok=True)

            for character_folder in os.scandir(group_folder.path):
                if not character_folder.is_dir():
                    continue

                character_name = character_folder.name
                txt_files = sorted([
                    f for f in os.listdir(character_folder.path) if f.endswith('.txt')
                ])
                output_file = os.path.join(group_output_folder, character_name + '.txt')

                with open(output_file, 'w', encoding='utf-8') as outfile:
                    for txt_file in txt_files:
                        file_path = os.path.join(character_folder.path, txt_file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as infile:
                                content = infile.read()
                                cleaned = self.clean_content(content)
                                audio_path = f"Data/yuan/audio/{character_name}/{txt_file.replace('.txt', '.wav')}"
                                outfile.write(f"{audio_path}|{character_name}|zh|{cleaned}\n")
                        except Exception as e:
                            self.logger.log_signal.emit(f"读取失败: {file_path} 错误: {e}")

                self.logger.log_signal.emit(f"{group_name}/{character_name} 合并完成 -> {output_file}")

        self.logger.log_signal.emit("所有子文件夹的合并任务完成！")

    def log(self, text):
        self.log_output.append(text)
