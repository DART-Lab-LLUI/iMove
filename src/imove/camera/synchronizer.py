import platform
from tqdm import tqdm
import re
import pandas as pd
import csv
import json
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
import sys
import numpy as np
import cv2 as cv
import subprocess
from multiprocessing.context import SpawnProcess
from scipy.spatial.distance import euclidean
import concurrent.futures

from PySide6.QtCore import  Slot, QObject, QThread, Signal


from ..multilogging import logger
from .utils import SynchronizationDescription
from ..project import SessionTask

 
class SynchronizerProcess(SpawnProcess):
    def __init__(self, sync_desc: SynchronizationDescription) -> None:
        super().__init__()
        self.sync_desc = sync_desc

    def run(self):
        logger.debug(f'Started synchronization process.')
        try:
            video_frames_paths = {}
            with ThreadPoolExecutor() as executor:
                
                # Get the raw timestamps
                future_to_video = {executor.submit(SynchronizerProcess.get_video_timestamps, video_path): video_path for video_path in self.sync_desc.video_paths}
                for future in as_completed(future_to_video):
                    video_path = future_to_video[future]
                    try:
                        result = future.result()
                        video_frames_paths[video_path] = result
                    except Exception as e:
                        print(f"Error processing {video_path}: {e}.")

                # Synchronize Videos
                video_frames_dfs = [pd.read_csv(video_frames_path) for video_frames_path in list(video_frames_paths.values())]
                # Create a reference timeseries that fits inside all the others. Remove 5 seconds from the beginning and the end to avoid initialization artifacts. TODO: this is a hack
                fps = self.sync_desc.fps
                trim_ends_time_sec = 3
                min_time =  max([df['timestamp'].min() for df in video_frames_dfs]) + trim_ends_time_sec
                max_time =  min([df['timestamp'].max() for df in video_frames_dfs]) - trim_ends_time_sec
                
                if max_time <= min_time:
                    logger.error(f'Invalid timestamps for videos.')
                    return

                min_error = np.inf
                min_error_shift = 0
                for shift in np.arange(0, (1/fps)*2, 0.001):
                    reference_frames_df = pd.DataFrame(np.arange(min_time+shift, max_time, 1/fps), columns=['ref_timestamp'])
                    error = -np.inf
                    for video_frame_df in video_frames_dfs:
                        video_frame_merged_with_reference_frame = pd.merge_asof(reference_frames_df, video_frame_df, left_on='ref_timestamp', right_on='timestamp', direction='nearest')
                        error = max(error, euclidean(video_frame_merged_with_reference_frame['ref_timestamp'].values, video_frame_merged_with_reference_frame['timestamp'].values))
                    if error < min_error:
                        min_error = error
                        min_error_shift = shift

                synchronizer_futures = []
                best_reference_frames_df = pd.DataFrame(np.arange(min_time+min_error_shift, max_time, 1/fps), columns=['ref_timestamp'])
                for video_frame_df, video_path in zip(video_frames_dfs, list(video_frames_paths.keys())):
                    video_frame_merged_with_best_reference_frame = pd.merge_asof(best_reference_frames_df, video_frame_df, left_on='ref_timestamp', right_on='timestamp', direction='nearest') 
                    synchronizer_futures.append(executor.submit(SynchronizerProcess.save_synchronized_video, video_path, video_frame_merged_with_best_reference_frame['id'].to_numpy(), video_path.replace('rawvideo.mkv', 'video.mp4')))
                for future in as_completed(synchronizer_futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error processing {video_path}: {e}.")
                    
                # Save the reference frame in csv
                logger.debug(f'Synchronizing the trials and sensors.')
                ref_frames_path = re.sub(r'_cam.+_rawvideo\.mkv$', '_refframes.csv', self.sync_desc.video_paths[0])
                best_reference_frames_df_with_id = best_reference_frames_df.rename(columns={'ref_timestamp': 'timestamp'})
                best_reference_frames_df_with_id = best_reference_frames_df_with_id.reset_index(drop=False).rename(columns={'index': 'id'})
                best_reference_frames_df_with_id = best_reference_frames_df_with_id[['id'] + [col for col in best_reference_frames_df_with_id.columns if col != 'id']]
                best_reference_frames_df_with_id.to_csv(ref_frames_path, index=False)
                
                # Change tiral timestamps to trial frames
                try:
                    trial_dict = {'onset': [], 'offset': [], 'trial_id': []}
                    raw_trial_df = pd.read_csv(self.sync_desc.trial_path)
                    for trial in raw_trial_df.itertuples():
                        trial_dict['onset'].append(int(best_reference_frames_df_with_id.iloc[np.where(best_reference_frames_df_with_id['timestamp'] > trial.onset)[0][0]]['id']))
                        trial_dict['offset'].append(int(best_reference_frames_df_with_id.iloc[np.where(best_reference_frames_df_with_id['timestamp'] > trial.offset)[0][0]]['id']))
                        trial_dict['trial_id'].append(trial.trial_id)
                    trial_df = pd.DataFrame(trial_dict)
                    trial_df.to_csv(self.sync_desc.trial_path.replace('raw', ''), index=False)
                except Exception as e:
                    logger.debug(f'Not synchronizing rawevents. {e}')
                

                try:
                    # Synchronize the sensors
                    for sensor_path in self.sync_desc.sensor_paths:
                        sensor_df = pd.read_csv(sensor_path)
                        merged_df = pd.merge_asof(best_reference_frames_df_with_id, sensor_df, on='timestamp')
                        merged_df.to_csv(sensor_path.replace('raw', ''), index=False)
                except Exception as e:
                    logger.debug(f'Not synchronizing rawmotion. {e}')
    
            
        except Exception as e:
            if str(e) != "":
                logger.error(f'Synchronizer process {e}.')

    @staticmethod
    def get_video_timestamps(video_path: str):
        logger.debug(f'Extracting timestamps from {video_path}.')
        command = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'frame=pts_time',
            '-of', 'json',
            video_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        frames = json.loads(result.stdout)['frames']
        frame_pts_list = [(i, float(frame['pts_time'])) for i, frame in enumerate(frames)]
        df = pd.DataFrame(frame_pts_list, columns=['id', 'timestamp'])
        video_frames_path = video_path.replace('rawvideo.mkv', 'rawframes.csv')
        df.to_csv(video_frames_path, index=False)
        return video_frames_path

    @staticmethod
    def save_synchronized_video(video_path: str, frame_ids, output_path):
        video = cv.VideoCapture(video_path)
        if not video.isOpened():
            logger.error(f'Failed to open {video_path}.')
            return
        
        fps = video.get(cv.CAP_PROP_FPS)
        width = int(video.get(cv.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv.VideoWriter.fourcc(*'mp4v')
        
        output_video = cv.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = int(video.get(cv.CAP_PROP_FRAME_COUNT))
        
        curr = 0
        last_processed_frame_id = -1 
        last_valid_frame = np.zeros((height, width, 3), dtype=np.uint8)
        for frame_id in tqdm(frame_ids):
            if frame_id < 0 or frame_id >= frame_count:
                logger.debug(f"Frame ID {frame_id} is out of range in {video_path}.")
                continue

            # If the current frame_id is the same as the last processed one, reuse the last_valid_frame
            if frame_id == last_processed_frame_id:
                output_video.write(last_valid_frame)
                continue

            # Don't use cv2.CAP_PROP_POS_FRAMES: https://github.com/opencv/opencv/issues/9053
            while True:
                ret, frame = video.read()
                if curr == frame_id:
                    curr += 1
                    break
                curr += 1

            if not ret:
                logger.error(f"Error reading frame {frame_id} from {video_path}.")
                frame = last_valid_frame
            else:
                last_valid_frame = frame
            output_video.write(frame)
            last_processed_frame_id = frame_id
        logger.debug(f'Resampling done {video_path}.')
        video.release()
        output_video.release()
        
class Synchronizer(QObject):

    finished = Signal()

    def __init__(self, sync_desc: SynchronizationDescription, exec_thread: QThread, parent=None):
        super().__init__(parent=parent)

        self._process: SynchronizerProcess | None = None

        self.is_finished = False
        self.exec_thread: QThread = exec_thread
        self.sync_desc = sync_desc

        self.exec_thread.started.connect(self.run)
        self.finished.connect(self.exec_thread.quit)
        self.finished.connect(self.deleteLater)
        self.exec_thread.finished.connect(self.exec_thread.deleteLater)
        
    @Slot()
    def run(self):
        self._process = SynchronizerProcess(self.sync_desc)
        self._process.start()
        self._process.join()
        self.finish()

    @Slot()
    def finish(self):
        if self._process is not None and self._process.is_alive():
            if self._process.join(timeout=5) is None:
                self._process.terminate()
                self._process.join(timeout=1)
        logger.debug(f'Deinitialized synchronizer.')
        self.finished.emit()
        self.is_finished = True
