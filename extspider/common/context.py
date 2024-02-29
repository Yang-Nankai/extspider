# -*- coding: utf-8 -*-
import os
from pathlib import Path
from extspider.common.utils import get_today_date_string

common_package_path = os.path.dirname(__file__)
today_string = get_today_date_string()
PACKAGE_ROOT = os.path.join(common_package_path, "..")
PROJECT_ROOT = os.path.join(PACKAGE_ROOT, "..")

DATA_PATH = os.path.join(PROJECT_ROOT, "data")
CONF_PATH = os.path.join(PROJECT_ROOT, "conf")
ASSETS_PATH = os.path.join(PROJECT_ROOT, "assets")
TESTS_PATH = os.path.join(PROJECT_ROOT, "tests")

SCRAPER_CONF_PATH = os.path.join(CONF_PATH, "configuration.yaml")
TEST_SAMPLES_PATH = os.path.join(ASSETS_PATH, "test_samples")

# TODO: 这里针对于DATA的地方要重新考虑一下
IDENTIFIER_DIRECTORY_PATH = Path(DATA_PATH) / "chrome_daily_identifier"
DAILY_IDENTIFIERS_PATH = IDENTIFIER_DIRECTORY_PATH / f"{today_string}_identifiers.txt"

RESULT_DIRECTORY_PATH = Path(DATA_PATH) / "chrome_daily_result"
DAILY_RESULTS_PATH = RESULT_DIRECTORY_PATH / f"{today_string}_results.csv"


# Request Header
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/118.0.5993.90"
    ),
    "Host": "chromewebstore.google.com",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
}
