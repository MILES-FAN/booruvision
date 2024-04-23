from PIL import ImageGrab, Image
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QCloseEvent, QPixmap, QClipboard, QImage, QIcon
from PyQt5.QtCore import Qt, QTimer
from wd_tagger import wd_tagger
from PyQt5.QtWidgets import QFileDialog
import configparser
import os
import platform
import time
from hotkey import QtKeyBinder, PynputKeyBinder, KeyBinderBase

platform_system = platform.system()

def QImage_to_PIL(qimage):
    qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)
    # swap R and B channels
    qimage = qimage.rgbSwapped()
    data = qimage.bits().asstring(qimage.byteCount())
    pilimage = Image.frombuffer("RGBA", (qimage.width(), qimage.height()), data, 'raw', "RGBA", 0, 1)
    return pilimage

class TagDisplay(QWidget):
    def __init__(self, tags, parent=None):
        super().__init__()
        self.setWindowTitle("Image Tags")
        self.setGeometry(100, 100, self.calc_size(400, 600)[0], self.calc_size(400, 600)[1])
        self.tags = tags
        self.formated_tags = tags
        self.parent = parent
        self.parent.readConfig()
        self.tag_format = self.parent.tag_format
        self.initUI(tags)
    
    def get_scale(self):
        ref_width = 1920
        ref_height = 1080
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        scale = min(screen_size.width() / ref_width, screen_size.height() / ref_height)
        return scale
    
    def calc_size(self, width, height):
        scale = self.get_scale()
        width = int(width * scale)
        height = int(height * scale)
        return width, height

    def initUI(self, tags):
        layout = QVBoxLayout()
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Tag", "Confidence"])
        for tag, confidence in tags.items():
            rowPosition = table.rowCount()
            table.insertRow(rowPosition)

            # Convert tag and confidence to string before passing to QTableWidgetItem
            table.setItem(rowPosition, 0, QTableWidgetItem(str(tag)))
            table.setItem(rowPosition, 1, QTableWidgetItem(str(confidence)))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        copyToClipboardButton = QPushButton("Copy tags to clipboard")
        copyToClipboardButton.clicked.connect(self.copyToClipboard)
        layout.addWidget(copyToClipboardButton)

        self.formatLabel = QLabel("Tag format:")
        self.formatDropdown = QComboBox()
        self.formatDropdown.addItem("Booru")
        self.formatDropdown.addItem("Stable Diffusion")
        for i in range(self.formatDropdown.count()):
            if self.formatDropdown.itemText(i) == self.tag_format:
                self.formatDropdown.setCurrentIndex(i)
                break
        self.formatDropdown.currentIndexChanged.connect(self.changeTagFormat)
        self.changeTagFormat()
        layout.addWidget(self.formatLabel)
        layout.addWidget(self.formatDropdown)

        self.setLayout(layout)

    def changeTagFormat(self):
        self.tag_format = self.formatDropdown.currentText()
        print(f"Tag format changed to {self.tag_format}")
        if self.tag_format == "Booru":
            print("Booru format selected")
            self.formated_tags = self.tags
        elif self.tag_format == "Stable Diffusion":
            print("Stable Diffusion format selected")
            formatted_tags = {}
            for tag, confidence in self.tags.items():
                tag = tag.replace("_", " ").replace("(", r"\(").replace(")", r"\)")
                formatted_tags[tag] = confidence
            self.formated_tags = formatted_tags
        
        self.parent.saveConfig()

    def copyToClipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.getTagString())

    def getTagString(self):
        tagString = ""
        tagString = ", ".join([f"{tag}" for tag, confidence in self.formated_tags.items()])
        return tagString

class ImageInterrogator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icon.png"))
        self.windowTittle = "Image Interrogator"
        self.setWindowTitle(self.windowTittle)
        self.setGeometry(100, 100, self.calc_size(800, 600)[0], self.calc_size(800, 600)[1])
        self.tagger = wd_tagger()
        self.tagDisplay = None
        self.tag_format = "booru"
        self.currentKeybind = "Ctrl+Shift+I"
        self.modelName = "wd-swinv2-v3"
        self.threshold = 0.35
        self.taskQueue = []
        self.taskTimer = QTimer()
        self.taskTimer.timeout.connect(self.dealWithQueue)
        self.taskTimer.setInterval(50)
        self.taskTimer.start()
        self.readConfig()
        if platform_system != "Darwin":
            self.keybinder = QtKeyBinder(self.winId())
        else:
            self.keybinder = PynputKeyBinder()
        self.keybinder.register_hotkey(self.currentKeybind, self.addFastAnalyzeToQueue)
        self.initUI()
    
    def saveConfig(self):
        print("Saving config...")
        try:
            config = configparser.ConfigParser()
            config["GUI"] = {
                "shortcut": self.currentKeybind,
                "unload_model_when_done": self.tagger.unloadAfterAnalysis,
                "tag_format": self.tag_format
            }
            config["Tagger"] = {
                "model": self.modelName,
                "threshold": self.threshold
            }
            if self.tagDisplay:
                config["GUI"]["tag_format"] = self.tagDisplay.tag_format
            with open("config.ini", "w") as configfile:
                config.write(configfile)
        except Exception as e:
            print("Error saving config file")
            raise e

    def readConfig(self):
        try:
            if not os.path.exists("config.ini"):
                self.saveConfig()
            config = configparser.ConfigParser()
            config.read("config.ini")
            self.currentKeybind = config["GUI"]["shortcut"]
            self.tagger.unloadAfterAnalysis = config["GUI"].getboolean("unload_model_when_done")
            self.tag_format = config["GUI"]["tag_format"]
            self.modelName = config["Tagger"]["model"]
            self.threshold = float(config["Tagger"]["threshold"])
            self.tagger.set_threshold_and_model(self.threshold, self.modelName)
        except Exception as e:
            print("Error reading config file")
            self.saveConfig()

    def get_scale(self):
        ref_width = 1920
        ref_height = 1080
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        scale = min(screen_size.width() / ref_width, screen_size.height() / ref_height)
        return scale
    
    def calc_size(self, width, height):
        scale = self.get_scale()
        width = int(width * scale)
        height = int(height * scale)
        return width, height

    def initUI(self):
        # Main layout
        layout = QVBoxLayout()

        layout.setAlignment(Qt.AlignCenter)

        # Image label for displaying the image
        self.imageLabel = QLabel("Image will appear here...")
        self.imageLabel.setFixedSize(self.calc_size(720, 540)[0], self.calc_size(720, 540)[1])
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setStyleSheet("border: 1px solid black;")

        # Button to load image from clipboard
        self.loadImageButton = QPushButton("Load Image from Clipboard")
        self.loadImageButton.clicked.connect(self.loadImageFromClipboard)

        # Button to load image from a file
        self.loadFileButton = QPushButton("Load Image from File")
        self.loadFileButton.clicked.connect(self.loadImageFromFile)

        # Button to analyze the image
        self.analyzeButton = QPushButton("Analyze Image")
        self.analyzeButton.clicked.connect(self.analyzeImage)

        # Checkbox for unload model after every analysis
        self.unloadModelCheckbox = QCheckBox("Unload model after every analysis")
        self.unloadModelCheckbox.setChecked(self.tagger.unloadAfterAnalysis)
        self.unloadModelCheckbox.stateChanged.connect(self.unloadModel)
        self.unloadModel()

        # Dropdown for selecting shortcut combination
        self.shortcutLabel = QLabel("Shortcut:")
        self.shortcutDropdown = QComboBox()
        self.shortcutDropdown.addItem("Ctrl+Shift+I")
        self.shortcutDropdown.addItem("Ctrl+Shift+J")
        self.shortcutDropdown.addItem("Ctrl+Shift+K")
        currentKeybindInList = False
        for i in range(self.shortcutDropdown.count()):
            if self.shortcutDropdown.itemText(i) == self.currentKeybind:
                self.shortcutDropdown.setCurrentIndex(i)
                currentKeybindInList = True
                break
        if not currentKeybindInList:
            self.shortcutDropdown.addItem(self.currentKeybind)
            self.shortcutDropdown.setCurrentIndex(self.shortcutDropdown.count() - 1)
        self.shortcutDropdown.currentIndexChanged.connect(self.changeShortcut)

        # Add widgets to layout
        layout.addWidget(self.imageLabel)
        layout.addWidget(self.loadFileButton)
        layout.addWidget(self.loadImageButton)
        layout.addWidget(self.analyzeButton)
        layout.addWidget(self.unloadModelCheckbox)
        layout.addWidget(self.shortcutLabel)
        layout.addWidget(self.shortcutDropdown)

        # Central widget
        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def changeShortcut(self):
        oldKeybind = self.currentKeybind
        try:
            self.keybinder.unregister_hotkey(self.currentKeybind)
            self.currentKeybind = self.shortcutDropdown.currentText()
            self.keybinder.register_hotkey(self.currentKeybind, self.addFastAnalyzeToQueue)
        except Exception as e:
            print(f"Error changing shortcut keybind: {e}, tring to revert to old keybind")
            self.currentKeybind = oldKeybind
            self.shortcutDropdown.setCurrentText(oldKeybind)
            self.keybinder.register_hotkey(self.currentKeybind, self.addFastAnalyzeToQueue)
            print("Reverted to old keybind")
        self.saveConfig()

    def addFastAnalyzeToQueue(self, Optional=None):
        self.taskQueue.append(self.fastAnalyzeImageFromClipboard)
        if len(self.taskQueue) > 1:
            return
    
    def dealWithQueue(self):
        for task in self.taskQueue:
            task()
        self.taskQueue = []


    def fastAnalyzeImageFromClipboard(self):
        if self.tagDisplay:
            self.tagDisplay.close()
        self.loadImageFromClipboard()
        self.analyzeImage()
        #If window is minimized, restore it
        self.showNormal()
        #bring the main window to the front
        self.activateWindow()
        self.raise_()
        #focus on the tag display window
        self.tagDisplay.activateWindow()
        self.tagDisplay.raise_()

    def loadImageFromClipboard(self):
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if image.isNull() or not image:
            print("Clipboard does not contain an image!")
            return
        pixmap = QPixmap.fromImage(image)
        self.imageLabel.setPixmap(pixmap.scaled(self.imageLabel.width(), self.imageLabel.height(), Qt.KeepAspectRatio))

    def loadImageFromFile(self):
        imagePath, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        try:
            if imagePath:
                pixmap = QPixmap(imagePath)
                self.imageLabel.setPixmap(pixmap.scaled(self.imageLabel.width(), self.imageLabel.height(), Qt.KeepAspectRatio))
        except Exception as e:
            self.imageLabel.setText("Error loading image!")

    def displayResults(self, tags):
        self.tagDisplay = TagDisplay(tags, self)
        self.tagDisplay.show()

    def unloadModel(self):
        if self.unloadModelCheckbox.isChecked():
            self.tagger.unloadAfterAnalysis = True
            self.saveConfig()
        else:
            self.tagger.unloadAfterAnalysis = False
            self.saveConfig()

    def analyzeImage(self):
        # Placeholder for image analysis logic
        print("Analyze the image...")
        self.setWindowTitle(f"{self.windowTittle} - Analyzing...")
        pilimage = QImage_to_PIL(self.imageLabel.pixmap().toImage())
        tags = self.tagger.tag_image_by_pil(pilimage)
        print(tags)
        self.setWindowTitle(f"{self.windowTittle}")
        self.displayResults(tags)
        return tags

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = ImageInterrogator()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
        with open(f"error_log_{time.time()}.txt", "a+") as f:
            f.write(str(e))

