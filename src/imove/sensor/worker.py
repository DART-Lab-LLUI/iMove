import time
import math
import humps
import csv
from typing import Any, Dict, Iterator, TextIO
from dataclasses import asdict
import struct
from viztracer import get_tracer

from multiprocessing.synchronize import Lock as LockT, Event as EventT, Condition as ConditionT, Barrier as BarrierT
from multiprocessing.sharedctypes import Synchronized

from PySide6.QtCore import Slot, QObject, QThread, Property, Signal, QByteArray
from PySide6.QtBluetooth import QBluetoothAddress, QBluetoothDeviceInfo, QBluetoothUuid, QLowEnergyCharacteristic, QLowEnergyController, QLowEnergyDescriptor, QLowEnergyService

from ..config import CONFIG
from .utils import SensorData, SensorDescription
from ..project import ProjectManager, SessionTask
from ..camera.utils import RecordingDescription, RecordingState
from ..multilogging import logger


QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

class SensorWorker(QObject):
    
    batteryChanged = Signal(int)
    firmwareVersionChanged = Signal(str)
    tagChanged = Signal(str)
    connectedChanged = Signal(bool)
    measurementChanged = Signal(dict)
    
    _finished = Signal()

    def __init__(self, sensor: SensorDescription, exec_thread: QThread, parent=None):
        super().__init__(parent=parent)
        self._task: SessionTask = SessionTask.calib
        self._recording_description: RecordingDescription | None = None
        self._is_writing = False
        self._first_measurement_received = False
        self._first_measurement_timestamp_diff: float = 0.0
        self._sensor_data_file: TextIO | None = None
        self._sensor_data_writer  = None

        self.sensor = sensor
        self.exec_thread = exec_thread
         
        self.services: Dict[QBluetoothUuid, QLowEnergyService] = {}
        self.descriptors: Dict[QBluetoothUuid, QLowEnergyDescriptor] = {}
        self.found_services: list[QBluetoothUuid] = []

        self.exec_thread.started.connect(self.run)
        self._finished.connect(self.exec_thread.quit)
        self._finished.connect(self.deleteLater)
        self.exec_thread.finished.connect(self.exec_thread.deleteLater)
        
    @Slot()
    def run(self):
        # get_tracer().enable_thread_tracing()
        self.controller = QLowEnergyController.createCentral(QBluetoothDeviceInfo(QBluetoothAddress(self.sensor.address), self.sensor.name, self.sensor.classOfDevice), self)
        self.controller.serviceDiscovered.connect(self.serviceDiscovered)
        self.controller.discoveryFinished.connect(self.serviceScanDone)
        self.controller.errorOccurred.connect(self.controllerErrorOccurred)
        self.controller.connected.connect(self.controllerConnected)
        self.controller.disconnected.connect(self.controllerDisconnected)
        logger.debug(f'Connecting to device: {self.sensor.address}')
        self.controller.connectToDevice()
        

    @Slot(QBluetoothUuid)
    def serviceDiscovered(self, gatt: QBluetoothUuid):
        logger.debug(f'Found service: {gatt}')
        if gatt == CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid']:
            logger.debug(f'Configuration service found.')
            self.found_services.append(CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid'])
        elif gatt == CONFIG.SENSORS.MOVELLA_DOT['measurement']['uuid']:
            logger.debug(f'Measurement service found.')
            self.found_services.append(CONFIG.SENSORS.MOVELLA_DOT['measurement']['uuid'])
        elif gatt == CONFIG.SENSORS.MOVELLA_DOT['battery']['uuid']:
            logger.debug(f'Battery service found.')
            self.found_services.append(CONFIG.SENSORS.MOVELLA_DOT['battery']['uuid'])
        elif gatt == CONFIG.SENSORS.MOVELLA_DOT['dfu']['uuid']:
            logger.debug(f'DFU service found.')
            self.found_services.append(CONFIG.SENSORS.MOVELLA_DOT['dfu']['uuid'])
        elif gatt == CONFIG.SENSORS.MOVELLA_DOT['message']['uuid']:
            logger.debug(f'Message service found.')
            self.found_services.append(CONFIG.SENSORS.MOVELLA_DOT['message']['uuid'])
            
    @Slot()
    def serviceScanDone(self):
        logger.debug(f'Service scan done.')
        for service in self.found_services:
            if service == CONFIG.SENSORS.MOVELLA_DOT['battery']['uuid']:
                service_object = self.controller.createServiceObject(CONFIG.SENSORS.MOVELLA_DOT['battery']['uuid'], self)
                service_object.stateChanged.connect(self.batteryServiceStateChanged)
                service_object.characteristicChanged.connect(self.batteryCharacteristicChanged)
                service_object.descriptorWritten.connect(self.confirmedDescriptorWrite)
                service_object.discoverDetails()
                self.services[CONFIG.SENSORS.MOVELLA_DOT['battery']['uuid']] = service_object
            elif service == CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid']:
                service_object = self.controller.createServiceObject(CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid'], self)
                service_object.stateChanged.connect(self.configurationServiceStateChanged)
                service_object.characteristicChanged.connect(self.configurationCharacteristicChanged)
                service_object.descriptorWritten.connect(self.confirmedDescriptorWrite)
                service_object.characteristicWritten.connect(self.confirmedCharacteristicWrite)
                service_object.discoverDetails()
                self.services[CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid']] = service_object
            elif service == CONFIG.SENSORS.MOVELLA_DOT['measurement']['uuid']:
                service_object = self.controller.createServiceObject(CONFIG.SENSORS.MOVELLA_DOT['measurement']['uuid'], self)
                service_object.stateChanged.connect(self.measurementServiceStateChanged)
                service_object.characteristicChanged.connect(self.measurementCharacteristicChanged)
                service_object.descriptorWritten.connect(self.confirmedDescriptorWrite)
                service_object.characteristicWritten.connect(self.confirmedCharacteristicWrite)
                service_object.discoverDetails()
                self.services[CONFIG.SENSORS.MOVELLA_DOT['measurement']['uuid']] = service_object


    @Slot(QLowEnergyDescriptor, QByteArray)
    def confirmedDescriptorWrite(self, d: QLowEnergyDescriptor, value):
        logger.debug(f'Confirmed receipt of descriptor: {d.name()}, {d.type()} with value: {value}.')
        if (d.isValid() and d == self.descriptors[CONFIG.SENSORS.MOVELLA_DOT['battery']['characteristics']['battery']['uuid']] and value == QLowEnergyCharacteristic.CCCDDisable):
            logger.debug(f'Device wants to disconnect by setting the vlaue of notif descriptor to 0.')
            self.controller.disconnectFromDevice()
            self.services = {}

    @Slot(QLowEnergyCharacteristic, QByteArray)
    def confirmedCharacteristicWrite(self, c: QLowEnergyCharacteristic, value):
        logger.debug(f'Successfully wrote to: {c.uuid()}, {c.name()}')


    @Slot(QLowEnergyController.Error)
    def controllerErrorOccurred(self, error: QLowEnergyController.Error):
        logger.error(f"Cannot connect to remote device: {error}.")
        self.connectedChanged.emit(False)
        self._finished.emit()


    @Slot()
    def controllerConnected(self):
        logger.debug(f"Controller connected. Searching for services.")
        self.connectedChanged.emit(True)
        self.controller.discoverServices()


    @Slot()
    def controllerDisconnected(self):
        logger.debug(f"Controller disconnected.")
        self.connectedChanged.emit(False)
        self._finished.emit()
    
    @Slot()
    def disconnectSensor(self):
        self.controller.disconnectFromDevice()
        

    @Slot(SensorDescription, RecordingDescription)
    def startStreaming(self, sensor: SensorDescription, rec_desc: RecordingDescription):
        self._recording_description = rec_desc
        self.sensor = sensor
        self._received_first_measurement = False
        logger.debug(f"Start measurement from the sensor.")
        service_object = self.services[CONFIG.SENSORS.MOVELLA_DOT['measurement']['uuid']]
        control_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['measurement']['characteristics']['control']['uuid'])
        if control_char.isValid():
            data = bytearray(control_char.value().data())
            type_field = 1
            data[0] = type_field
            action = 1 # Start
            data[1] = action
            payload_mode = 7 # extended euler
            data[2] = payload_mode
            service_object.writeCharacteristic(control_char, bytes(data))
            self.start_writing()
        else:
            logger.error('Could not get a valid control characteristic.')

    @Slot()
    def stopStreaming(self):
        logger.debug(f"Stopped measurement from the sensor.")
        service_object = self.services[CONFIG.SENSORS.MOVELLA_DOT['measurement']['uuid']]
        control_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['measurement']['characteristics']['control']['uuid'])
        if control_char.isValid():
            data = bytearray(control_char.value().data())
            type_field = 1
            data[0] = type_field
            action = 0 # Stop
            data[1] = action
            payload_mode = 7 # extended euler
            data[2] = payload_mode
            service_object.writeCharacteristic(control_char, bytes(data))
            self.stop_writing()
        else:
            logger.error('Could not get a valid control characteristic.')

    @Slot()
    def identifySensor(self):
        logger.debug(f"Identifying the sensor.")
        service_object = self.services[CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid']]
        device_control_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['configuration']['characteristics']['control']['uuid'])
        if device_control_char.isValid():
            data = bytearray(device_control_char.value().data())
            visit_index_byte = 0b00000001
            data[0] = visit_index_byte
            data[1] = 0x01
            service_object.writeCharacteristic(device_control_char, bytes(data))
        else:
            logger.error('Could not get a valid device control characteristic.')

    @Slot(str)
    def renameTag(self, new_tag:str):
        
        # Validate the tag based on specification
        try:
            new_tag.encode('ascii')
            if len(new_tag) > 16:
                logger.error("Tag needs to be less than 16 in length.")
                return
        except UnicodeEncodeError:
            logger.error("Tag needs to be ascii alphanumeric")
            return

        logger.debug(f"Renaming the sensor.")
        service_object = self.services[CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid']]
        device_control_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['configuration']['characteristics']['control']['uuid'])
        if device_control_char.isValid():
            data = bytearray(device_control_char.value().data())
            visit_index_byte = 0b00001000
            data[0] = visit_index_byte
            tag_length = len(new_tag)
            data[7] = tag_length
            data[8:8+tag_length] = bytes(new_tag, 'ascii')
            service_object.writeCharacteristic(device_control_char, bytes(data))
            self.tagChanged.emit(new_tag)
        else:
            logger.error('Could not get a valid device control characteristic.')


    @Slot()
    def shutdownSensor(self):

        logger.debug(f"Shutting down the sensor.")
        service_object = self.services[CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid']]
        device_control_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['configuration']['characteristics']['control']['uuid'])
        if device_control_char.isValid():
            data = bytearray(device_control_char.value().data())
            visit_index_byte = 0b00000010
            data[0] = visit_index_byte
            data[2] = 0b00000001
            service_object.writeCharacteristic(device_control_char, bytes(data))
            self.controllerDisconnected()
        else:
            logger.error('Could not get a valid device control characteristic.')


    @Slot(QLowEnergyCharacteristic, QByteArray)
    def batteryCharacteristicChanged(self, c: QLowEnergyCharacteristic, value: QByteArray):
        data = value.data()
        battery_percentage = int(data[0])
        battery_charging = int(data[1])
        logger.debug(f'Received battery char percentage: {battery_percentage}, chargin: {battery_charging}.')
        
        self.batteryChanged.emit(battery_percentage)

    @Slot(QLowEnergyService.ServiceState)
    def batteryServiceStateChanged(self, switch):
        if switch == QLowEnergyService.ServiceState.RemoteService:
            logger.debug(f'Remote battery service.')
        elif switch == QLowEnergyService.ServiceState.RemoteServiceDiscovering:
            logger.debug(f'Remote battery service discovering.')
        elif switch == QLowEnergyService.ServiceState.RemoteServiceDiscovered:
            logger.debug(f'Remote battery service discovered.')
            service_object = self.services[CONFIG.SENSORS.MOVELLA_DOT['battery']['uuid']]
            battery_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['battery']['characteristics']['battery']['uuid'])
            if battery_char.isValid():
                battery_desc = battery_char.descriptor(QBluetoothUuid.DescriptorType.ClientCharacteristicConfiguration)
                if battery_desc.isValid():
                    self.descriptors[CONFIG.SENSORS.MOVELLA_DOT['battery']['characteristics']['battery']['uuid']] = battery_desc
                    service_object.writeDescriptor(battery_desc, QLowEnergyCharacteristic.CCCDEnableNotification)
            else:
                logger.error('Could not get a valid battery characteristic.')

    @Slot(QLowEnergyService.ServiceState)
    def configurationServiceStateChanged(self, switch):
        if switch == QLowEnergyService.ServiceState.RemoteService:
            logger.debug(f'Remote configuration service.')
        elif switch == QLowEnergyService.ServiceState.RemoteServiceDiscovering:
            logger.debug(f'Remote configuration service discovering.')
        elif switch == QLowEnergyService.ServiceState.RemoteServiceDiscovered:
            logger.debug(f'Remote configuration service discovered.')
            service_object = self.services[CONFIG.SENSORS.MOVELLA_DOT['configuration']['uuid']]
            
            # Device info, 0x1001, Sensor basic information
            device_info_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['configuration']['characteristics']['information']['uuid'])
            if device_info_char.isValid():
                data = device_info_char.value().data()
                version_major = int(data[6])
                version_minor = int(data[7])
                version_revision = int(data[8])
                version_str = f'{version_major}.{version_minor}.{version_revision}'
                logger.debug(f'Received version number {version_str}.')
                self.firmwareVersionChanged.emit(version_str)
            else:
                logger.error('Could not get a valid device information characteristic.')
                
            
            # Device control, 0x1002, Sensor behavior and configurations
            device_control_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['configuration']['characteristics']['control']['uuid'])
            if device_control_char.isValid():
                data = device_control_char.value().data()
                tag_length = int(data[7])
                tag = data[8:8+tag_length].decode('utf-8')
                output_rate = int.from_bytes(data[24:26], byteorder='little')
                filter_profile = int(data[26])
                logger.debug(f'Received tag: {tag}, output rate: {output_rate}, filterprofile: {'general' if filter_profile == 0 else 'dynamic'}.')
                self.tagChanged.emit(tag)
            else:
                logger.error('Could not get a valid device control characteristic.')
            

    @Slot(QLowEnergyCharacteristic, QByteArray)
    def configurationCharacteristicChanged(self, c: QLowEnergyCharacteristic, value: QByteArray):
        if c == CONFIG.SENSORS.MOVELLA_DOT['configuration']['characteristics']['information']['uuid']:
            logger.debug('Received configuration characteristic change.')


    @Slot(QLowEnergyService.ServiceState)
    def measurementServiceStateChanged(self, switch):
        if switch == QLowEnergyService.ServiceState.RemoteService:
            logger.debug(f'Remote measurement service.')
        elif switch == QLowEnergyService.ServiceState.RemoteServiceDiscovering:
            logger.debug(f'Remote measurement service discovering.')
        elif switch == QLowEnergyService.ServiceState.RemoteServiceDiscovered:
            logger.debug(f'Remote measurement service discovered.')
            service_object = self.services[CONFIG.SENSORS.MOVELLA_DOT['measurement']['uuid']]
            short_payload_char = service_object.characteristic(CONFIG.SENSORS.MOVELLA_DOT['measurement']['characteristics']['measurementMediumPayload']['uuid'])
            if short_payload_char.isValid():
                short_payload_desc = short_payload_char.descriptor(QBluetoothUuid.DescriptorType.ClientCharacteristicConfiguration)
                if short_payload_desc.isValid():
                    self.descriptors[CONFIG.SENSORS.MOVELLA_DOT['measurement']['characteristics']['measurementMediumPayload']['uuid']] = short_payload_desc
                    service_object.writeDescriptor(short_payload_desc, QLowEnergyCharacteristic.CCCDEnableNotification)
                else:
                    logger.error('Could not get a valid short payload notification descriptor.')
                    
            else:
                logger.error('Could not get a valid short payload characteristic.')
                
                
    @Slot(QLowEnergyCharacteristic, QByteArray)
    def measurementCharacteristicChanged(self, c: QLowEnergyCharacteristic, value: QByteArray):
        data = value.data()
        timestamp = int.from_bytes(data[0:4], byteorder='little')
        timestamp = timestamp / 1000000
        
        euler = [struct.unpack('<f', data[4:8])[0], struct.unpack('<f', data[8:12])[0], struct.unpack('<f', data[12:16])[0]] # x, y, z
        accel = [struct.unpack('<f', data[16:20])[0], struct.unpack('<f', data[20:24])[0], struct.unpack('<f', data[24:28])[0]] # x, y, z
        status = struct.unpack('<H', data[28:30])[0]
        clip_accel = int.from_bytes(data[30:31], byteorder='little', signed=False)
        clip_gyro = int.from_bytes(data[31:32], byteorder='little', signed=False)

        if not self._first_measurement_received:
            self._first_measurement_received = True
            self._first_measurement_timestamp_diff = time.time() - timestamp

        sensor_data = SensorData(timestamp + self._first_measurement_timestamp_diff, euler[0], euler[1], euler[2], accel[0], accel[1], accel[2], status, clip_accel, clip_gyro)
            
        self.measurementChanged.emit(asdict(sensor_data))
        try:
            self.writing_pipeline(sensor_data)
        except Exception as e:
            logger.error(f'Failed to writer sensor data {self.sensor.tag}: {e}')
            

    def start_writing(self):
        if self._recording_description is None:
            return
        self._first_measurement_received = False
        sensor_data_path = self._recording_description.sensor_data_path
        self._task =  SessionTask(self._recording_description.task)
        self._sensor_data_file = open(file=sensor_data_path, mode='w', newline='')
        self._sensor_data_writer = csv.writer(self._sensor_data_file)
        self._sensor_data_writer.writerow(['timestamp', 'euler_x', 'euler_y', 'euler_z', 'accel_x', 'accel_y', 'accel_z', 'status'])
        self._is_writing = True
        logger.debug(f'Sensor: started writing {self.sensor.tag}.')
        
    def stop_writing(self):
        if self._sensor_data_file is not None and not self._sensor_data_file.closed:
            self._sensor_data_file.close()
            self._sensor_data_file = None
        self._is_writing = False

    def writing_pipeline(self, sensor_data: SensorData):
        if self._is_writing and self._sensor_data_writer is not None:
            self._sensor_data_writer.writerow([sensor_data.timestamp, sensor_data.eulerX, sensor_data.eulerY, sensor_data.eulerZ, sensor_data.accelX, sensor_data.accelY, sensor_data.accelZ, sensor_data.status])
