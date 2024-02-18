import os
import sys
import traceback
import inspect
import logging
import html
from typing import Callable
from extspider.common.configuration import LOG_PATH

# Use project root as destination folder for log file
LOG_FILE_NAME = "runtime.log"
LOG_FILE_PATH = os.path.join(LOG_PATH, LOG_FILE_NAME)


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
