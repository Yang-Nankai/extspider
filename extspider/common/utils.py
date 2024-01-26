# -*- coding: utf-8 -*-
import re


def is_valid_extension_id(identifier: str) -> bool:
    # [a-p]{32}
    pattern = r'^[a-p]{32}$'
    match = re.match(pattern, identifier)
    return bool(match)


