from enum import Enum
import json

from PySide6.QtMultimedia import QVideoFrameFormat

from .utils import replace_uuid

class Config:
    _instance = None
    
    class Sensors():
        def __init__(self):
            with open('src/imove/sensor/plugins/movella_dot/specification.json', 'r') as file:
                self.MOVELLA_DOT = json.load(file)
                replace_uuid(self.MOVELLA_DOT)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.SENSORS = Config.Sensors()
        self.SENSOR_MAC_FILTER = 'D4:22:CD:'
        self.MIN_CAMERA_WIDTH = 1800
        self.MIN_CAMERA_HEIGHT = 1000
        self.MIN_CAMERA_FPS = 30
        self.CAMERA_PIXELFORMATS = [QVideoFrameFormat.PixelFormat.Format_Jpeg]

CONFIG = Config()
