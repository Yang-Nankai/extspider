# -*- coding: utf-8 -*-
import random
import re
import string

import requests
import time


def is_valid_extension_id(identifier: str) -> bool:
    # [a-p]{32}
    pattern = r'^[a-p]{32}$'
    match = re.match(pattern, identifier)
    return bool(match)


def request_retry_with_backoff(max_retries=3, retry_interval=1):
    def decorator(func):
        def _request_retry_with_backoff(*args, **kwargs):
            retries = 0
            result = False

            while retries < max_retries:
                try:
                    result = func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    # Log or handle the exception if needed
                    print(f"RequestException: {e}, retrying...")
                    result = False

                if result:
                    break

                retries += 1
                time.sleep(retry_interval)

            return result

        return _request_retry_with_backoff

    return decorator


def get_random_extension_id() -> str:
    encoded_digits = string.ascii_lowercase[:16]
    return "".join(random.choice(encoded_digits) for _ in range(32))
