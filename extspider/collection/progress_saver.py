# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Optional, List
from extspider.common.context import DATA_PATH
import json


class ProgressSaver(ABC):
    @abstractmethod
    def save_progress(self, status: int, scraped_categories: Optional[List[str]] = None,
                      now_category: Optional[str] = None, token: Optional[str] = None,
                      break_reason: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def load_progress(self) -> Optional[dict]:
        pass


class ChromeProgressSaver(ProgressSaver):
    def __init__(self, filename: str = "chrome_progress.json"):
        self.filename = f"{DATA_PATH}/{filename}"

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

    def load_progress(self) -> Optional[dict]:
        try:
            with open(self.filename, "r") as file:
                progress = json.load(file)
            return progress
        except FileNotFoundError:
            return None
