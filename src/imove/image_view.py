import cv2 as cv
from PySide6.QtCore import Property, Signal, Qt, Slot
from PySide6.QtGui import QImage
from PySide6.QtQml import QmlElement
from PySide6.QtQuick import QQuickPaintedItem
from .multilogging import logger

QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class ImageView(QQuickPaintedItem):
    imageChanged = Signal()

    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)
        self._image = QImage()

    def paint(self, painter):
        if not self._image.isNull():
            painter.drawImage(0, 0, self._image.scaled(self.size().toSize(), aspectMode=Qt.AspectRatioMode.KeepAspectRatio))

    @Property(QImage, notify=imageChanged)
    def image(self):
        return self._image

    @image.setter
    def image(self, new_image: QImage):
        self._image = new_image
        self.imageChanged.emit()
        self.update()
        
    @Slot(QImage)
    def setImage(self, new_image: QImage):
        self.image = new_image