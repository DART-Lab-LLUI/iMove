from viztracer import get_tracer

from PySide6.QtCore import  Slot, QObject, QThread, Property, Signal
from PySide6.QtQml import QmlElement

from .worker import MetricsWorker, PoseWorker
from .metrics import MetricsHandle
from ..multilogging import logger

QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class PoseManager(QObject):
    estimatingChanged = Signal()
    plotsChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._is_estimating = False
        self._plots_db: list[MetricsHandle] = []
        
    @Slot()
    def startEstimation(self):
        self.isEstimating = True
        self.estimator = PoseWorker(QThread(self))
        self.estimator.moveToThread(self.estimator.exec_thread)
        self.estimator.finished.connect(self.estimationFinished)
        self.estimator.exec_thread.start()

    @Slot()
    def plotMetrics(self):
        self.plots = []
        self.plotter = MetricsWorker(QThread(self))
        self.plotter.moveToThread(self.plotter.exec_thread)
        self.plotter.metricsCreated.connect(self.addPlot)
        self.plotter.exec_thread.start()
        
    @Slot(str, dict)
    def addPlot(self, title: str, subplots: dict[str, str]):
        self._plots_db.append(MetricsHandle(title, subplots))
        self.plotsChanged.emit()
    
    @Slot()
    def estimationFinished(self):
        self.isEstimating = False 
        self.plotMetrics()

    @Property(bool, notify=estimatingChanged)
    def isEstimating(self):
        return self._is_estimating
    @isEstimating.setter
    def isEstimating(self, new_val: bool):
        self._is_estimating = new_val
        self.estimatingChanged.emit()

    @Property("QVariant", notify=plotsChanged)
    def plots(self):
        return self._plots_db
    @plots.setter
    def plots(self, new_plot: list[MetricsHandle]):
        self._plots_db = new_plot
        self.plotsChanged.emit()
