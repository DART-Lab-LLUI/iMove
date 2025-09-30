from dataclasses import dataclass
import numpy as np
from viztracer import get_tracer


from ..config import CONFIG
from ..multilogging import logger


@dataclass
class SensorData():
    timestamp: float
    eulerX: float
    eulerY: float
    eulerZ: float
    accelX: float
    accelY: float
    accelZ: float
    status: int
    clip_count_accel: int
    clip_count_gyro: int

@dataclass
class SensorDescription:
    name: str
    address: str
    uuid: str
    classOfDevice: int
    tag: str
