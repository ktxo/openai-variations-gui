import json
import os
import shutil
import sys
import openai
import requests
from urllib.parse import urlparse, unquote

_about = {
    "version": "1.0.0", "author": "ktxo", "date": "2023-06-14",
    "url": "https://github.com/ktxo/openai-variations-gui",
}
REFERENCES = {
    "OpenAI Image variation": "https://platform.openai.com/docs/guides/images/variations",
    "OpenAI Image variation API" : "https://platform.openai.com/docs/api-reference/images/create-variation"
}
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFileDialog,
    QFormLayout, QVBoxLayout, QHBoxLayout,
    QStatusBar,
    QRadioButton,
    QLabel, QLineEdit, QSpinBox, QMessageBox, QPushButton
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt



def resource_path(resource_path):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, resource_path)
    else:
        return resource_path


openai.api_key = None
# ----------------------------------------------------------------------------
def create_variation(filename, num=3, size="256x256", prefix=""):
    response = openai.Image.create_variation(
        image=open(filename, "rb"),
        size=size,
        n=num
    )
    if prefix:
        prefix = f"_{prefix}"
    filename,_ = os.path.splitext(os.path.basename(filename))
    response_json = os.path.join("variations", f"{filename}{prefix}.json")
    with open(response_json, "w") as fd:
        json.dump(response, fp=fd, indent=4)
    if prefix:
        prefix = f"_{prefix}"
    save_images(response, filename, prefix)
    return response, response_json


def save_images( response, filename:str, prefix=""):
  for data in response['data']:
    response = requests.get(data["url"], stream=True, timeout=120)
    if response.status_code == 200:
      filename_ = os.path.join("variations", f"{filename}{prefix}_{urlparse(data['url']).path.split('/')[-1]}")
      with open(filename_, 'wb') as f:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, f)

# ----------------------------------------------------------------------------
def load_config():
    try:
        with open("config.json", "r") as fd:
            return json.load(fd)
    except:
        return {}

def save_config(config):
    try:
        with open("config.json", "w") as fd:
            return json.dump(config, fd, indent=4)
    except:
        pass

# ----------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = load_config()
        os.makedirs("variations", exist_ok=True)
        self.cwd = os.getcwd()
        openai.api_key = self.config.get("api_key", None)

        self.setWindowTitle('OpenAI GUI')
        self.setWindowIcon(QIcon(resource_path("images/logo.ico")))
        self.setFixedSize(600,450)

        self.txt_api_key = QLineEdit()
        self.txt_api_key.setText(self.config.get("api_key", None))
        self.txt_api_key.setToolTip("OpenAI api key (see OpenAI)")

        self.txt_filename = QLineEdit()
        self.txt_filename.setReadOnly(True)
        self.txt_prefix = QLineEdit()
        self.txt_prefix.setToolTip("Prefix to add to image filenames, e.g.: mydrawing")

        self.sp_num = QSpinBox()
        self.sp_num.setMinimum(1)
        self.sp_num.setMaximum(10)
        self.sp_num.setValue(3)
        self.sp_num.setToolTip("The number of images to generate (see OpenAI)")

        self.rd_256 = QRadioButton("&256x256")
        self.rd_256.setToolTip("The size of the generated images (see OpenAI)")
        self.rd_256.setChecked(True)
        self.rd_512 = QRadioButton("&512x512")
        self.rd_512.setToolTip("The size of the generated images (see OpenAI)")
        self.rd_1024 = QRadioButton("&1024x1024")
        self.rd_1024.setToolTip("The size of the generated images (see OpenAI)")

        bt1 = QPushButton('&Select image')
        bt1.setToolTip("The image to use as the basis for the variation(s). \nMust be a valid PNG file, less than 4MB, and square (see OpenAI)")
        bt1.clicked.connect(self.open_file_dialog)

        bt2 = QPushButton('&Execute')
        bt2.setToolTip("Execute OpenAI variation API and get the images")
        bt2.clicked.connect(self.execute)

        bt3 = QPushButton('&About')
        bt3.setToolTip("About this program")
        bt3.clicked.connect(self.about)

        self.lbl_image = QLabel("Select an image first")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_image.setScaledContents(True)
        self.lbl_image.setStyleSheet("border: 1px solid black;")
        self.lbl_image.setFixedWidth(200)
        self.lbl_image.setFixedHeight(200)

        # Layouts
        # -- Form
        self.size_layout = QHBoxLayout()
        self.size_layout.addWidget(self.rd_256)
        self.size_layout.addWidget(self.rd_512)
        self.size_layout.addWidget(self.rd_1024)

        self.form = QFormLayout()
        self.form.addRow(QLabel("OpenAI Api Key"), self.txt_api_key)
        self.form.addRow(QLabel("Num of variation"), self.sp_num)
        self.form.addRow(QLabel("Image prefix"), self.txt_prefix)
        self.form.addRow(QLabel("Image Size"), self.size_layout)
        self.form.addRow(QLabel("Image filename"), self.txt_filename)


        # -- Buttons
        self.bt_layout = QHBoxLayout()
        self.bt_layout.addStretch()
        self.bt_layout.addWidget(bt1, Qt.AlignmentFlag.AlignCenter)
        self.bt_layout.addWidget(bt2, Qt.AlignmentFlag.AlignCenter)
        self.bt_layout.addWidget(bt3, Qt.AlignmentFlag.AlignCenter)
        self.form.addRow("", QLabel())

        # -- Botton Layout
        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.addLayout(self.bt_layout)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.lbl_image, alignment=Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addLayout(self.form)
        layout.addLayout(self.bottom_layout)
        layout.addStretch()

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.show()

    def about(self):
        msg = QMessageBox()
        msg.setFixedSize(1500,1500)
        msg.setWindowTitle("Basic GUI to use OpenAI" + " " * 100) # I need a wider MeesageBox
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setInformativeText(f"v{_about['version']} ({_about['date']})")
        msg.setDetailedText("\n".join([f"{k}={v}" for k,v in _about.items()]
                                      + ["\nSome references\n"]
                                      + list(REFERENCES.values())))
        msg.exec()

    def _show_image(self, filename):
        self.lbl_image.setPixmap(QPixmap(filename))

    def open_file_dialog(self):
        self.status_bar.showMessage("")
        dialog = QFileDialog(self)
        dialog.setDirectory(os.getcwd())
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("PNG Files (*.png)")
        dialog.setViewMode(QFileDialog.ViewMode.List)
        if dialog.exec():
            filename = dialog.selectedFiles()
            if filename:
                self.txt_filename.setText(filename[0])
                self._show_image(filename[0])

    def execute(self):
        if self.txt_api_key.text().strip() == "":
            self.status_bar.showMessage(f"OpenAI api key empty :-(")
            return
        if self.txt_filename.text().strip() == "":
            self.status_bar.showMessage(f"Choose an image first :-(")
            return
        self.config = {"api_key" : self.txt_api_key.text().strip()}
        save_config(self.config)

        try:
            openai.api_key = self.txt_api_key.text().strip()
            if self.rd_256.isChecked():
                size_ = "256x256"
            elif self.rd_512.isChecked():
                size_ = "256x256"
            else:
                size_ = "1024x1024"
            res, filename = create_variation(self.txt_filename.text().strip(), self.sp_num.value(), size_, self.txt_prefix.text().strip())
            self.status_bar.showMessage(f"Done, images saved to folder 'variations'")
        except Exception as e:
            self.status_bar.showMessage(f"Got an error: {str(e)}")
            return


# ----------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())