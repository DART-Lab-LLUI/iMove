from enum import Enum, IntEnum
import re
import os
from pathlib import Path
import json
import glob
from typing import override
import humps
import pandas as pd
from .multilogging import logger

from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import Property, QEnum, QFile, QModelIndex, QObject, Slot, Signal
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "qml"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class ProjectFileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
    @override
    def columnCount(self, parent):
        return 1

class SessionTask(IntEnum):
    calib, drink = range(2)

@QmlElement
class ProjectManager(QObject):
    
    QEnum(SessionTask)

    projectChanged = Signal(str)
    subjectChanged = Signal(str)
    sessionChanged = Signal(str)
    calibrationChanged = Signal(str)
    taskChanged = Signal(SessionTask)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)
        logger.debug(f"Created ProjectManager: {id(self)}.")
        self._opened_project_path: Path | None = None
        self._selected_task: SessionTask | None = SessionTask.calib
        self._selected_calibration: str = ''
        self._file_system_model: ProjectFileSystemModel | None = None
        
        # TODO: remove the manual initialization
        self._selected_subject_id: str = '4a20'
        self._selected_session_id: str = '20240901a'
        self.openProject('/home/arashsm79/bids_root')
        
    @Slot(result=list)
    def sessionTaskNames(self) -> list[str]:
        return [task.name for task in SessionTask]
    
    @Property(QModelIndex, notify=projectChanged)
    def projectIndex(self):
        if self._file_system_model is None:
            return
        return self._file_system_model.index(self._file_system_model.rootPath())

    def get_video_save_path(self, cam_idx: int) -> str:
        if self.selectedTask == SessionTask.drink:
            return os.path.join(f'{self.openedProjectPath}', f'sub-{self.selectedSubject}', f'ses-{self.selectedSession}', 'video', f'sub-{self.selectedSubject}_ses-{self.selectedSession}_task-{self.selectedTask.name}_cam{cam_idx}_rawvideo.mkv')
        else:
            return os.path.join(f'{self.openedProjectPath}', f'sub-{self.selectedSubject}', f'ses-{self.selectedSession}', 'video', f'sub-{self.selectedSubject}_ses-{self.selectedSession}_task-{self.selectedTask.name}_cam-{cam_idx}_rawvideo.mkv')

    def get_frames_timestamp_save_path(self, cam_idx: int) -> str:
        if self.selectedTask == SessionTask.drink:
            return os.path.join(f'{self.openedProjectPath}', f'sub-{self.selectedSubject}', f'ses-{self.selectedSession}', 'video', f'sub-{self.selectedSubject}_ses-{self.selectedSession}_task-{self.selectedTask.name}_cam{cam_idx}_rawframes.csv')
        else:
            return os.path.join(f'{self.openedProjectPath}', f'sub-{self.selectedSubject}', f'ses-{self.selectedSession}', 'video', f'sub-{self.selectedSubject}_ses-{self.selectedSession}_task-{self.selectedTask.name}_cam-{cam_idx}_rawframes.csv')

    def get_trial_save_path(self) -> str:
        return os.path.join(f'{self.openedProjectPath}', f'sub-{self.selectedSubject}', f'ses-{self.selectedSession}', 'video', f'sub-{self.selectedSubject}_ses-{self.selectedSession}_task-{self.selectedTask.name}_rawevents.csv')

    def get_sensor_save_path(self, tag: str) -> str:
        return os.path.join(f'{self.openedProjectPath}', f'sub-{self.selectedSubject}', f'ses-{self.selectedSession}', 'motion', f'sub-{self.selectedSubject}_ses-{self.selectedSession}_task-{self.selectedTask.name}_tracksys-imu_sensor-{humps.camelize(tag)}_rawmotion.csv')

    def get_calibration_save_path(self) -> str:
        return os.path.join(f'{self.openedProjectPath}', f'sub-{self.selectedSubject}', f'ses-{self.selectedSession}', 'video', f'sub-{self.selectedSubject}_ses-{self.selectedSession}_task-{SessionTask.calib.name}_calibration.toml')

    @property
    def metrics_plot_path(self) -> str:
        return os.path.join(f'{self.openedProjectPath}', f'sub-{self.selectedSubject}', f'ses-{self.selectedSession}', 'metric', 'Plots')

    @Property(str, notify=subjectChanged)
    def selectedSubject(self):
        return self._selected_subject_id
    @selectedSubject.setter
    def selectedSubject(self, new_val: str):
        self._selected_subject_id = new_val
        self.subjectChanged.emit(new_val)
    @Slot(str)
    def selectSubject(self, subject: str):
        self.selectedSession = ''
        self.selectedSubject = subject

    @Property(str, notify=sessionChanged)
    def selectedSession(self):
        return self._selected_session_id
    @selectedSession.setter
    def selectedSession(self, new_val: str):
        self._selected_session_id = new_val
        self.sessionChanged.emit(new_val)
    @Slot(str, str)
    def selectSession(self, subject: str, session: str):
        self.selectedSession = session
        self.selectedSubject = subject

    @Property(str, notify=calibrationChanged)
    def selectedCalibration(self):
        return self._selected_calibration
    @selectedCalibration.setter
    def selectedCalibration(self, new_val: str):
        self._selected_calibration = new_val
        self.calibrationChanged.emit(new_val)
    @Slot(str)
    def selectCalibration(self, calib_path: str):
        self.selectedCalibration = calib_path
        
        
    @Property('QVariant', notify=sessionChanged)
    def selectedTask(self):
        return self._selected_task
    @selectedTask.setter
    def selectedTask(self, new_val: str):
        self._selected_task = getattr(SessionTask, new_val)
        self.taskChanged.emit(self._selected_task)

    @Slot(str, str)
    def getCalibrationPath(self, subject_id: str, session_id: str) -> str | None:
        video_path = self._opened_project_path / f'sub-{subject_id}' / f'ses-{session_id}' / 'video'
        calib_file_paths = list(video_path.rglob('*_calibration.toml'))
        if len(calib_file_paths) > 0:
            return str(calib_file_paths[0])

    @Slot()
    def getSessionDir(self) -> Path:
        return self._opened_project_path / f'sub-{self.selectedSubject}' / f'ses-{self.selectedSession}'

    @Slot()
    def getSessionVideoDir(self) -> Path:
        return self.getSessionDir() / 'video'

    @Slot()
    def getSessionMotionDir(self) -> Path:
        return self.getSessionDir() / 'motion'

    @Property(str, notify=projectChanged)
    def openedProjectName(self):
        return self._opened_project_path.name

    @Property(str, notify=projectChanged)
    def openedProjectPath(self):
        return str(self._opened_project_path)
    
    @Property('QVariant', notify=projectChanged)
    def fileSystemModel(self):
        return self._file_system_model

    def _load_json(self, file_path: Path) -> dict | list[dict]:
        if self._opened_project_path is None:
            return {}
        full_path = self._opened_project_path / file_path
        if full_path.exists():
            with full_path.open('r') as f:
                return json.load(f)
        return {}

    def _load_tsv(self, file_path: Path) -> pd.DataFrame:
        if self._opened_project_path is None:
            return pd.DataFrame()
        full_path = self._opened_project_path / file_path
        if full_path.exists():
            return pd.read_csv(str(full_path), sep='\t')
        return pd.DataFrame()

    def _save_json(self, data: dict | list[dict], file_path: Path):
        if self._opened_project_path is None:
            return
        full_path = self._opened_project_path / file_path
        with full_path.open('w') as f:
            json.dump(data, f, indent=4)

    def _save_tsv(self, data: pd.DataFrame, file_path: Path):
        if self._opened_project_path is None:
            return
        full_path = self._opened_project_path / file_path
        if data.empty:
            # Create the file and write the header
            with open(full_path, 'w', newline='') as file:
                file.write('\t'.join(data.columns) + '\n')
        else:
            # Write the DataFrame to a CSV file
            data.to_csv(full_path, sep='\t', index=False)

    @Slot(result=list)
    def getTaskVideos(self, task: SessionTask, raw=False) -> list[str]:
        if raw:
            task_video_paths = list(self.getSessionVideoDir().rglob(f'*task-{task.name}*_rawvideo.mkv'))
        else:
            task_video_paths = list(self.getSessionVideoDir().rglob(f'*task-{task.name}*_video.mp4'))
        task_video_paths_str = [str(file) for file in task_video_paths]
        return task_video_paths_str

    @Slot(result=list)
    def getCalibrationVideos(self) -> list[str]:
        return self.getTaskVideos(SessionTask.calib, raw=False)

    @Slot(result=list)
    def getSelectedTaskVideos(self, raw=False) -> list[str]:
        return self.getTaskVideos(self.selectedTask, raw)

    @Slot(result=list)
    def getTaskSensorData(self, task: SessionTask) -> list[str]:
        task_sensor_paths = list(self.getSessionMotionDir().rglob(f'*task-{task.name}*_rawmotion.csv'))
        task_sensor_paths_str = [str(file) for file in task_sensor_paths]
        return task_sensor_paths_str

    @Slot(result=list)
    def getSelectedTaskSensorData(self) -> list[str]:
        return self.getTaskSensorData(self.selectedTask)

    @Slot(str)
    def openProject(self, project_dir_path_str: str):
        project_dir_path = Path(project_dir_path_str)
        if self._file_system_model is None:
            self._file_system_model = ProjectFileSystemModel()
            self._file_system_model.setNameFilters(['sub-*', 'ses-*'])
            self._file_system_model.setNameFilterDisables(False)

        self._file_system_model.setRootPath(str(project_dir_path))
        self._opened_project_path = project_dir_path
        self.projectChanged.emit(str(project_dir_path))
        # from .context import ctx
        # ctx.reset()

    @Slot(str)
    def createProject(self, project_dir_path_str: str):
        project_dir_path = Path(project_dir_path_str)
        self._opened_project_path = project_dir_path
        name = project_dir_path.name
        project_dir_path.mkdir(parents=True, exist_ok=True)

        dataset_description = {
            "Name": name,
            "BIDSVersion": "1.10.0",
            "Authors": ['Arash Sal Moslehian', 'iMove', 'LLUI']
        }
        self._save_json(dataset_description, 'dataset_description.json')
        
        readme_content = f"""
        # {name}

        ## Description

        Dataset created with org.LLUI.iMove
        """
        readme_path = project_dir_path / 'README.md'
        readme_path.write_text(readme_content)
        
        participants = pd.DataFrame(columns=['participant_id'])
        self._save_tsv(participants, 'participants.tsv')
        
        self.openProject(project_dir_path_str)

    def list_subjects(self) -> list[str]:
        subjects = self._opened_project_path.glob('sub-*')
        return [sub.name for sub in subjects]

    def list_sessions(self, subject_id: str):
        if self._opened_project_path is None:
            return []
        subject_dir_path = self._opened_project_path /  subject_id
        sessions = subject_dir_path.glob('ses-*')
        return [ses.name for ses in sessions]

    def list_tasks(self, subject_id, session_id):
        if self._opened_project_path is None:
            return []
        session_dir_path = self._opened_project_path / subject_id / session_id
        task_regex = re.compile(r'task-(\w+)')
        return list(set([task_regex.search(file_path.name).group(1) for file_path in session_dir_path.glob('*_task-*')]))

    @Slot(str)
    def addSubject(self, subject_id: str):
        if self._opened_project_path is None:
            return
        subject_id_with_prefix = 'sub-' + subject_id
        subject_dir_path: Path = self._opened_project_path / subject_id_with_prefix
        subject_dir_path.mkdir(exist_ok=True)
        participants_df = self._load_tsv('participants.tsv')
        new_row = pd.DataFrame({'participant_id': [subject_id_with_prefix]})
        participants_df = pd.concat([participants_df, new_row], ignore_index=True)
        self._save_tsv(participants_df, file_path='participants.tsv')
        self.selectedSubject(subject_id)
        

    @Slot(str)
    def addSession(self, session_id):
        if self._opened_project_path is None:
            return
        session_id_with_prefix = 'ses-' + session_id
        session_dir_path: Path = self._opened_project_path / f'sub-{self.selectedSubject}' / session_id_with_prefix
        session_dir_path.mkdir(exist_ok=True)
        (session_dir_path / 'video').mkdir(exist_ok=True)
        (session_dir_path / 'motion').mkdir(exist_ok=True)
        self.selectedSession = session_id

    def summary(self):
        subjects = self.list_subjects()
        summary = {
            "Number of subjects": len(subjects),
            "Subjects": {}
        }
        for subject in subjects:
            sessions = self.list_sessions(subject)
            summary["Subjects"][subject] = {
                "Number of sessions": len(sessions),
                "Sessions": {}
            }
            for session in sessions:
                tasks = self.list_tasks(subject, session)
                summary["Subjects"][subject]["Sessions"][session] = {
                    "Number of tasks": len(tasks),
                    "Tasks": tasks
                }
        return summary
