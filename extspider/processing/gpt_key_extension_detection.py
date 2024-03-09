# -*- coding: utf-8 -*-
import json
import re
import os
from io import BytesIO
from zipfile import ZipFile, BadZipFile
from extspider.storage.database_handle import DatabaseHandle
from extspider.storage.models.extension import Extension
from extspider.storage.extension_handle import ExtensionHandle
from extspider.storage.crx_archive import CrxArchive
from extspider.common.context import DATA_PATH

GPT_KEY_EXTRACT_FILE = os.path.join(DATA_PATH, "gpt_key_extract_result.json")


def find_gpt_key_in_zip(crx_path: str):
    pattern = re.compile(rb'sk-[a-zA-Z0-9]{48}')
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
                            found_strings.append((file_name, match))
        except BadZipFile:
            return []

    return found_strings


def main():
    total_result = []
    # 1.查询得到名字里面存在gpt的extension_id、version
    session = DatabaseHandle.get_session()

    extensions = session.query(
        Extension.id, Extension.version
    ).filter(Extension.name.like('%gpt%')).all()

    # 2.根据id+version得到crx，然后存放在结果集中

    for extension in extensions:
        download_path = ExtensionHandle.get_extension_storage_path(
            extension[0],
            extension[1]
        )

        result = find_gpt_key_in_zip(download_path)
        info = {
            extension[0]: [
                extension[1],
                result
            ]
        }
        total_result.append(info)

        if len(result) > 0:
            print(f"The crx {extension[0]} {extension[1]} exists the gpt-key:\n"
                  f"{result}\n")

    # 3. 存放在目标文件中
    with open(GPT_KEY_EXTRACT_FILE, "w") as file:
        json.dump(total_result, file)
