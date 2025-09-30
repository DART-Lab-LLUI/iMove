from dataclasses import asdict
import time
import math
from viztracer import get_tracer

from PySide6.QtCore import QTimer, Slot, QObject, QThread, Property, Signal
from PySide6.QtQml import QmlElement
from PySide6.QtBluetooth import QBluetoothDeviceDiscoveryAgent, QBluetoothDeviceInfo, QBluetoothLocalDevice

from ..config import CONFIG
from .handle import SensorHandle
from ..multilogging import logger
from ..camera.utils import RecordingDescription, RecordingState
from .utils import SensorData


QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class SensorManager(QObject):
    
    devicesChanged = Signal()
    connectedDevicesChanged = Signal()
    scanningChanged = Signal()
    
    scanStarted = Signal()
    scanStopped = Signal()
    refreshStarted = Signal()
    
    recordingStateChanged = Signal(RecordingState)
    streamingChanged = Signal()
    
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        logger.debug(f"Created SensorManager: {id(self)}.")
        self._recording_state = RecordingState.Stopped
        self._is_streaming = False

        self.devices_db: list[SensorHandle] = []
        self.sensor_scanner_worker: SensorScanner
        self.sensor_scanner_initialized = False
        self.is_scanning = False

        self.local_device = QBluetoothLocalDevice()
        self.validate_local_bluetooth_device()
        self.initialize_sensor_scanner()
    
    def initialize_sensor_scanner(self):
        self.sensor_scanner_worker = SensorScanner(self.local_device, QThread(parent=self))
        self.sensor_scanner_worker.moveToThread(self.sensor_scanner_worker.exec_thread)

        self.scanStarted.connect(self.sensor_scanner_worker.startScan)
        self.scanStopped.connect(self.sensor_scanner_worker.stopScan)
        self.refreshStarted.connect(self.sensor_scanner_worker.refresh)

        self.sensor_scanner_worker.sensorDetected.connect(self.addSensor)
        self.sensor_scanner_worker.sensorsCleared.connect(self.clearSensors)
        self.sensor_scanner_worker.scanning.connect(self.changeIsScanning)
        
        self.finished.connect(self.sensor_scanner_worker.finished)

        self.sensor_scanner_worker.exec_thread.start()

    def validate_local_bluetooth_device(self) -> bool:
        if self.local_device.isValid():
            self.local_device.powerOn()
            logger.debug(f"Bluetooth powered on.")

            logger.debug(f"Local Bluetooth device name: {self.local_device.name()}")

            self.local_device.setHostMode(QBluetoothLocalDevice.HostDiscoverable)
            logger.debug(f"Bluetooth device: {self.local_device.name()} is now visible to others.")
            return True
        else:
            logger.error(f"Invalid Bluetooth device.")
            return False

    @Property("QVariant", notify=devicesChanged)
    def devices(self):
        return self.devices_db

    @Property(bool, notify=scanningChanged)
    def scanning(self):
        return self.is_scanning

    @Property("QVariant", notify=connectedDevicesChanged)
    def connectedDevices(self) -> list[SensorHandle]:
        return [device for device in self.devices if device.connected]

    @Property('QVariant', notify=recordingStateChanged)
    def recordingState(self) -> RecordingState:
        return self._recording_state
    @recordingState.setter
    def recordingState(self, new_val):
        if type(new_val) == int:
            new_val = RecordingState(new_val)
        
        # Stopped -> Started
        if self._recording_state == RecordingState.Stopped and new_val == RecordingState.Started:
            self.startStreaming()
            self.streaming = True
        # Any -> Stopped
        if self._recording_state != RecordingState.Stopped and new_val == RecordingState.Stopped:
            self.stopStreaming()
            self.streaming = False

        self._recording_state = new_val
        self.recordingStateChanged.emit(new_val)

    @Property(bool, notify=streamingChanged)
    def streaming(self) -> bool :
        return self._is_streaming
    @streaming.setter
    def streaming(self, new_val: bool):
        self._is_streaming = new_val
        self.streamingChanged.emit()
        
    def startStreaming(self):
        connected_sensors: list[SensorHandle] = self.connectedDevices
        if(len(connected_sensors) < 1):
            logger.info(f'No connected sensors.')
            return

        self.streaming = True

        from ..context import ctx
        for sensor in connected_sensors:
            recording_desc = RecordingDescription(
                preview_only = False,
                video_path = "",
                sensor_data_path = ctx.projectManager.get_sensor_save_path(sensor.tag),
                preview_fps = 0,
                task = ctx.projectManager.selectedTask,
                board = None
            )
            if not sensor.streaming:
                sensor.startStreaming(recording_desc)

    def stopStreaming(self):
        connected_sensors: list[SensorHandle] = self.connectedDevices
        if(len(connected_sensors) < 1):
            logger.info(f'No connected sensors.')
            return

        self.streaming = False
        
        for sensor in connected_sensors:
            if sensor.streaming:
                sensor.stopStreaming()
    
    
    @Slot(bool)
    def changeIsScanning(self, is_scanning: bool):
        self.is_scanning = is_scanning
        self.scanningChanged.emit()
    
    @Slot()
    def clearSensors(self):
        self.devices_db.clear()
        self.devicesChanged.emit()
        
    @Slot(QBluetoothDeviceInfo)
    def addSensor(self, device: QBluetoothDeviceInfo):
        sensor_item = SensorHandle(device)
        sensor_item.connectedChanged.connect(self.connectedDevicesChanged)
        self.devices_db.append(sensor_item)
        self.devicesChanged.emit()
        
    @Slot()
    def finish(self):
        self.finished.emit()

class SensorScanner(QObject):
    
    sensorsCleared = Signal()
    sensorDetected = Signal(QBluetoothDeviceInfo)
    
    scanning = Signal(bool)
    finished = Signal()
    
    def __init__(self, local_bluetooth_device: QBluetoothLocalDevice, exec_thread: QThread, parent=None):
        super().__init__(parent=parent)
        self.devices_address_db: list[str] = []
        self.exec_thread = exec_thread
        self.local_device = local_bluetooth_device
        self.discovery_agent: QBluetoothDeviceDiscoveryAgent

        self.exec_thread.started.connect(self.run)
        self.finished.connect(self.exec_thread.quit)
        self.finished.connect(self.deleteLater)
        self.exec_thread.finished.connect(self.exec_thread.deleteLater)
    
    @Slot()
    def run(self):
        self.discovery_agent = QBluetoothDeviceDiscoveryAgent(parent=self)
        self.discovery_agent.deviceDiscovered.connect(self.addSensor)
        self.discovery_agent.errorOccurred.connect(self.scanError)
        self.discovery_agent.finished.connect(self.scanFinished)
        self.discovery_agent.canceled.connect(self.scanFinished)

        
    @Slot()
    def refresh(self):
        self.discovery_agent.stop()
        self.scanning.emit(self.discovery_agent.isActive())

        self.devices_address_db.clear()
        self.sensorsCleared.emit()
        
        self.run()

    @Slot()
    def startScan(self):
        self.devices_address_db.clear()
        self.sensorsCleared.emit()
        logger.debug(f"Bluetooth device: {self.local_device.name()} discovery agent started.")
        self.discovery_agent.start(QBluetoothDeviceDiscoveryAgent.LowEnergyMethod)
        self.scanning.emit(self.discovery_agent.isActive())
        logger.debug("Scanning started.")

    @Slot()
    def stopScan(self):
        self.discovery_agent.stop()
        self.scanning.emit(self.discovery_agent.isActive())
        logger.debug("Scanning stopped.")
    
    @Slot(QBluetoothDeviceDiscoveryAgent.Error)
    def scanError(self, error):
        logger.error(f"Error occured while scanning: {error}.")

    @Slot()
    def scanFinished(self):
        if len(self.devices_address_db) <= 0:
            logger.debug("No sensors were found.")

        self.scanning.emit(self.discovery_agent.isActive())

    @Slot(QBluetoothDeviceInfo)
    def addSensor(self, device: QBluetoothDeviceInfo):
        if not self.discovery_agent.isActive():
            return
        address = device.address().toString()
        if address.startswith(CONFIG.SENSOR_MAC_FILTER):
            if not any(device_address_in_list == address for device_address_in_list in self.devices_address_db):
                logger.debug(f"Adding sensor {address}.")
                self.devices_address_db.append(address)
                self.sensorDetected.emit(device)
