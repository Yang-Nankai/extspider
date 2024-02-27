# -*- coding: utf-8 -*-
import random
import re
import string
import requests
import time
import json
from typing import List
from extspider.common.exception import (InvalidDetailResponseFormat,
                                        MaxRequestRetryError)
from requests.exceptions import RequestException, HTTPError

DETAILS_PATTERN = re.compile(r'(\[\[.*\]\])')


def is_valid_extension_id(identifier: str) -> bool:
    # [a-p]{32}
    pattern = r'^[a-p]{32}$'
    match = re.match(pattern, identifier)
    return bool(match)


def is_valid_extension_version(version: str) -> bool:
    pattern = re.compile(r'^(\d+\.)?(\d+\.)?(\d+)(\.\d+)*$')
    return bool(pattern.match(version))


def details_response_to_json_format(response_text: str) -> List:
    """Remove irrelevant content from the response and convert it
            into List type data using the JSON library."""
    details_match = re.findall(DETAILS_PATTERN, response_text)
    if details_match:
        details = json.loads(json.loads(details_match[0])[0][2])
        return details
    else:
        raise InvalidDetailResponseFormat("The details response format is incorrect.")


def request_retry_with_backoff(max_retries=3, retry_interval=1):
    def decorator(func):
        def _request_retry_with_backoff(*args, **kwargs):
            retries = 0
            result = False

            while retries < max_retries:
                try:
                    result = func(*args, **kwargs)
                except (RequestException, HTTPError) as e:
                    # Log or handle the exception if needed
                    print(f"RequestException: {str(e)}, retrying...")
                    result = False

                if result:
                    break

                retries += 1
                time.sleep(retry_interval)

            if not result:
                raise MaxRequestRetryError

            return result

        return _request_retry_with_backoff

    return decorator


def get_random_extension_id() -> str:
    encoded_digits = string.ascii_lowercase[:16]
    return "".join(random.choice(encoded_digits) for _ in range(32))


def get_random_extension_version():
    num_parts = random.randint(1, 4)  # 这里我们限制了1到4部分
    parts = [str(random.randint(0, 9999)) for _ in range(num_parts)]
    return '.'.join(parts)
