#!/usr/bin/env python3

import multiprocessing
import os
import sys
import signal
from loguru import logger
from viztracer import VizTracer
from .multilogging import logger

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFontDatabase, QFont
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import Qt, Slot
from PySide6.QtBluetooth import QBluetoothUuid
QBluetoothUuid.__hash__ = lambda self: hash(self.toString())

from imove import context, image_view
import resources


# tracer = VizTracer()

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# logger = logging.getLogger(__name__)

def main():
    # tracer.start()
    
    # Initializes and manages the application execution
    QApplication.setApplicationName("iMove")
    QApplication.setOrganizationName("LLUI")
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
     

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/icons/llui/imove.ico'))
    

    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)

    # Needed to close the app with Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Set themes, fonts, and icons
    font_id = QFontDatabase.addApplicationFont(":/assets/fonts/Signika/Signika-VariableFont_GRAD,wght.ttf")
    if font_id == -1:
        logger.error("Failed to load font")
        sys.exit(-1)
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    font = QFont(font_family)
    app.setFont(font)
    QIcon.setThemeName('breeze')


    base_path = os.path.abspath(os.path.dirname(__file__))
    engine.addImportPath(base_path)
    engine.loadFromModule("qml", "Main")

    if len(engine.rootObjects()) == 0:
        quit()

    context.ctx = engine.singletonInstance("qml", "Context")
    context.ctx.app = app
    engine.quit.connect(context.ctx.exit)

    sys.exit(app.exec())
    

if __name__ == "__main__":
    main()
    

