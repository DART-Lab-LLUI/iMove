from enum import Enum
import time
from multiprocessing import Condition, Value
from PySide6.QtWidgets import QApplication

from PySide6.QtQml import QmlElement, QmlSingleton
from PySide6.QtCore import Property, QEnum, Signal, QObject, Slot


from .sensor.manager import SensorManager
from .project import ProjectManager
from .pose.manager import PoseManager
from .camera.calibration import CalibrationManager
from .camera.manager import CameraManager
from .camera.utils import RecordingState
from .multilogging import logger


QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
@QmlSingleton
class Context(QObject):
    
    contexChanaged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._sensor_manager: SensorManager
        self._camera_manager: CameraManager
        self._project_manager: ProjectManager
        self._pose_manager: PoseManager
        self._calibration_manager: CalibrationManager
        self.app: QApplication | None = None
        self.initialize()
        

    @Property(SensorManager, notify=contexChanaged)
    def sensorManager(self):
        return self._sensor_manager
        
    @Property(CameraManager, notify=contexChanaged)
    def cameraManager(self):
        return self._camera_manager

    @Property(ProjectManager, notify=contexChanaged)
    def projectManager(self):
        return self._project_manager

    @Property(CalibrationManager, notify=contexChanaged)
    def calibrationManager(self):
        return self._calibration_manager

    @Property(PoseManager, notify=contexChanaged)
    def poseManager(self):
        return self._pose_manager

    @Slot()
    def exit(self):
        if self.app is not None:
            logger.debug("Exiting the app.")
            self._sensor_manager.finish()
            self.app.exit()

    def reset(self):
        logger.debug("Reset context.")

    def initialize(self):
        logger.debug("Initialized the context.")
        self._sensor_manager = SensorManager()
        self._camera_manager = CameraManager()
        self._project_manager = ProjectManager()
        self._calibration_manager = CalibrationManager()
        self._pose_manager = PoseManager()

# Injected after the QML engine has been started.
ctx: Context | None = None