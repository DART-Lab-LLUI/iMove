import time
import pandas as pd
from viztracer import get_tracer

from PySide6.QtCore import  QEnum, Slot, QObject, QThread, Property, Signal
from PySide6.QtQml import QmlElement
from PySide6.QtMultimedia import QMediaDevices, QCamera


from .handle import CameraHandle
from .synchronizer import Synchronizer
from ..multilogging import logger
from .utils import RecordingDescription, RecordingState, SynchronizationDescription
from ..config import CONFIG

QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1
  


@QmlElement
class CameraManager(QObject):
    
    devicesChanged = Signal()
    connectedDevicesChanged = Signal()
    devicesIdChanged = Signal()
    trialsChanged = Signal()
    synchronizingChanged = Signal()

    recordingStateChanged = Signal(RecordingState)
    streamingChanged = Signal()
    trialStateChanged = Signal(RecordingState)
    previewChanged = Signal()
    
    QEnum(RecordingState)
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        logger.debug(f"Created CameraManager: {id(self)}.")
        self._devices_db: list[CameraHandle] = []
        self._trials: list[TrialHandle] = []
        self._streaming_devices: list[CameraHandle] = []
        self._camera_ids: list[int] = []
        self._recording_state = RecordingState.Stopped
        self._is_streaming = False
        self._is_preview = False
        self._is_recording = False
        self._is_recording_trial = False
        self._is_synchronizing = False
        self._sampling_fps: int = 60
        self._media_devices: QMediaDevices | None = None
        self._trial_state = RecordingState.Stopped
        self._synchronizer: Synchronizer | None = None
        
 

    @Slot(list, bool)
    def startStreaming(self, cameras: list[CameraHandle], preview_only):
        
        if(len(cameras) < 1):
            logger.info(f'No connected cameras.')
            return

        # Sampling FPS is the min fps of cameras.
        self._sampling_fps = int(min([camera.fps for camera in cameras]))
        
        self.streaming = True

        from ..context import ctx
        for camera in cameras:
            if not camera.streaming:
                recording_desc = RecordingDescription(
                    preview_only = preview_only,
                    video_path = ctx.projectManager.get_video_save_path(camera.idx),
                    sensor_data_path="",
                    preview_fps=5,
                    task=ctx.projectManager.selectedTask,
                    board=ctx.calibrationManager.get_board_description_copy()
                )
                camera.startStreaming(recording_desc)
                self._streaming_devices.append(camera)
        
    @Slot()
    def stopStreaming(self):
        self.streaming = False
        for camera in self._streaming_devices:
            camera.stopStreaming()
        self._streaming_devices = []

    @Slot()
    def synchronize(self):
        from ..context import ctx
        self.synchronizing = True
        
        video_list = ctx.projectManager.getSelectedTaskVideos(raw=True)
        sensor_list = ctx.projectManager.getSelectedTaskSensorData()
        trial_path: str = ctx.projectManager.get_trial_save_path()
        
        self._synchronizer = Synchronizer(SynchronizationDescription(video_list, sensor_list, trial_path, self._sampling_fps), exec_thread=QThread(self))
        self._synchronizer.moveToThread(self._synchronizer.exec_thread)
     
        self._synchronizer.finished.connect(self.synchronizationFinished)
        
        self._synchronizer.exec_thread.start()
        
    @Slot()
    def synchronizationFinished(self):
        self.synchronizing = False
    
    @Property('QVariant', notify=recordingStateChanged)
    def recordingState(self) -> RecordingState:
        return self._recording_state
    @recordingState.setter
    def recordingState(self, new_val):
        if type(new_val) == int:
            new_val = RecordingState(new_val)
        
        # Stopped -> Started
        if self._recording_state == RecordingState.Stopped and new_val == RecordingState.Started:
            self.preview = False
            self.startStreaming(self.connectedDevices, preview_only=False)
            self.recording = True
        # Any -> Stopped
        if self._recording_state != RecordingState.Stopped and new_val == RecordingState.Stopped:
            self.stopStreaming()
            self.save_reset_trials()
            self.recording = False

        self._recording_state = new_val
        self.recordingStateChanged.emit(new_val)

    @Property('QVariant', notify=trialStateChanged)
    def trialState(self) -> RecordingState:
        return self._trial_state
    @trialState.setter
    def trialState(self, new_val):
        if type(new_val) == int:
            new_val = RecordingState(new_val)

        if new_val == RecordingState.Started:
            self.start_trial()
        elif new_val == RecordingState.Stopped:
            self.stop_trial()

        self._trial_state = new_val
        self.trialStateChanged.emit(new_val)
        
    def start_trial(self):
        self.recordingTrial = True
        self._trials.append(TrialHandle(id=len(self._trials)+1, start_frame_time=time.time()))
        self.trialsChanged.emit()

    def stop_trial(self):
        if len(self._trials) < 1:
            return
        self.recordingTrial = False
        last_trial = self._trials[-1]
        last_trial.endFrameTime = time.time()
        last_trial.durationSec = round((last_trial.endFrameTime - last_trial.startFrameTime), 2)
    
    def save_reset_trials(self):
        trial_dict = {'onset': [], 'offset': [], 'trial_id': []}
        for trial in self._trials:
            trial_dict['onset'].append(trial.startFrameTime)
            trial_dict['offset'].append(trial.endFrameTime)
            trial_dict['trial_id'].append(trial.id)
        from ..context import ctx
        trial_path: str = ctx.projectManager.get_trial_save_path()
        trial_df = pd.DataFrame(trial_dict)
        trial_df.to_csv(trial_path, index=False)
        self._trials = []
        self.trialsChanged.emit()

    @Property(bool, notify=streamingChanged)
    def streaming(self) -> bool :
        return self._is_streaming
    @streaming.setter
    def streaming(self, new_val: bool):
        self._is_streaming = new_val
        self.streamingChanged.emit()

    @Property(bool, notify=recordingStateChanged)
    def recording(self) -> bool :
        return self._is_recording
    @recording.setter
    def recording(self, new_val: bool):
        self._is_recording = new_val

    @Property(bool, notify=trialStateChanged)
    def recordingTrial(self) -> bool :
        return self._is_recording_trial
    @recordingTrial.setter
    def recordingTrial(self, new_val: bool):
        self._is_recording_trial = new_val

    @Property(bool, notify=synchronizingChanged)
    def synchronizing(self) -> bool :
        return self._is_synchronizing
    @synchronizing.setter
    def synchronizing(self, new_val: bool):
        self._is_synchronizing = new_val
        self.synchronizingChanged.emit()

    @Property(bool, notify=synchronizingChanged)
    def preview(self) -> bool :
        return self._is_preview
    @preview.setter
    def preview(self, new_val: bool):
        self._is_preview = new_val
        if self._is_preview:
            self.startStreaming(self.devices, True)
        else:
            self.stopStreaming()
        self.previewChanged.emit()
    
    @Property(list, notify=devicesIdChanged)
    def cameraIDs(self) -> list[int]:
        return self._camera_ids

    @Slot()
    def scanCameras(self):
        if self._media_devices is None:
            self._media_devices = QMediaDevices()
            self._media_devices.videoInputsChanged.connect(self.createCameraItem)
            self.createCameraItem()
        else:
            for dev in self.devices:
                dev.deleteLater()
                self.removeCameraIdx(dev.idx)
            self.devices = []
            self.createCameraItem()

    @Slot()
    def createCameraItem(self):
        if self._media_devices is None:
            return
        devices = self._media_devices.videoInputs()
        
        # delete everything that is in self.devices but not in the new inputs
        new_device_ids = [dev.id().data().decode('utf-8') for dev in devices]
        valid_cameras = [camera_item for camera_item in self.devices if camera_item.id in new_device_ids]
        invalid_cameras = [camera_item for camera_item in self.devices if camera_item.id not in new_device_ids]
        self.devices = valid_cameras
        for dev in invalid_cameras:
            dev.deleteLater()
            self.removeCameraIdx(dev.idx)

        for device in devices:
            # TODO: hack to remove unnecessary cameras
            if 'Y8' in device.videoFormats()[0].pixelFormat().name:
                continue
            # if the camera is already in the list dont need to add a new one.
            camera_with_this_id:  CameraHandle | None = next((camera_item for camera_item in self.devices if camera_item.id == device.id().data().decode('utf-8')), None)
            if camera_with_this_id is not None:
                continue
            camera = QCamera(device)
            camera_item = CameraHandle(camera, parent=self)
            camera.setParent(camera_item)
            
            camera_item.connectedChanged.connect(self.connectedDevicesChanged)

            self.addCamera(camera_item)
            
    @Slot(int)
    def addCameraIdx(self, new_id):
        self._camera_ids.append(new_id)
        self.devicesIdChanged.emit()
            
    @Slot(int)
    def removeCameraIdx(self, to_be_removed_id: int):
        if to_be_removed_id in self._camera_ids:
            self._camera_ids.remove(to_be_removed_id)
            self.devicesIdChanged.emit()

    @Slot(result=int)
    def nextCameraIdx(self) -> int:
        if len(self._camera_ids) < 1:
            self.addCameraIdx(1)
            return 1

        self._camera_ids.sort()
        next_number = 1
        
        for num in self._camera_ids:
            if num == next_number:
                next_number += 1
            elif num > next_number:
                break
        
        self.addCameraIdx(next_number)
        return next_number
            
    @Slot(int)
    def reassignCameraIdx(self, old_id, new_id):
        self.removeCameraIdx(old_id)
        camera_with_this_id:  CameraHandle | None = next((camera_item for camera_item in self.devices if camera_item.idx == new_id), None)
        if camera_with_this_id:
            camera_with_this_id.connected = False
        self.addCameraIdx(new_id)

            
    @Property("QVariant", notify=devicesChanged)
    def devices(self):
        return self._devices_db

    @Property("QVariant", notify=trialsChanged)
    def trials(self):
        return self._trials

    @Property("QVariant", notify=connectedDevicesChanged)
    def connectedDevices(self) -> list[CameraHandle]:
        return [device for device in self.devices if device.connected]

    @Property("QVariant", notify=devicesChanged)
    def disconnectedDevices(self) -> list[CameraHandle]:
        return [device for device in self.devices if not device.connected]

    @devices.setter
    def devices(self, new_devices: list[CameraHandle]):
        self._devices_db = new_devices
        self.devicesChanged.emit()

    @Slot()
    def clearCameras(self):
        self._devices_db.clear()
        self.devicesChanged.emit()
        
    @Slot(CameraHandle)
    def addCamera(self, camera_item: CameraHandle):
        self._devices_db.append(camera_item)
        self.devicesChanged.emit()

class TrialHandle(QObject):
    trialChanged = Signal()
    def __init__(self, id: int,  start_frame_time: float, parent=None):
        super().__init__(parent=parent)
        self._id = id
        self._start_frame_time = start_frame_time
        self._end_frame_time: float | None = None
        self._duration_sec: float | None = None
        
    @Property(int, notify=trialChanged)
    def id(self):
        return self._id
    @id.setter
    def id(self, new_val: int):
        self._id = new_val
        self.trialChanged.emit()

    @Property(float, notify=trialChanged)
    def startFrameTime(self):
        return self._start_frame_time
    @startFrameTime.setter
    def startFrameTime(self, new_val: float):
        self._start_frame_time = new_val
        self.trialChanged.emit()

    @Property(float, notify=trialChanged)
    def endFrameTime(self):
        return self._end_frame_time
    @endFrameTime.setter
    def endFrameTime(self, new_val: float):
        self._end_frame_time = new_val
        self.trialChanged.emit()

    @Property(float, notify=trialChanged)
    def durationSec(self):
        return self._duration_sec
    @durationSec.setter
    def durationSec(self, new_val: float):
        self._duration_sec = new_val
        self.trialChanged.emit()
