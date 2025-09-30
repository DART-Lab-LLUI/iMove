from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Dict, TypeVar, Generic
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, Slot


class QRolesMeta(type):
    def __new__(cls, name, bases, class_dict):
        if len(class_dict.get('__annotations__', {})) > 0:
            role_dict = {f: auto() for f in class_dict.get('__annotations__', {}).keys()}
            role_dict[next(iter(role_dict))] = Qt.UserRole
            roles = IntEnum('roles', role_dict)
            
            # Create the ROLE_NAMES dictionary dynamically
            role_names = {getattr(roles, key): key.lower().encode() for key in role_dict}
            
            # Add Roles enum and ROLE_NAMES to the class
            class_dict['Roles'] = roles
            class_dict['ROLE_NAMES'] = role_names
        
        return super().__new__(cls, name, bases, class_dict)


class QAbstractListItem(metaclass=QRolesMeta):
    def __getitem__(self, role):
        if role in self.ROLE_NAMES:
            return getattr(self, self.ROLE_NAMES[role].decode('utf-8'))
        else:
            raise KeyError(f"Role {role} is not valid.")

    def __setitem__(self, role, value):
        if role in self.ROLE_NAMES:
            setattr(self, self.ROLE_NAMES[role].decode('utf-8'), value)
        else:
            raise KeyError(f"Role {role} is not valid.")



class QListModel[T: QAbstractListItem](QAbstractListModel):
    def __init__(self, role_names: Dict[IntEnum, bytes], parent=None):
        super().__init__(parent=parent)
        self._data: [T] = []
        self.ROLE_NAMES: Dict[IntEnum, bytes] = role_names
        
    def roleNames(self) ->  Dict[IntEnum, bytes]:
        return self.ROLE_NAMES

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)
    
    def data(self, index: QModelIndex, role: int):
        if role not in list(self.ROLE_NAMES):
            return None

        if not self._data:
            return None

        if not index.isValid():
            return None

        try:
            device: T = self._data[index.row()]
            return device[role]
        except (IndexError, KeyError):
            logger.error(f'Cannot get data from the model.')
            return None

        return None
    
    def insertRow(self, new_row: T, row: int, parent=QModelIndex()) -> bool:
        return self.insertRows([new_row], row, 1)

    def insertRows(self, new_rows: [T], row: int, count: int, index=QModelIndex()) -> bool:
        self.beginInsertRows(QModelIndex(), row, row + count - 1)

        for i in range(count):
            self._data.insert(row, new_rows[i])

        self.endInsertRows()
        return True
    
    def setData(self, index: QModelIndex, value: T, role=IntEnum) -> bool:
        if role not in list(IntEnum):
            return False
        try:
            data: T = self._data[index.row()]
            data[role] = value[role]
        except (IndexError, KeyError):
            logger.error(f'Cannot set data to CameraModel.')
            return False
        
        self.dataChanged.emit(index, index, [role])
        return True
    
    @Slot('QVariant')
    def append(self, item: T):
        self.insertRow(item, self.rowCount())