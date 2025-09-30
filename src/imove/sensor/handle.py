from typing import Dict
from dataclasses import dataclass, field, asdict
from typing import ClassVar
import struct
from viztracer import get_tracer

from PySide6.QtCore import Slot, QObject, QThread, Property, Signal, QByteArray
from PySide6.QtQml import QmlElement
from PySide6.QtBluetooth import QBluetoothDeviceInfo

from ..config import CONFIG
from .worker import SensorWorker
from ..camera.utils import RecordingDescription
from .utils import SensorDescription
from ..multilogging import logger


QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

class SensorHandle(QObject):

    deviceChanged = Signal()
    connectedChanged = Signal()
    streamingChanged = Signal()

    identifyRequested = Signal()
    shutdownRequested = Signal()
    tagRenameRequested = Signal(str)
    disconnectRequested = Signal()
    startStreamingRequested = Signal(SensorDescription, RecordingDescription)
    stopStreamingRequested = Signal()
    measurementChanged = Signal(dict)
    
    def __init__(self, device: QBluetoothDeviceInfo, parent = None):
        super().__init__(parent=parent)
        self._device = device
        self._battery_level: int = 0
        self._tag: str = ""
        self._firmware_version: str = ""
        self._connected: bool = False
        self._is_streaming = False

        self.sensorWorker: SensorWorker | None = None

    @Slot()
    def connectToSensor(self):
        logger.debug(f'Connecting to sensor with address {self.address}')
        self.sensorWorker = SensorWorker(self.description, QThread(parent=self))
        self.sensorWorker.moveToThread(self.sensorWorker.exec_thread)

        self.sensorWorker.batteryChanged.connect(self.setBatteryLevel)
        self.sensorWorker.firmwareVersionChanged.connect(self.setFirmwareVersion)
        self.sensorWorker.tagChanged.connect(self.setTag)
        self.sensorWorker.connectedChanged.connect(self.setConnected)
        self.sensorWorker.measurementChanged.connect(self.measurementChanged)
        
        self.identifyRequested.connect(self.sensorWorker.identifySensor)
        self.tagRenameRequested.connect(self.sensorWorker.renameTag)
        self.shutdownRequested.connect(self.sensorWorker.shutdownSensor)
        self.disconnectRequested.connect(self.sensorWorker.disconnectSensor)
        self.startStreamingRequested.connect(self.sensorWorker.startStreaming)
        self.stopStreamingRequested.connect(self.sensorWorker.stopStreaming)

        self.disconnectRequested.connect(self.stopStreaming)

        self.sensorWorker.exec_thread.start()
        
    @Slot()
    def startStreaming(self, rec_desc: RecordingDescription):
        self.streaming = True
        self.startStreamingRequested.emit(self.description, rec_desc)

    @Slot()
    def stopStreaming(self):
        if self.streaming:
            self.streaming = False
            self.stopStreamingRequested.emit()

    @Property(QBluetoothDeviceInfo, notify=deviceChanged)
    def device(self):
        return self._device
    @device.setter
    def device(self, new_val):
        self._device = new_val
        self.deviceChanged.emit()

    @Property(str, notify=deviceChanged)
    def name(self):
        return self._device.name()

    @Property(str, notify=deviceChanged)
    def address(self):
        return self._device.address().toString()

    @Property(str, notify=deviceChanged)
    def uuid(self):
        return self._device.deviceUuid().toString()

    @Property(str, notify=deviceChanged)
    def classOfDevice(self):
        return  (self._device.serviceClasses().value << 13) | (self._device.majorDeviceClass().value << 8) | (self._device.minorDeviceClass() << 2)

    @Property(int, notify=deviceChanged)
    def batteryLevel(self):
        return self._battery_level
    @batteryLevel.setter
    def batteryLevel(self, new_value: int):
        self._battery_level = new_value
        self.deviceChanged.emit()
    @Slot(int)
    def setBatteryLevel(self, new_value: int):
        self.batteryLevel = new_value

    @Property(int, notify=deviceChanged)
    def signalStrength(self):
        return self._device.rssi()

    @Property(str, notify=deviceChanged)
    def tag(self):
        return self._tag
    @tag.setter
    def tag(self, new_value):
        self._tag = new_value
        self.deviceChanged.emit()
    @Slot(str)
    def setTag(self, new_value):
        self.tag = new_value

    @Property(str, notify=deviceChanged)
    def firmwareVersion(self):
        return self._firmware_version
    @firmwareVersion.setter
    def firmwareVersion(self, new_value):
        self._firmware_version = new_value
        self.deviceChanged.emit()
    @Slot(str)
    def setFirmwareVersion(self, new_value):
        self.firmwareVersion = new_value

    @Property(bool, notify=connectedChanged)
    def connected(self):
        return self._connected
    @connected.setter
    def connected(self, new_value):
        self._connected = new_value
        self.connectedChanged.emit()
        self.deviceChanged.emit()
    @Slot(bool)
    def setConnected(self, new_value):
        self.connected = new_value

    @Property(bool, notify=streamingChanged)
    def streaming(self) -> bool :
        return self._is_streaming
    @streaming.setter
    def streaming(self, new_val: bool):
        self._is_streaming = new_val
        self.streamingChanged.emit()

    @property
    def description(self):
        return SensorDescription(self.name, self.address, self.uuid, self.classOfDevice, self.tag)
