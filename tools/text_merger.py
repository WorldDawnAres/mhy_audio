import os,re,sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit,QInputDialog
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject
from tools.config import get_resource_path
from tools.log_stream import EmittingStream

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

        self.text = None

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

        self.custom_label = QLabel("请点击按钮输入可选信息：(不输入则使用默认格式)")
        layout.addWidget(self.custom_label)

        custom_btn = QPushButton("自定义文本内容")
        custom_btn.clicked.connect(self.custom_text)
        layout.addWidget(custom_btn)

        merge_btn = QPushButton("开始合并")
        merge_btn.clicked.connect(self.merge)
        layout.addWidget(merge_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

        sys.stdout = EmittingStream(text_edit=self.log_output)
        sys.stderr = EmittingStream(text_edit=self.log_output)
        
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择合并文件夹", os.getcwd())
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
    
    def custom_text(self):
        default_text = "Data/{model_name}/audio/{model_name}_audio_{language}/{character_name}"
        text, ok = QInputDialog.getText(self, "自定义文本", 
                                        "请输入自定义文本路径:\n可输入内容有:\n1. {model_name}: 模型名称\n"
                                        "2. {language}: 语言\n3. {character_name}: 角色名称\n"
                                        "4. 其他文件夹名称: 如Data等\n5. 可根据以下示例格式自定义输入",
                                        text=default_text)
        if ok:
            self.text = text.strip() if text.strip() else default_text
        else:
            self.text = None
    
        if self.text:
            self.custom_label.setText(f"当前自定义内容: {self.text}")
        else:
            self.custom_label.setText("使用默认格式")

    def get_language_from_path(self, folder_path):
        current_folder = os.path.basename(folder_path)
        current_match = re.match(r'^([a-zA-Z0-9]+)_audio_([a-zA-Z\-]+)$', current_folder)
        if current_match:
            return current_match.group(2)
        
        parent_folder = os.path.basename(os.path.dirname(folder_path))
        parent_match = re.match(r'^([a-zA-Z0-9]+)_audio_([a-zA-Z\-]+)$', parent_folder)
        if parent_match:
            return parent_match.group(2)
        
        return "unknown"

    def merge(self):
        def process_txt_files(folder_path, output_path, character_name, model_info=None):
            if not model_info:
                parent_folder = os.path.basename(os.path.dirname(folder_path))
                prefix_match = re.match(r'^([a-zA-Z0-9]+)_audio_([a-zA-Z\-]+)$', parent_folder)
                model_info = {
                    'model_name': prefix_match.group(1) if prefix_match else 'unknown',
                    'language': prefix_match.group(2) if prefix_match else 'unknown'
                }

            txt_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.txt')])
            with open(output_path, 'w', encoding='utf-8') as outfile:
                for txt_file in txt_files:
                    file_path = os.path.join(folder_path, txt_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            cleaned = self.clean_content(content)
                            if self.text:
                                real_path = self.text.format(
                                    model_name=model_info['model_name'],
                                    language=model_info['language'],
                                    character_name=character_name
                                )
                                audio_path = os.path.join(real_path, txt_file.replace(".txt", ".wav")).replace("\\", "/")
                            else:
                                audio_path = txt_file.replace(".txt", ".wav").replace("\\", "/")
                            outfile.write(f"{audio_path}|{character_name}|{model_info['language']}|{cleaned}\n")
                    except Exception as e:
                        print(f"读取失败: {file_path} 错误: {e}")

        def has_txt_files(folder):
            return any(f.name.endswith('.txt') for f in os.scandir(folder) if f.is_file())

        def has_subfolders(folder):
            return any(f.is_dir() for f in os.scandir(folder))

        if os.path.isdir(self.parent_folder):
            if has_subfolders(self.parent_folder):
                for model_folder in os.scandir(self.parent_folder):
                    if not model_folder.is_dir():
                        continue
                    
                    model_folder_name = model_folder.name
                    audio_folder_match = re.match(r'^([a-zA-Z0-9]+)_audio_([a-zA-Z\-]+)$', model_folder_name)
                    
                    if audio_folder_match:
                        model_name = audio_folder_match.group(1)
                        language = audio_folder_match.group(2)
                        model_output_folder = os.path.join(self.output_folder, model_folder_name)
                        os.makedirs(model_output_folder, exist_ok=True)
                        
                        for character_folder in os.scandir(model_folder.path):
                            if not character_folder.is_dir():
                                continue
                            
                            character_name = character_folder.name
                            output_file = os.path.join(model_output_folder, f"{character_name}_launcher_{language}.txt")
                            
                            if has_txt_files(character_folder.path):
                                model_info = {
                                    'model_name': model_name,
                                    'language': language
                                }
                                process_txt_files(character_folder.path, output_file, character_name, model_info)
                                print(f"文本合并完成 -> {output_file}")
                        continue
                    
                    subfolder_name = model_folder_name
                    language = self.get_language_from_path(model_folder.path)
                    if os.path.exists(self.output_folder) and self.output_folder != os.path.join(os.getcwd(), "output/text"):
                        output_file = os.path.join(self.output_folder, f"{subfolder_name}_launcher_{language}.txt")
                    else:
                        os.makedirs(self.output_folder, exist_ok=True)
                        output_file = os.path.join(self.output_folder, f"{subfolder_name}_launcher_{language}.txt")

                    if has_txt_files(model_folder.path):
                        process_txt_files(model_folder.path, output_file, subfolder_name)
                        print(f"文本合并完成 -> {output_file}")

            elif has_txt_files(self.parent_folder):
                folder_name = os.path.basename(self.parent_folder.rstrip("\\/"))
                language = self.get_language_from_path(self.parent_folder)
                
                if os.path.exists(self.output_folder) and self.output_folder != os.path.join(os.getcwd(), "output/text"):
                    output_file = os.path.join(self.output_folder, f"{folder_name}_launcher_{language}.txt")
                else:
                    os.makedirs(self.output_folder, exist_ok=True)
                    output_file = os.path.join(self.output_folder, f"{folder_name}_launcher_{language}.txt")
                
                process_txt_files(self.parent_folder, output_file, folder_name)
                print(f"文本合并完成 -> {output_file}")
                return

            print("所有文件夹的合并任务完成！")

    def log(self, text):
        self.log_output.append(text)
