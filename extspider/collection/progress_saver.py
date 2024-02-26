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
        # TODO : 对于chrome_progress的路径由configuration指定
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

    def save_uncompleted_progress(self, scraped_categories: List[str],
                                  now_category: str, token: Optional[str]):
        progress = {
            "status": ProgressStatus.UNCOMPLETED.value,
            "scraped_categories": scraped_categories,
            "now_category": now_category,
            "token": token
        }
        with open(self.filename, "w") as file:
            json.dump(progress, file)

    def save_completed_progress(self):
        progress = {
            "status": ProgressStatus.COMPLETED.value,
            "scraped_categories": list(),
            "now_category": "",
            "token": ""
        }
        with open(self.filename, "w") as file:
            json.dump(progress, file)


