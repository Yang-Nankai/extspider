# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from extspider.common.context import DATA_PATH
import json


class ProgressSaver(ABC):
    @abstractmethod
    def save_progress(self, **kwargs):
        pass

    @abstractmethod
    def load_progress(self):
        pass


class ChromeProgressSaver(ProgressSaver):
    def __init__(self, filename="chrome_progress.json"):
        self.filename = f"{DATA_PATH}/{filename}"

    def save_progress(self, status, scraped_categories = None, now_category = None, token = None, break_reason = None):
        progress = {
            "status": status,
            "scraped_categories": scraped_categories,
            "now_category": now_category,
            "token": token,
            "break_reason": break_reason
        }
        with open(self.filename, "w") as file:
            json.dump(progress, file)

    def load_progress(self):
        try:
            with open(self.filename, "r") as file:
                progress = json.load(file)
            return progress
        except FileNotFoundError:
            return None

