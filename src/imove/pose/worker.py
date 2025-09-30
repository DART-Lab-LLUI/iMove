import subprocess
from pathlib import Path
import sys
import os
import shlex
from viztracer import get_tracer
from ..multilogging import logger

from PySide6.QtCore import  Slot, QObject, QThread, Signal

class PoseWorker(QObject):
    
    finished = Signal()

    def __init__(self, exec_thread: QThread, parent=None):
        super().__init__(parent=parent)
        self.is_finished = False
        self.exec_thread: QThread = exec_thread

        self.exec_thread.started.connect(self.run)
        self.finished.connect(self.exec_thread.quit)
        self.finished.connect(self.deleteLater)
        self.exec_thread.finished.connect(self.exec_thread.deleteLater)


    @Slot()
    def run(self):
        from ..context import ctx
        bids_root = ctx.projectManager.openedProjectPath
        subject_id = ctx.projectManager.selectedSubject
        session_id = ctx.projectManager.selectedSession
        calib_path = ctx.projectManager.selectedCalibration
        logger.debug(f'Initialized pose worker.')
        self.finish()
        
    @Slot()
    def finish(self):
        logger.debug(f'Deinitialized pose worker.')
        self.finished.emit()
        self.is_finished = True
        


class MetricsWorker(QObject):
    
    finished = Signal()
    metricsCreated = Signal(str, dict)

    def __init__(self, exec_thread: QThread, parent=None):
        super().__init__(parent=parent)
        self.is_finished = False
        self.exec_thread: QThread = exec_thread

        self.exec_thread.started.connect(self.run)
        self.finished.connect(self.exec_thread.quit)
        self.finished.connect(self.deleteLater)
        self.exec_thread.finished.connect(self.exec_thread.deleteLater)


    @Slot()
    def run(self):
        from ..context import ctx
        subject_id = ctx.projectManager.selectedSubject
        session_id = ctx.projectManager.selectedSession
        self.finish()
        
    @Slot()
    def finish(self):
        logger.debug(f'Deinitialized metrics worker.')
        self.finished.emit()
        self.is_finished = True
