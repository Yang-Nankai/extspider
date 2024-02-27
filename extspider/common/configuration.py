import yaml
import os
from typing import Any, Optional
from extspider.common import context

DEFAULT_PATH = os.path.join(context.CONF_PATH, "scraper_configuration.yaml")


class ConfigurationError(Exception):
    pass


class ScraperConfiguration:
    _configuration: dict = None

    def __init__(self, path: str = DEFAULT_PATH) -> None:
        self.configuration_path = self.check_path(path)

    @property
    def configuration(self) -> dict:
        return type(self)._configuration

    @configuration.setter
    def configuration(self, data: dict) -> None:
        type(self)._configuration = self.check_configuration(data)

    @staticmethod
    def check_path(path: str) -> str:
        if not os.path.isfile(path):
            raise ConfigurationError(f"{path} not found.")

        return path

    @staticmethod
    def check_configuration(data: Any) -> dict:
        if data is None or not isinstance(data, dict):
            raise ConfigurationError(f"{data} is not a valid configuration")
        return data

    def load_configuration(self) -> dict:

        if self.configuration is not None:
            return self.configuration

        # Open the YAML file and load its contents
        with open(self.configuration_path, 'r', encoding='utf-8') as yaml_file:
            self.configuration = yaml.safe_load(yaml_file)

        # Save configuration to class variable with property setter
        return self.setup()

    def set(self, key, value) -> None:
        self.configuration[key] = value

    def get(self, key) -> Optional[Any]:
        return self.configuration.get(key)

    def setup(self) -> dict:
        # TODO: include configuration files in docker bind path
        self.set("db_path", context.DATA_PATH)
        self.set("storage_path", context.DATA_PATH)
        self.set("log_path", context.PROJECT_ROOT)

        feishu_parameters = self.configuration.get("feishu_parameters")
        if (feishu_parameters is not None
                and feishu_parameters.get("webhook_url") is not None):
            self.set("is_feishu_enabled", True)
        else:
            self.set("is_feishu_enabled", False)

        return self.configuration


CONFIGURATION = ScraperConfiguration().load_configuration()

# Output paths
STORAGE_PATH = CONFIGURATION["storage_path"]
DB_PATH = CONFIGURATION["db_path"]
LOG_PATH = CONFIGURATION["log_path"]

# Scraper
COLLECTORS_AMOUNT = CONFIGURATION["scraper_parameters"]["collectors_amount"]
BACKLOG_LIMIT = CONFIGURATION["scraper_parameters"]["backlog_limit"]
TIMEOUT_SECONDS = CONFIGURATION["scraper_parameters"]["timeout_seconds"]
UPDATE_SECONDS = CONFIGURATION["scraper_parameters"]["update_seconds"]
STORE_URL = CONFIGURATION["scraper_parameters"]["store_url"]
PROD_VERSION = CONFIGURATION["scraper_parameters"]["prod_version"]
CHROME_CATEGORY_REQUEST_ID = CONFIGURATION["scraper_parameters"]["chrome_category_request_id"]
CHROME_DETAIL_REQUEST_ID = CONFIGURATION["scraper_parameters"]["chrome_detail_request_id"]
CHROME_SCRAPER_ONCE_NUM = CONFIGURATION["scraper_parameters"]["chrome_scraper_once_num"]

# Proxy
PROXIES = CONFIGURATION["scraper_parameters"]["proxies"]

# Feishu
FEISHU_WEBHOOK_URL = None
IS_FEISHU_ENABLED = CONFIGURATION["is_feishu_enabled"]
if IS_FEISHU_ENABLED:
    FEISHU_WEBHOOK_URL = CONFIGURATION["feishu_parameters"]["webhook_url"]