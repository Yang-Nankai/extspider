# -*- coding: utf-8 -*-
import json
import os
from zipfile import ZipFile
from typing import List, Set, Optional
from extspider.storage.extension_handle import ExtensionHandle
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.storage.crx_archive import CrxArchive


# 根据输入的ids，讲得到的crx文件变为zip文件，然后放在结果集中

def get_extensions_from_ids(ids_list: List[Set], output_dir: str):
    for id, version in ids_list:
        download_path = ExtensionHandle.get_extension_storage_path(
            id,
            version
        )
        extension = ChromeExtensionDetails(id)
        zip_file = extension.get_zip_archive(download_path)
        output_zip_path = os.path.join(output_dir, f"{id}.{version}.zip")
        with ZipFile(zip_file) as zip_memory_file:
            with open(output_zip_path, 'wb') as zip_output_file:
                zip_output_file.write(zip_memory_file.read())


if __name__ == '__main__':
    ids_list = []
    json_file_path = 'gpt_key_extract_result.json'
    with open(json_file_path, 'r') as file:
        # 加载 JSON 数据
        data = json.load(file)
        # 遍历列表，获取每个字典中的第一和第二个字符串
        for key, value in dict(data).items():
            ids_list.append((key, value[0]))

    get_extensions_from_ids(ids_list, "D:\Ph0Jav7\科研任务\extspider\output")