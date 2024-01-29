# -*- coding: utf-8 -*-
import sys
from typing import List


def read_extension_ids(filename: str):
    """Read extension ids from a file and return a set."""
    try:
        with open(filename, 'r', encoding='UTF-8') as file:
            extension_ids = {line.strip() for line in file}
        return extension_ids
    except IOError as e:
        print("Read File Error: ", e)
        sys.exit()


def write_diff_result(diff_result_filename: str, diff_result: list):
    """Write the difference result to a file."""
    try:
        with open(diff_result_filename, 'w') as file:
            file.writelines(diff_result)
    except IOError as e:
        print("Write File Error: ", e)
        sys.exit()


def generate_diff_result(old_ids_filename: str, new_ids_filename: str) -> List[str]:
    """Generate the different ids from two extension_ids files."""
    old_extension_ids = read_extension_ids(old_ids_filename)
    new_extension_ids = read_extension_ids(new_ids_filename)

    # Calculate the differences between two sets
    deleted_extension_ids = old_extension_ids.difference(new_extension_ids)
    added_extension_ids = new_extension_ids.difference(old_extension_ids)

    # Generate the difference result
    diff_result = [f"[-] {extension_id}\n" for extension_id in deleted_extension_ids]
    diff_result += [f"[+] {extension_id}\n" for extension_id in added_extension_ids]

    return diff_result
