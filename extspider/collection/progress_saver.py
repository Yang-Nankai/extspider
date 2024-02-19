# -*- coding: utf-8 -*-
import json
from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from extspider.common.context import DATA_PATH


class ProgressStatus(Enum):
    UNCOMPLETED = 0
    COMPLETED = 1


class ProgressSaver(ABC):
    @abstractmethod
    def save_progress(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def progress_info(self) -> Optional[Dict]:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_finished(self) -> bool:
        raise NotImplementedError


class ChromeProgressSaver(ProgressSaver):
    def __init__(self, filename: str = "chrome_progress.json"):
        # TODO: 对于chrome_progress的路径由configuration指定
        self.filename = f"{DATA_PATH}/{filename}"

    @property
    def is_finished(self) -> bool:
        progress = self.progress_info
        if progress:
            status = progress.get("status")
            if status == ProgressStatus.UNCOMPLETED.value:
                return False

        return True

    @property
    def progress_info(self) -> Optional[Dict]:
        try:
            with open(self.filename, "r") as file:
                progress = json.load(file)
            return progress
        except FileNotFoundError:
            return None

    def save_progress(self, status: int, scraped_categories: List[str] = [],
                      now_category: Optional[str] = None, token: Optional[str] = None,
                      break_reason: Optional[str] = None) -> None:
        progress = {
            "status": status,
            "scraped_categories": scraped_categories,
            "now_category": now_category,
            "token": token,
            "break_reason": break_reason
        }
        with open(self.filename, "w") as file:
            json.dump(progress, file)

