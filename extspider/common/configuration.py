import yaml
import os
from typing import Any, Optional

from extspider.common import context


DEFAULT_PATH = os.path.join(context.CONF_PATH, "scraper_configuration.yaml")


class ConfigurationError(Exception):
    pass


class ScraperConfiguration:

    _configuration:dict = None


    def __init__(self, path:str=DEFAULT_PATH) -> None:
        self.configuration_path = self.check_path(path)


    @property
    def configuration(self) -> dict:
        return type(self)._configuration


    @configuration.setter
    def configuration(self, data:dict) -> None:
        type(self)._configuration = self.check_configuration(data)


    @staticmethod
    def check_path(path:str) -> str:
        if not os.path.isfile(path):
            raise ConfigurationError(f"{path} not found.")

        return path


    @staticmethod
    def check_configuration(data:Any) -> dict:
        if data is None or not isinstance(data, dict):
            raise ConfigurationError(f"{data} is not a valid configuration")
        return data


    def load_configuration(self) -> dict:

        if self.configuration is not None:
            return self.configuration

        # Open the YAML file and load its contents
        with open(self.configuration_path, 'r') as yaml_file:
            self.configuration = yaml.safe_load(yaml_file)

        # Save configuration to class variable with property setter
        return self.setup()


    def set(self, key, value) -> None:
        self.configuration[key] = value


    def get(self, key) -> Optional[Any]:
        return self.configuration.get(key)


    def setup(self) -> dict:
        if (os.getenv("DOCKER_DRIVER_PATH") is not None
            and os.getenv("DOCKER_BROWSER_PATH") is not None):

            browser = self.configuration["chrome_parameters"]
            browser["driver_path"] = os.getenv("DOCKER_DRIVER_PATH")
            browser["browser_path"] = os.getenv("DOCKER_BROWSER_PATH")
            self.set("chrome_parameters", browser)

        # TODO: include configuration files in docker bind path
        if os.getenv("DOCKER_BIND_PATH") is not None:
            self.set("data_path", os.getenv("DOCKER_BIND_PATH"))
            self.set("storage_path", os.getenv("DOCKER_BIND_PATH"))
            self.set("log_path", os.getenv("DOCKER_BIND_PATH"))
        else:
            self.set("db_path", context.DATA_PATH)
            self.set("storage_path", context.DATA_PATH)
            self.set("log_path", context.PROJECT_ROOT)


        telegram_parameters = self.configuration.get("telegram_parameters")
        if (telegram_parameters is not None
            and telegram_parameters.get("token") is not None
            and telegram_parameters.get("user_id") is not None):

            self.set("is_telegram_enabled", True)
        else:
            self.set("is_telegram_enabled", False)

        return self.configuration


CONFIGURATION = ScraperConfiguration().load_configuration()

# Output paths
STORAGE_PATH = CONFIGURATION["storage_path"]
DB_PATH = CONFIGURATION["db_path"]
LOG_PATH = CONFIGURATION["log_path"]

# Browser
DRIVER_PATH = CONFIGURATION["chrome_parameters"]["driver_path"]
BROWSER_PATH = CONFIGURATION["chrome_parameters"]["browser_path"]
BROWSER_ARGUMENTS = CONFIGURATION["chrome_parameters"]["browser_arguments"]

# Scraper
COLLECTORS_AMOUNT = CONFIGURATION["scraper_parameters"]["collectors_amount"]
BACKLOG_LIMIT = CONFIGURATION["scraper_parameters"]["backlog_limit"]
TIMEOUT_SECONDS = CONFIGURATION["scraper_parameters"]["timeout_seconds"]
UPDATE_SECONDS = CONFIGURATION["scraper_parameters"]["update_seconds"]
STORE_URL = CONFIGURATION["scraper_parameters"]["store_url"]
CSS_SELECTORS = CONFIGURATION["scraper_parameters"]["css_selectors"]

# Telegram
TELEGRAM_TOKEN = None
TELEGRAM_USER_ID = None
IS_TELEGRAM_ENABLED = CONFIGURATION["is_telegram_enabled"]
if IS_TELEGRAM_ENABLED:
    TELEGRAM_TOKEN = CONFIGURATION["telegram_parameters"]["token"]
    TELEGRAM_USER_ID = CONFIGURATION["telegram_parameters"]["user_id"]
