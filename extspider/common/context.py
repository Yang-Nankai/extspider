# -*- coding: utf-8 -*-
import os

common_package_path = os.path.dirname(__file__)
PACKAGE_ROOT = os.path.join(common_package_path, "..")
PROJECT_ROOT = os.path.join(PACKAGE_ROOT, "..")

DATA_PATH = os.path.join(PROJECT_ROOT, "data")
CONF_PATH = os.path.join(PROJECT_ROOT, "conf")
ASSETS_PATH = os.path.join(PROJECT_ROOT, "assets")
TESTS_PATH = os.path.join(PROJECT_ROOT, "tests")

TEST_SAMPLES_PATH = os.path.join(ASSETS_PATH, "test_samples")