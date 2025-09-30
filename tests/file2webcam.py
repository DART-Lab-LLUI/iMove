# This script plays back a video file on the virtual camera.
# It also shows how to:
# - select a specific camera device
# - use BGR as pixel format

import argparse
from dataclasses import dataclass
from contextlib import ExitStack
import pyvirtualcam
from pyvirtualcam import PixelFormat
import cv2

parser = argparse.ArgumentParser()
parser.add_argument("video_paths", type=str, nargs='+', help="path to input video file")
parser.add_argument("--devices", type=str, nargs='+', help="virtual camera device, e.g. /dev/video0 (optional)")
args = parser.parse_args()


@dataclass
class VideoItem():
    video: cv2.VideoCapture
    length: int
    width: int
    height: int
    fps: float
    device: str
    played_frame_count: int = 0

videos: [VideoItem] = []

for video_path, device in zip(args.video_paths, args.devices):
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise ValueError("error opening video")
    video_item = VideoItem(video, int(video.get(cv2.CAP_PROP_FRAME_COUNT)), int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)), video.get(cv2.CAP_PROP_FPS), device)
    videos.append(video_item)

with ExitStack() as es:
    virtual_cams = [es.enter_context(pyvirtualcam.Camera(vc.width, vc.height, vc.fps, fmt=PixelFormat.BGR, device=vc.device, print_fps=False)) for vc in videos]

    
    while True:
        frames = []
        for video_item in videos:
            # Restart video on last frame.
            if video_item.played_frame_count == video_item.length:
                video_item.played_frame_count = 0
                video_item.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Read video frame.
            ret, frame = video_item.video.read()
            if not ret:
                raise RuntimeError('Error fetching frame')
            
            frames.append(frame)
            video_item.played_frame_count += 1

        for idx, cam in enumerate(virtual_cams):
            cam.send(frames[idx])

        for cam in virtual_cams:
            # Wait until it's time for the next frame
            cam.sleep_until_next_frame()