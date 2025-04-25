import os,sys,subprocess,threading,platform
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QSpinBox, QHBoxLayout, QLineEdit, QTextEdit
)
from PySide6.QtCore import Signal, QObject
from tools.config import FFMPEG_PATH, get_resource_path
from tools.log_stream import EmittingStream

class Logger(QObject):
    log_signal = Signal(str)

class AudioConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音频转换工具")
        self.resize(600, 300)
        self.setWindowIcon(QIcon(get_resource_path("icon/icon1.ico")))

        layout = QVBoxLayout()

        self.input_label = QLabel("输入文件夹: (默认 ./audio)")
        layout.addWidget(self.input_label)

        folder_btn = QPushButton("选择转换文件夹")
        folder_btn.clicked.connect(self.select_input_folder)
        layout.addWidget(folder_btn)

        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("采样率："))
        self.sample_rate_input = QLineEdit()
        self.sample_rate_input.setPlaceholderText("例如：44100 或 48000")
        self.sample_rate_input.setText("44100")
        rate_layout.addWidget(self.sample_rate_input)
        layout.addLayout(rate_layout)

        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("最大线程数(根据自身cpu核心数调整，默认12)："))
        self.thread_count = QSpinBox()
        self.thread_count.setRange(1, 64)
        self.thread_count.setValue(12)
        thread_layout.addWidget(self.thread_count)
        layout.addLayout(thread_layout)

        self.start_btn = QPushButton("开始转换")
        self.start_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.start_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)
        self.input_folder = os.path.join(os.getcwd(), "audio")
        
        sys.stdout = EmittingStream(text_edit=self.log_output)
        sys.stderr = EmittingStream(text_edit=self.log_output)

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入文件夹", os.getcwd())
        if folder:
            self.input_folder = folder
            self.input_label.setText(f"输入文件夹: {folder}")

    def start_conversion(self):
        sample_rate_text = self.sample_rate_input.text().strip()
        if not sample_rate_text.isdigit():
            print("采样率格式错误，请输入数字。")
            return

        sample_rate = int(sample_rate_text)
        max_workers = self.thread_count.value()
        output_folder = os.path.join(os.getcwd(), f"output/{sample_rate}")
        ffmpeg_path = FFMPEG_PATH

        print(f"开始转换，采样率：{sample_rate}，线程数：{max_workers}")
        threading.Thread(
            target=self.convert_ogg_to_wav,
            args=(self.input_folder, output_folder, ffmpeg_path, sample_rate, max_workers),
            daemon=True
        ).start()

    def convert_ogg_to_wav(self, input_folder, output_folder, ffmpeg_path, sample_rate, max_workers):
        failed_files = []

        def walk_subfolders(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(".ogg"):
                        yield os.path.join(root, file)

        def convert_file(input_path, output_path):
            try:
                flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                subprocess.run(
                    [ffmpeg_path, '-i', input_path, '-ar', str(sample_rate), output_path],
                    check=True,
                    creationflags=flags
                )
                print(f"转换成功: {output_path}")
            except subprocess.CalledProcessError:
                failed_files.append(input_path)
                print(f"转换失败: {input_path}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for input_path in walk_subfolders(input_folder):
                rel_path = os.path.relpath(input_path, input_folder)
                output_path = os.path.join(output_folder, rel_path).replace(".ogg", ".wav")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                if not os.path.exists(output_path):
                    futures.append(executor.submit(convert_file, input_path, output_path))

            for f in futures:
                f.result()

        if failed_files:
            fail_path = os.path.join(output_folder, 'failed_files.txt')
            with open(fail_path, 'w', encoding='utf-8') as f:
                for file in failed_files:
                    f.write(f"{file}\n")
            print("部分文件转换失败，详情见 failed_files.txt")

        print("所有转换任务完成！")

if __name__ == "__main__":
    app = QApplication([])
    win = AudioConverter()
    win.show()
    app.exec()
