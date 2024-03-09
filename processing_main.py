# -*- coding: utf-8 -*-
import os
from extspider.processing.gpt_key_extension_detection import get_all_gpt_key
from extspider.processing.extension_daily_change import get_daily_manifest_version_change
from extspider.processing.process_chart_drawing import daily_manifest_version_counter

if __name__ == '__main__':
    # get_all_gpt_key()
    get_daily_manifest_version_change("2024_03_01", "2024_03_08")
    daily_manifest_version_counter()

