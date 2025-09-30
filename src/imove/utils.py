import cv2
from .multilogging import logger

from PySide6.QtCore import QUuid
from PySide6.QtBluetooth import QBluetoothUuid


def replace_uuid(d):
    for key, value in d.items():
        if isinstance(value, dict):
            replace_uuid(value)
        elif key == 'uuid' and isinstance(value, str) and len(value) == 36 and value.count('-') == 4:
            d[key] = QBluetoothUuid(QUuid.fromString(value))
            
def print_cap_prop(cap: cv2.VideoCapture):
        properties = [
            (cv2.CAP_PROP_POS_MSEC, 'CAP_PROP_POS_MSEC'),
            (cv2.CAP_PROP_POS_FRAMES, 'CAP_PROP_POS_FRAMES'),
            (cv2.CAP_PROP_FRAME_WIDTH, 'CAP_PROP_FRAME_WIDTH'),
            (cv2.CAP_PROP_FRAME_HEIGHT, 'CAP_PROP_FRAME_HEIGHT'),
            (cv2.CAP_PROP_FPS, 'CAP_PROP_FPS'),
            (cv2.CAP_PROP_FOURCC, 'CAP_PROP_FOURCC'),
            (cv2.CAP_PROP_FORMAT, 'CAP_PROP_FORMAT'),
            (cv2.CAP_PROP_MODE, 'CAP_PROP_MODE'),
            (cv2.CAP_PROP_BRIGHTNESS, 'CAP_PROP_BRIGHTNESS'),
            (cv2.CAP_PROP_CONTRAST, 'CAP_PROP_CONTRAST'),
            (cv2.CAP_PROP_SATURATION, 'CAP_PROP_SATURATION'),
            (cv2.CAP_PROP_GAIN, 'CAP_PROP_GAIN'),
            (cv2.CAP_PROP_EXPOSURE, 'CAP_PROP_EXPOSURE'),
            (cv2.CAP_PROP_AUTOFOCUS, 'CAP_PROP_AUTOFOCUS'),
            (cv2.CAP_PROP_BUFFERSIZE, 'CAP_PROP_BUFFERSIZE'),
            (cv2.CAP_PROP_HW_ACCELERATION, 'CAP_PROP_HW_ACCELERATION'),
            (cv2.CAP_PROP_HW_DEVICE, 'CAP_PROP_HW_DEVICE'),
        ]
        for prop, name in properties:
            value = cap.get(prop)
            if prop == cv2.CAP_PROP_FOURCC:
                value = ''.join([chr((int(value) >> 8 * i) & 0xFF) for i in range(4)])
            logger.debug(f"{name}: {value}")