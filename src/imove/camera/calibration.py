from pathlib import Path
import os
import toml
import time
import numpy as np
import re
from multiprocessing.connection import Connection
from multiprocessing import Pipe, Process
from dataclasses import dataclass, replace
from aniposelib.boards import CharucoBoard
import cv2 as cv

from PySide6.QtQml import QmlElement
from PySide6.QtCore import QObject, Slot, Signal, QThread, Property
from PySide6.QtGui import QImage

from ..multilogging import logger

QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

@dataclass
class CharucoBoardDescription():
    width: int # squaresX
    height: int # squaresY
    square_length: int
    marker_length: int
    marker_bits: int
    dict_size: int
    manually_verify: bool
    fisheye: bool
    
class CalibratedCamera(QObject):

    calibratedCameraChanged = Signal()
    def __init__(self, idx: int, preview_image_path: str, error: float, matrix: np.ndarray, 
                 distortions: np.ndarray, rotation: np.ndarray, translation: np.ndarray, 
                 parent: QObject | None = None):
        super().__init__(parent=parent)
        self._idx = idx
        self._preview_image_path = preview_image_path
        self._error = error
        self._matrix = matrix
        self._distortions = distortions
        self._rotation = rotation
        self._translation = translation
        
    @Property(int, notify=calibratedCameraChanged)
    def idx(self) -> int:
        return self._idx
    
    @Property(float, notify=calibratedCameraChanged)
    def error(self) -> float:
        return self._error
    
    @Property(str, notify=calibratedCameraChanged)
    def matrix(self) -> str:
        return np.array2string(self._matrix, separator=', ', formatter={'float_kind': lambda x: f"{x:.2f}"}).replace('\n', '').replace(' ', '')

    @Property(str, notify=calibratedCameraChanged)
    def distortions(self) -> str:
        return np.array2string(self._distortions, separator=', ', formatter={'float_kind': lambda x: f"{x:.2f}"}).replace('\n', '').replace(' ', '')

    @Property(str, notify=calibratedCameraChanged)
    def rotation(self) -> str:
        return np.array2string(self._rotation, separator=', ', formatter={'float_kind': lambda x: f"{x:.2f}"}).replace('\n', '').replace(' ', '')

    @Property(str, notify=calibratedCameraChanged)
    def translation(self) -> str:
        return np.array2string(self._translation, separator=', ', formatter={'float_kind': lambda x: f"{x:.2f}"}).replace('\n', '').replace(' ', '')

    @Property(QImage, notify=calibratedCameraChanged)
    def preview(self) -> QImage:
        return QImage(self._preview_image_path)


@QmlElement
class CalibrationManager(QObject):
    calibratingChanged = Signal()
    calibratedCamerasChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        logger.debug(f"Created CalibrationManager.")
        self.board_description = CharucoBoardDescription(7, 5, 115, 92, 4, 250, False, False)
        self.board_detector = get_charuco_detector(self.board_description)
        
        self.calibrator: CameraCalibrator | None = None
        self._is_calibrating = False
        self._calibrated_cameras: list[CalibratedCamera] = []

    @Property("QVariant", notify=calibratedCamerasChanged)
    def calibratedCameras(self):
        return self._calibrated_cameras
        
    def get_board_description_copy(self):
        return replace(self.board_description)

    @Slot(str, str)
    def selectCalibration(self, subject: str, session: str):
        from ..context import ctx
        self._calibrated_cameras = []
        calib_path: str | None = ctx.projectManager.getCalibrationPath(subject, session)
        if calib_path is None:
            self.calibratedCamerasChanged.emit()
            return

        ctx.projectManager.selectCalibration(calib_path)
        try:
            calib_path = Path(calib_path)
            calib_file = toml.load(calib_path)
            
            for key in calib_file:
                if key.startswith('cam_'):
                    cam = calib_file[key]
                    cam_name = cam['name']
                    metadata = calib_file['metadata']
                    # TODO; idx=int(cam_name.split('-')[-1]) add this back later
                    self._calibrated_cameras.append(CalibratedCamera(idx=int(cam_name[3:]), preview_image_path=os.path.join(str(calib_path.parent), metadata[f'{cam_name}_preview']), error=metadata['error'], matrix=np.array(cam['matrix'], dtype=float), distortions=np.array(cam['distortions'], dtype=float), rotation=np.array(cam['rotation'], dtype=float), translation=np.array(cam['translation'], dtype=float)))
        except Exception as e:
            logger.error(f'Could not load the calibration file. {e}')

        self.calibratedCamerasChanged.emit()


    @Property(bool, notify=calibratingChanged)
    def isCalibrating(self):
        return self._is_calibrating
    @isCalibrating.setter
    def isCalibrating(self, new_val: bool):
        self._is_calibrating = new_val
        self.calibratingChanged.emit()
    
    @Slot()
    def startCalibration(self):
        if self.isCalibrating:
            logger.error(f'Cannot start calibrating. Already calibrating.')
            return
        self.isCalibrating = True
        self.calibrator = CameraCalibrator(QThread(self))
        self.calibrator.moveToThread(self.calibrator.exec_thread)
        self.calibrator.finished.connect(self.calibrationFinished)
        self.calibrator.exec_thread.start()
    
    @Slot()
    def calibrationFinished(self):
        self.isCalibrating = False
    
def get_charuco_detector(board_description: CharucoBoardDescription):
    return cv.aruco.CharucoDetector(CharucoBoard(squaresX=board_description.width, squaresY=board_description.height, square_length=board_description.square_length, marker_length=board_description.marker_length, marker_bits=board_description.marker_bits, dict_size=board_description.dict_size, manually_verify=board_description.manually_verify).board)

def get_charuco_board(board_description: CharucoBoardDescription):
    return CharucoBoard(squaresX=board_description.width, squaresY=board_description.height, square_length=board_description.square_length, marker_length=board_description.marker_length, marker_bits=board_description.marker_bits, dict_size=board_description.dict_size, manually_verify=board_description.manually_verify)


def _camera_calibrator_process(video_path_list: list[str], board_description: CharucoBoardDescription, calibration_path: str, comm_channel: Connection):
    from aniposelib.boards import CharucoBoard
    from aniposelib.cameras import CameraGroup
    
    def save_preview_frame(video_path: Path, output_folder: Path) -> Path | None:
        video = cv.VideoCapture(str(video_path))
        total_frames = int(video.get(cv.CAP_PROP_FRAME_COUNT))
        middle_frame_index = total_frames // 2
        video.set(cv.CAP_PROP_POS_FRAMES, middle_frame_index)
        success, frame = video.read()
        video.release()
        
        if success:
            video_name = video_path.name.replace('_video.mp4', '_preview.jpg').replace('cam-', 'cam')
            image_path = output_folder / video_name
            cv.imwrite(str(image_path), frame)
            return image_path
        else:
            logger.error(f"Failed to extract frame from {video_path}")
            return None


    try:
        board = get_charuco_board(board_description)
        camera_ids: list[str] = []
        cam_regex = re.compile(r'cam-(\d+)')
        # TODO: add the - back between cam and id later.
        camera_ids = list([f'cam{cam_regex.search(file_path).group(1)}' for file_path in video_path_list])

        sorted_camera_ids, sorted_video_path = zip(*sorted(zip(camera_ids, video_path_list)))
        camera_ids = list(sorted_camera_ids)
        video_path_list = list(sorted_video_path)

        cgroup = CameraGroup.from_names(camera_ids, fisheye=False)
        video_path_list_list = [[path] for path in video_path_list]
        error, _rows = cgroup.calibrate_videos(video_path_list_list, board)
        logger.debug(f'Anipose calibration done.')
        metadata = {}
        for video_path, camera_name in zip(video_path_list, camera_ids):
            preview_path = save_preview_frame(Path(video_path), Path(calibration_path).parent)
            if preview_path is not None:
                metadata[f'{camera_name}_preview'] = preview_path.name
        metadata['error'] = float(error)
        sub_ses_regex = re.compile(r'sub-(\w+?)_ses-(\w+?)_')
        sub_ses_regex_match = sub_ses_regex.search(calibration_path)
        subject_id = sub_ses_regex_match.group(1)
        session_id = sub_ses_regex_match.group(2)
        metadata['subject_id'] = subject_id
        metadata['session_id'] = session_id
        metadata['created_timestamp'] = time.time()
        cgroup.metadata = metadata
        cgroup.dump(calibration_path)
    except Exception as e:
        logger.error(f'CalibrationProcess {e}.')

class CameraCalibrator(QObject):
    
    finished = Signal()

    def __init__(self, exec_thread: QThread, parent=None):
        super().__init__(parent=parent)

        self.comm_channels = Pipe(duplex=False)

        self._process: Process | None = None
        self.is_finished = False
        self.exec_thread: QThread = exec_thread

        self.exec_thread.started.connect(self.run)
        self.finished.connect(self.exec_thread.quit)
        self.finished.connect(self.deleteLater)
        self.exec_thread.finished.connect(self.exec_thread.deleteLater)


    @Slot()
    def run(self):
        # get_tracer().enable_thread_tracing()
        from ..context import ctx
        self._process = Process(target=_camera_calibrator_process, args=[ctx.projectManager.getCalibrationVideos(), ctx.calibrationManager.get_board_description_copy(), ctx.projectManager.get_calibration_save_path(), self.comm_channels[0]])
        self._process.start()
        self._process.join()
        self.finish()
        
    @Slot()
    def finish(self):
        logger.debug(f'Deinitialized Calibrator.')
        self.is_finished = True
        self.finished.emit()