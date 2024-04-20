from PIL import ImageGrab, Image
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QCloseEvent, QPixmap, QClipboard, QImage
from PyQt5.QtCore import Qt, QAbstractNativeEventFilter, QAbstractEventDispatcher
from wd_tagger import wd_tagger
from PyQt5.QtWidgets import QFileDialog
from typing import Callable, Optional
from pyqtkeybind import keybinder
from requests import get

def QImage_to_PIL(qimage):
    qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)
    data = qimage.bits().asstring(qimage.byteCount())
    pilimage = Image.frombuffer("RGBA", (qimage.width(), qimage.height()), data, 'raw', "RGBA", 0, 1)
    return pilimage

class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


class EventDispatcher:
    """Install a native event filter to receive events from the OS"""

    def __init__(self, keybinder) -> None:
        self.win_event_filter = WinEventFilter(keybinder)
        self.event_dispatcher = QAbstractEventDispatcher.instance()
        self.event_dispatcher.installNativeEventFilter(self.win_event_filter)

class QtKeyBinder:
    def __init__(self, win_id: Optional[int]) -> None:
        keybinder.init()
        self.win_id = win_id

        self.event_dispatcher = EventDispatcher(keybinder=keybinder)

    def register_hotkey(self, hotkey: str, callback: Callable) -> None:
        keybinder.register_hotkey(self.win_id, hotkey, callback)

    def unregister_hotkey(self, hotkey: str) -> None:
        keybinder.unregister_hotkey(self.win_id, hotkey)

class TagDisplay(QWidget):
    def __init__(self, tags):
        super().__init__()

        self.setWindowTitle("Image Tags")
        self.setGeometry(100, 100, self.calc_size(400, 600)[0], self.calc_size(400, 600)[1])
        self.tags = tags
        self.formated_tags = tags
        self.tag_format = "booru"
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

        self.formatDropdown = QComboBox()
        self.formatDropdown.addItem("Booru")
        self.formatDropdown.addItem("Stable Diffusion")
        self.formatDropdown.currentIndexChanged.connect(self.changeTagFormat)
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

        self.setWindowTitle("Image Interrogator")
        self.setGeometry(100, 100, self.calc_size(800, 600)[0], self.calc_size(800, 600)[1])
        self.tagger = wd_tagger()
        self.tagDisplay = None
        self.currentKeybind = "Ctrl+Shift+I"
        self.keybinder = QtKeyBinder(self.winId())
        self.keybinder.register_hotkey(self.currentKeybind, self.fastAnalyzeImageFromClipboard)
        self.initUI()
    
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
        self.unloadModelCheckbox.stateChanged.connect(self.unloadModel)

        # Dropdown for selecting shortcut combination
        self.shortcutDropdown = QComboBox()
        self.shortcutDropdown.addItem("Ctrl+Shift+I")
        self.shortcutDropdown.addItem("Ctrl+Shift+J")
        self.shortcutDropdown.addItem("Ctrl+Shift+K")
        self.shortcutDropdown.currentIndexChanged.connect(self.changeShortcut)

        # Add widgets to layout
        layout.addWidget(self.imageLabel)
        layout.addWidget(self.loadFileButton)
        layout.addWidget(self.loadImageButton)
        layout.addWidget(self.analyzeButton)
        layout.addWidget(self.unloadModelCheckbox)
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
            self.keybinder.register_hotkey(self.currentKeybind, self.fastAnalyzeImageFromClipboard)
        except Exception as e:
            self.currentKeybind = oldKeybind
            self.shortcutDropdown.setCurrentText(oldKeybind)
            self.keybinder.register_hotkey(self.currentKeybind, self.fastAnalyzeImageFromClipboard)
            print("Error changing shortcut keybind")

    def fastAnalyzeImageFromClipboard(self):
        if self.tagDisplay:
            self.tagDisplay.close()
        self.loadImageFromClipboard()
        self.analyzeImage()
        #If window is minimized, restore it
        self.showNormal()
        #bring the main window to the front
        self.activateWindow()
        #focus on the tag display window
        self.tagDisplay.activateWindow()

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
        self.tagDisplay = TagDisplay(tags)
        self.tagDisplay.show()

    def unloadModel(self):
        if self.unloadModelCheckbox.isChecked():
            self.tagger.unloadAfterAnalysis = True
        else:
            self.tagger.unloadAfterAnalysis = False

    def analyzeImage(self):
        # Placeholder for image analysis logic
        print("Analyze the image...")
        pilimage = QImage_to_PIL(self.imageLabel.pixmap().toImage())
        tags = self.tagger.tag_image_by_pil(pilimage)
        print(tags)
        self.displayResults(tags)
        return tags

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageInterrogator()
    window.show()
    sys.exit(app.exec_())
