import numpy as np
from dataclasses import dataclass
import struct
from multiprocessing import shared_memory
import cv2 as cv
from enum import Enum, IntEnum, auto

from PySide6.QtMultimedia import QVideoFrame, QVideoFrameFormat
from PySide6.QtCore import QSize, QObject, Signal, Slot, Property
from PySide6.QtGui import QImage

from .calibration import CharucoBoardDescription
from ..project import SessionTask
from ..multilogging import logger 
    

@dataclass
class SynchronizationDescription:
    video_paths: list[str]
    sensor_paths: list[str]
    trial_path: str
    fps: int

@dataclass
class CameraDescription:
    id: str
    idx: int
    width: int
    height: int
    channels: int
    fps: int
    dtype: np.dtype
    
@dataclass
class RecordingDescription():
    preview_only: bool
    video_path: str
    sensor_data_path: str
    task: SessionTask
    preview_fps: int
    board: CharucoBoardDescription | None

class RecordingState(IntEnum):
    Started =  0
    Stopped = -1
    Paused  = -2
    Resumed = -3
    
class WorkerMessage(Enum):
    EXIT = range(1)

            
def cvFrame2QVideoFrame(frame: np.ndarray) -> QVideoFrame:
    # This conversion takes less than 1 ms (negligible)
    rows, cols, channels = frame.shape
    fmt = QVideoFrameFormat(QSize(cols, rows), QVideoFrameFormat.PixelFormat.Format_BGRX8888)
    vf = QVideoFrame(fmt)
    vf.map(QVideoFrame.MapMode.WriteOnly)
    vf.bits(0)[:rows*cols*channels] = frame.tobytes()
    vf.unmap()
    return vf

def cv2qimage(cv_img: np.ndarray):
    """Converts an OpenCV image to a QImage object"""
    # Check if the image has an alpha channel
    if len(cv_img.shape) == 3 and cv_img.shape[2] == 4:
        # Convert from BGR to RGBA
        qimage = QImage(
            cv_img.data,
            cv_img.shape[1],
            cv_img.shape[0],
            cv_img.strides[0],
            QImage.Format.Format_RGBA8888,
        )
    else:
        # Convert from BGR to RGB
        cv_img = cv.cvtColor(cv_img, cv.COLOR_BGR2RGB)
        qimage = QImage(
            cv_img.data,
            cv_img.shape[1],
            cv_img.shape[0],
            cv_img.strides[0],
            QImage.Format.Format_RGB888,
        )
    # Make sure to copy the data into the QImage
    return qimage