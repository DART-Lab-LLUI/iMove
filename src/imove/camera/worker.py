import platform
import sys
import numpy as np
import cv2 as cv
import subprocess
from numpy import ndarray
from viztracer import get_tracer
from multiprocessing import Pipe, Queue
from multiprocessing.connection import Connection
from multiprocessing.context import SpawnProcess

from PySide6.QtCore import  QSocketNotifier, Slot, QObject, QThread, Signal
from PySide6.QtGui import QImage

from ..multilogging import logger
from .utils import CameraDescription, WorkerMessage, cv2qimage, RecordingDescription
from .calibration import get_charuco_detector, CharucoBoardDescription
from ..project import SessionTask

 
class CameraWorkerProcess(SpawnProcess):
    def __init__(self, camera: CameraDescription, board_description: CharucoBoardDescription, recording_description: RecordingDescription, preview_queue: Queue, notif_pipe_send: Connection, comm_channel: Connection) -> None:
        super().__init__()
        self.camera = camera
        self.process: subprocess.Popen | None = None
        self.notif_pipe_send = notif_pipe_send
        self.process_terminated = False
        self.board_desc = board_description
        self.rec_desc = recording_description
        self.comm_channel = comm_channel
        self.preview_queue = preview_queue
        self.frame_size = camera.width * camera.height * camera.channels * camera.dtype.itemsize
        
        self.overlay_frame: ndarray | None = None

    def run(self):
        try:
            os_name = platform.system()
            demuxer = 'v4l2' if os_name == 'Linux' else ('dshow' if os_name == 'Windows' else 'avfoundation')
            if self.rec_desc.preview_only:
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y', # Don't ask for approval when overwriting
                    "-f", demuxer, # Platform dependent demuxer
                    "-video_size", f"{self.camera.width}x{self.camera.height}",
                    "-input_format", "mjpeg",
                    "-framerate", f"{self.camera.fps}", # fps
                    "-i", self.camera.id, # input device
                    "-f", "rawvideo", # rawvideo video codec
                    "-pix_fmt", "bgr24", # opencv requires bgr24 pixel format
                    "-r", f"{self.rec_desc.preview_fps}",
                    "-an","-sn", # disable audio processing
                    "pipe:1" # output1 write to pipe
                    ]
            else:
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y', # Don't ask for approval when overwriting
                    "-f", demuxer, # Platform dependent demuxer
                    "-video_size", f"{self.camera.width}x{self.camera.height}",
                    "-input_format", "mjpeg",
                    "-ts", "abs",
                    "-framerate", f"{self.camera.fps}", # fps
                    "-i", self.camera.id, # input device
                    '-copyts', # copy timestamps (Frame PTS) to the output without normalization
                    '-c:v', 'copy', # video codec of the output is the same as input (mjpeg)
                    "-an","-sn", # disable audio processing
                    self.rec_desc.video_path, # output0 to file
                    "-f", "rawvideo", # rawvideo video codec
                    "-pix_fmt", "bgr24", # opencv requires bgr24 pixel format
                    "-r", f"{self.rec_desc.preview_fps}",
                    "-an","-sn", # disable audio processing
                    "pipe:1" # output1 write to pipe
                    ]
            self.board_detector = get_charuco_detector(self.board_desc)
            
            logger.debug(' '.join(ffmpeg_cmd))
            self.process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)

            if self.process.stdout is None:
                logger.error(f'Closed pipe {self.camera.id}.')
                return

            while not self.process_terminated:
                try:
                    frame = np.frombuffer(self.process.stdout.read(self.frame_size), self.camera.dtype).reshape((self.camera.height, self.camera.width, self.camera.channels))
                except Exception as e:
                    logger.error(f'Invalid read {self.camera.id}: {e}.')
                    self.terminate()

                if self.comm_channel.poll():
                    cmd_type, cmd_val = self.comm_channel.recv()
                    if cmd_type == WorkerMessage.EXIT:
                        self.terminate()
                        sys.exit()
                        
                self.preview(frame.copy())

        except Exception as e:
            if str(e) != "":
                logger.error(f'Worker process {self.camera.id}: {e}.')
            self.terminate()
            

    def terminate(self):
        if self.process is None or not (self.process.poll() is None):
            logger.info("Pipeline already terminated.")
            return
        self.process.stdin and self.process.stdin.close()
        self.process.stdout and self.process.stdout.close()
        self.process.poll() is None and self.process.terminate()
        self.process.wait()
        self.process = None
        logger.info(f"Pipeline terminated successfully. {self.camera.id}")
        
    def preview(self, frame: ndarray):
        if self.overlay_frame is None:
            self.overlay_frame = np.zeros_like(frame)
        width = self.board_desc.width - 1
        height = self.board_desc.height - 1
        if self.rec_desc.task == SessionTask.calib:
            charuco_corners, charuco_ids, marker_corners, marker_ids = self.board_detector.detectBoard(frame)
            if not (charuco_ids is None) and len(charuco_ids) == width*height:
                for i in range(len(charuco_corners)):
                    if i % width != width - 1:  # Horizontal line (if not last in row)
                        start_point = tuple(charuco_corners[i][0].astype(int))
                        end_point = tuple(charuco_corners[i + 1][0].astype(int))
                        cv.line(self.overlay_frame, start_point, end_point, (209, 197, 109), 20)
                    if i // width != height - 1:  # Vertical line (if not last in column)
                        start_point = tuple(charuco_corners[i][0].astype(int))
                        end_point = tuple(charuco_corners[i + width][0].astype(int))
                        cv.line(self.overlay_frame, start_point, end_point, (209, 197, 109), 20)
            overlay_mask = self.overlay_frame > 0
            merged_frame = cv.addWeighted(frame, 0.5, self.overlay_frame, 0.5, 0)
            frame[overlay_mask] = merged_frame[overlay_mask]

        # Drop preview frames if the queue is full
        if self.preview_queue.full():
            self.preview_queue.get()
        self.preview_queue.put(frame)
        self.notif_pipe_send.send(True)


class CameraWorker(QObject):

    _finished = Signal()
    frameProcessed = Signal(QImage)

    def __init__(self, camera: CameraDescription, recording_description: RecordingDescription, exec_thread: QThread, parent=None):
        super().__init__(parent=parent)

        self._notif_pipe = Pipe(duplex=False)
        self._notifier = QSocketNotifier(self._notif_pipe[0].fileno(), QSocketNotifier.Type.Read)
        self._notifier.activated.connect(self.processFrame)
        self._preview_queue = Queue(maxsize=30)
        self._camera = camera
        self._process: CameraWorkerProcess | None = None
        self._board = recording_description.board

        self._recording_description = recording_description

        self._comm_channel = Pipe(duplex=True)
        self._comm_channel_manager = self._comm_channel[1]
        self._comm_channel_worker = self._comm_channel[0]

        self.is_finished = False
        self.exec_thread: QThread = exec_thread

        self.exec_thread.started.connect(self.run)
        self._finished.connect(self.exec_thread.quit)
        self._finished.connect(self.deleteLater)
        self.exec_thread.finished.connect(self.exec_thread.deleteLater)
        
    @Slot()
    def processFrame(self):
        try:
            if self._notif_pipe[0].poll():
                _ = self._notif_pipe[0].recv()
                cv_frame = self._preview_queue.get(timeout=2)
                video_frame = cv2qimage(cv_frame)
                self.frameProcessed.emit(video_frame)
        except Exception as e:
            logger.warning(f'Could not process frame {e}. {self._camera.id}')

    @Slot()
    def run(self):
        self._process = CameraWorkerProcess(self._camera, self._board, self._recording_description, self._preview_queue, self._notif_pipe[1], self._comm_channel_worker)
        self._process.start()

    @Slot()
    def finish(self):
        if self._process is not None and self._process.is_alive():
            try:
                self._comm_channel_manager.send((WorkerMessage.EXIT, None))
            except (BrokenPipeError, OSError):
                logger.warning("Pipe already closed.")
            finally:
                self._comm_channel_manager.close()

            if self._process.join(timeout=5) is None:
                self._process.terminate()
                self._process.join(timeout=1)
        logger.debug(f'Deinitialized writer for camera {self._camera.id}.')
        self._finished.emit()
        self.is_finished = True
