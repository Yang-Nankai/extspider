import re
import os
import json
from typing import List
from io import BytesIO
from zipfile import ZipFile, BadZipFile
from extspider.storage.database_handle import DatabaseHandle
from extspider.storage.models.extension import Extension
from extspider.storage.extension_handle import ExtensionHandle
from extspider.storage.crx_archive import CrxArchive
from extspider.common.context import DATA_PATH

GPT_KEY_EXTRACT_FILE = os.path.join(DATA_PATH, "gpt_key_extract_result.json")

# Move the pattern compilation outside the function
pattern = re.compile(rb'sk-[a-zA-Z0-9]{48}')


def find_gpt_key_in_zip(crx_path: str) -> List:
    found_strings = []

    if not os.path.exists(crx_path):
        print(f"No Such Crx File: {crx_path}")
        return []

    with open(crx_path, "rb") as crx_file:
        try:
            CrxArchive.strip_crx_headers(crx_file)
            with ZipFile(BytesIO(crx_file.read()), 'r') as zip_ref:
                for file_name in zip_ref.namelist():
                    with zip_ref.open(file_name) as file:
                        file_content = file.read()
                        matches = pattern.findall(file_content)
                        for match in matches:
                            found_strings.append((file_name, match.decode('utf-8')))
        except BadZipFile:
            return []

    return found_strings


def main():
    try:
        total_result = []
        session = DatabaseHandle.get_session()
        try:
            extensions = session.query(
                Extension.id, Extension.version
            ).filter(Extension.name.like('%gpt%')).all()

            for extension in extensions:
                download_path = ExtensionHandle.get_extension_storage_path(
                    extension[0],
                    extension[1]
                )

                result = find_gpt_key_in_zip(download_path)
                if result:
                    info = {
                        extension[0]: [
                            extension[1],
                            result
                        ]
                    }
                    total_result.append(info)
                    print(f"The crx {extension[0]} {extension[1]} exists the gpt-key:\n"
                          f"{result}\n")
        finally:
            session.close()  # Proper closing of the session

        with open(GPT_KEY_EXTRACT_FILE, "w") as file:
            json.dump(total_result, file, ensure_ascii=False, indent=4)  # Proper JSON dumping with improved readability
    except Exception as e:
        # Consider logging the exception details to a file or logging service
        print(f"An error occurred: {e}")
