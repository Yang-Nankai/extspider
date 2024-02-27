import functools
import json
import os
import sys
import traceback
import inspect
import logging
import requests
import html
import unittest
from socket import socket
from typing import Callable
from extspider.common.configuration import (LOG_PATH, FEISHU_WEBHOOK_URL,
                                            IS_FEISHU_ENABLED)
from extspider.common.utils import request_retry_with_backoff
from extspider.common.exception import MaxRequestRetryError

# Use project root as destination folder for log file
LOG_FILE_NAME = "runtime.log"
LOG_FILE_PATH = os.path.join(LOG_PATH, LOG_FILE_NAME)


# TODO: 这里可以用到donwload的下载逻辑中
def cleanup_file(file_path):
    """Decorator to clean up a file after executing a unit test."""

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            try:
                # Run the test method
                test_func(*args, **kwargs)
            finally:
                # Clean up the file
                if os.path.exists(file_path):
                    os.remove(file_path)

        return wrapper

    return decorator


def use_test_samples(test_samples: list):
    """
    Decorator to run a unit test on a list of samples.
    Indicates the failing sample if an exception is raised.

    Args:
        test_samples (list[Any]): The sample arguments for the test method.
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(self):
            for index, sample in enumerate(test_samples):
                try:
                    test_func(self, sample)
                except Exception as e:
                    truncated = (
                        str(sample)[:40] + '...'
                        if len(str(sample)) > 40 else str(sample))
                    raise type(e)(
                        f"Test failed for sample at index {index}: {truncated}"
                    ) from e

        return wrapper

    return decorator


# region CONNECTIVITY TEST
# Global variable to cache the internet connectivity test result
_is_internet_connected = None


def is_internet_connected(host="8.8.8.8", port=53, timeout=3) -> bool:
    """
    Checks if the host machine has Internet connectivity.
    Caches the result to avoid redundant checks.

    Args:
        host (str, optional): Defaults to "8.8.8.8".
        port (int, optional): Defaults to 53.
        timeout (int, optional): Amount of seconds before timing out.
            Defaults to 3.

    Returns:
        bool: True if the host machine is connected; False otherwise.
    """
    global _is_internet_connected
    if _is_internet_connected is None:
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            ).connect((host, port))
            _is_internet_connected = True
        except socket.error:
            _is_internet_connected = False
    return _is_internet_connected


def skip_unless_internet_connected(func):
    """
    Decorator to skip a test method if there is no Internet connectivity.
    """

    @functools.wraps(func)
    @unittest.skipUnless(is_internet_connected(),
                         "Internet connection is required for this test")
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return wrapper


class FeishuMessenger:
    HEADERS = {"Content-Type": "application/json"}

    @request_retry_with_backoff(max_retries=3, retry_interval=1)
    def send_message(self, message_content: str) -> bool:
        if not IS_FEISHU_ENABLED:
            return

        payload = {
            "msg_type": "text",
            "content": {
                "text": message_content
            }
        }

        try:
            response = requests.post(FEISHU_WEBHOOK_URL,
                                     headers=self.HEADERS,
                                     data=json.dumps(payload))
            response.raise_for_status()
        except MaxRequestRetryError as e:
            print(f"Failed to senf feishu message: {str(e)}")
            return False

        return True


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    get_logger instantiates a logger object which will store all logs in a
    predefined log file -- the file is created if it does not exist.
    Additionally, if telegram parameters have been set in the
    `configuration.ini` file, it integrates the logger with the Telegram API

    Args:
        name (str): the logging name space
        level (int, optional): minimum severity level to be logged - defaults
        to logging.INFO (i.e. 20)

    Returns:
        logging.Logger: the created logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    setup_logging_stream_handler(logger)  # log to terminal
    setup_logging_file_handler(logger)

    return logger


def setup_logging_stream_handler(logger: logging.Logger) -> None:
    """
    setup_logging_stream_handler attaches a stream handler to a logger object
    to log to stdout

    Args:
        logger (logging.Logger): the logger object to be attached
    """
    handler = logging.StreamHandler(sys.stdout)  # log to terminal
    handler.setFormatter(
        logging.Formatter(
            '%(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)


def setup_logging_file_handler(logger: logging.Logger) -> None:
    """
    setup_logging_file_handler attaches a file handler to a logger object

    Args:
        logger (logging.Logger): the logger object to be attached
    """
    handler = logging.FileHandler(LOG_FILE_PATH)
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)


def generate_arguments_representation(*args, **kwargs):
    """
    generate_arguments_representation generates a list containing the
    representation (repr) of all received positional arguments and keyword
    arguments
    """
    positional_arguments = [repr(a) for a in args]
    keyword_arguments = [f"{key}={repr(value)}"
                         for key, value
                         in kwargs.items()]

    all_arguments_list = positional_arguments + keyword_arguments
    return ", ".join(all_arguments_list)


def monitor_function(function: Callable):
    """
    monitor_function function decorator to log input/output variables and
    raised exceptions
    """

    def wrapper(*args, **kwargs):
        # Extract keyword and positional arguments passed to the function
        arguments_representation = generate_arguments_representation(*args,
                                                                     **kwargs)

        # Get filename from which the decorated function has been called
        origin_file_path = inspect.stack()[1].filename
        origin_filename = os.path.basename(origin_file_path)

        logger = get_logger(f"{origin_filename}::{function.__name__}")

        # Log function details before execution
        # Avoid HTML-conflicting characters
        logger.info("Arguments: %s", arguments_representation)
        try:
            # Call function and log returned value
            return_value = function(*args, **kwargs)
            logger.info("Returned: %s", repr(return_value))
        except:
            # Log occured exception
            logger.exception(traceback.format_exc())
            raise

        # If no exception occured pass the returned value
        return return_value

    # Return the pointer to the function
    return wrapper
