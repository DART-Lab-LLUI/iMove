from PySide6.QtGui import QImage


from typing import Any
import numpy as np
from viztracer import get_tracer

from PySide6.QtCore import  Slot, QObject, QThread, Property, Signal
from PySide6.QtMultimedia import QCameraDevice, QCamera, QCameraFormat

from ..multilogging import logger
from ..config import CONFIG
from .worker import CameraWorker
from .utils import CameraDescription, RecordingDescription


QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

class CameraHandle(QObject):

    deviceChanged = Signal()
    connectedChanged = Signal()
    idxChanged = Signal()
    
    streamingChanged = Signal()
    streamingStopped = Signal()

    def __init__(self, camera: QCamera,  connected: bool = False, parent: QObject | None = None):
        super().__init__(parent=parent)
        self._camera: QCamera = camera
        self._connected: bool = connected
        self._is_streaming = False
        self._idx: int = -1
        self._valid_formats = [fmt for fmt in self._camera.cameraDevice().videoFormats() if fmt.resolution().height() >= CONFIG.MIN_CAMERA_HEIGHT and fmt.resolution().width() >= CONFIG.MIN_CAMERA_WIDTH and fmt.maxFrameRate() >= CONFIG.MIN_CAMERA_FPS and fmt.pixelFormat() in CONFIG.CAMERA_PIXELFORMATS]

        self.worker: CameraWorker | None = None
        self._video_sink = None

    @Slot()
    def setVideoFrame(self, vf: QImage):
        if self._video_sink is not None:
            self._video_sink.image = vf
            
    @Slot()
    def startStreaming(self, rec_desc: RecordingDescription):
        self.streaming = True

        self.worker = CameraWorker(self.description, rec_desc, exec_thread=QThread(self))
        self.worker.moveToThread(self.worker.exec_thread)
     
        self.worker.frameProcessed.connect(self.setVideoFrame)
        self.streamingStopped.connect(self.worker.finish)
        
        self.worker.exec_thread.start()
        
    @Slot()
    def stopStreaming(self):
        self.streaming = False
        logger.debug(f'Stopped stream on camera {self.id}.')
        self.streamingStopped.emit()
        
    @Property(bool, notify=streamingChanged)
    def streaming(self) -> bool :
        return self._is_streaming
    @streaming.setter
    def streaming(self, new_val: bool):
        self._is_streaming = new_val
        self.streamingChanged.emit()
                
    @Property('QVariant', notify=deviceChanged)
    def device(self) -> QCameraDevice:
        return self._camera.cameraDevice()

    @Property('QVariant', notify=deviceChanged)
    def videoSink(self):
        return self._video_sink
    @videoSink.setter
    def videoSink(self, new_val):
        self._video_sink = new_val
        self.deviceChanged.emit()

    @Property('QVariant', notify=deviceChanged)
    def camera(self):
        return self._camera

    @Property('QVariant', notify=deviceChanged)
    def cameraFormat(self):
        return self._camera.cameraFormat()
    @cameraFormat.setter
    def cameraFormat(self, format: QCameraFormat):
        self._camera.setCameraFormat(format)
        self.deviceChanged.emit()

    @Property('QVariant', notify=deviceChanged)
    def cameraFormats(self):
        return self._valid_formats

    @Property('QVariant', notify=deviceChanged)
    def cameraFormatsString(self):
        return [f'{fmt.resolution().width()} x {fmt.resolution().height()}, \n{fmt.minFrameRate()}-{fmt.maxFrameRate()} fps, {fmt.pixelFormat().name.replace("Format_", "", 1)}' for fmt in self._valid_formats]

    @Property('QVariant', notify=deviceChanged)
    def fps(self):
        return self._camera.cameraFormat().maxFrameRate()

    @Property('QVariant', notify=deviceChanged)
    def pixelFormat(self):
        return self._camera.cameraFormat().pixelFormat().name.replace("Format_", "", 1)

    @Property('QVariant', notify=deviceChanged)
    def width(self):
        return self._camera.cameraFormat().resolution().width()

    @Property('QVariant', notify=deviceChanged)
    def height(self):
        return self._camera.cameraFormat().resolution().height()
    
    @Property(str, notify=deviceChanged)
    def name(self):
        return self.device.description()

    @Property(str, notify=deviceChanged)
    def id(self):
        return self.device.id().data().decode('utf-8')

    @Property(int, notify=deviceChanged)
    def channels(self):
        return 3

    @Property(Any, notify=deviceChanged)
    def dtype(self):
        return np.dtype(np.uint8)
    
    @property
    def description(self):
        return CameraDescription(id=self.id, idx=self.idx, width=self.width, height=self.height, channels=self.channels, fps=self.fps, dtype=self.dtype)

    @Property(int, notify=idxChanged)
    def idx(self):
        return self._idx
    @idx.setter
    def idx(self, new_val):
        if self.idx != -1 and new_val != -1:
            from ..context import ctx
            ctx.cameraManager.reassignCameraIdx(self.idx, new_val)
        self._idx = new_val
        self.idxChanged.emit()
        
    
    @Property(bool, notify=connectedChanged)
    def connected(self):
        return self._connected
    @connected.setter
    def connected(self, new_value):
        self._connected = new_value
        from ..context import ctx
        if self._connected:
            self.idx = ctx.cameraManager.nextCameraIdx()
        else:
            ctx.cameraManager.removeCameraIdx(self.idx)
            self.idx = -1
        self.connectedChanged.emit()
        
    def __del__(self):
        logger.debug(f'Camera Item {self.id} is being destroyed.')
