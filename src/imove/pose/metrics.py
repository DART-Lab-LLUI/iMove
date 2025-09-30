from os import stat
from ..multilogging import logger
import pandas as pd
from viztracer import get_tracer

from PySide6.QtCore import  QEnum, Slot, QObject, QThread, Property, Signal
from PySide6.QtQml import QmlElement

from ..config import CONFIG

QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

class MetricsHandle(QObject):
    
    metricsChanged = Signal()
    
    def __init__(self, title: str, subplots: dict[str, str], parent=None):
        super().__init__(parent=parent)
        self._title = title
        self.subplots = subplots
        
    @Property(list, notify=metricsChanged)
    def subplotNames(self):
        return list(self.subplots.keys())
    
    @Property(str, notify=metricsChanged)
    def title(self):
        return MetricsHandle.capitalize_parts(self._title)
    
    @Slot(str, result=str)
    def getSubplot(self, name: str):
        return "file://" + self.subplots[name]

    @staticmethod
    def capitalize_parts(s: str):
        parts = s.split('_')
        capitalized_parts = [part.capitalize() for part in parts]
        return ' '.join(capitalized_parts)
