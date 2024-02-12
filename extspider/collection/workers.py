import logging
import time
import traceback
from datetime import timedelta
from logging import Logger
from abc import ABC as AbstractClass, abstractmethod
from typing import Any, List, Optional, Union, Iterator, Self
from queue import Queue, Empty as EmptyQueue
from threading import Event, Lock

from extspider.common.configuration import BACKLOG_LIMIT
from extspider.storage.archive_handle import ArchiveHandle
from extspider.storage.crx_archive import CrxArchive


class Counter:

    def __init__(self, start_value: int=0) -> None:
        self._count = start_value
        self.count_lock = Lock()

    @property
    def count(self) -> int:
        with self.count_lock:
            return self._count
        
    @count.setter
    def count(self, value: int) -> None:
        with self.count_lock:
            self._count = value

    def __str__(self) -> str:
        return str(self.count)
    
    def __int__(self) -> int:
        return self.count
    
    def __add__(self, other: Union[int, Self]) -> Self:
        return Counter(self.count + int(other))

    def increment(self, amount: int=1):
        with self.count_lock:
            self._count += amount

    def decrement(self, amount: int=1):
        with self.count_lock:
            self._count -= amount

    def __lt__(self, other: Union[int, Self]) -> bool:
        return self.count < int(other)
    
    def __gt__(self, other: Union[int, Self]) -> bool:
        return self.count > int(other)
    
    def __eq__(self, other: Union[int, Self]) -> bool:
        return self.count == int(other)
    
    def __truediv__(self, other: Union[int, Self]) -> float:
        if int(other) == 0:
            raise ZeroDivisionError("Division by zero")
        return self.count / int(other)
