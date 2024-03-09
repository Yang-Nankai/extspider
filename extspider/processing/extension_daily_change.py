import csv
import os.path

import pandas as pd
from pathlib import Path
from typing import Iterable, Optional, List, Set, Tuple
from extspider.common.context import DATA_PATH

CHROME_DAILY_PROCESSING = os.path.join(DATA_PATH, "chrome_daily_processing")

# TODO:后续将这个设置为一个类


def get_id_difference_set(f_path: str, s_path: str) -> Set[str]:
    # 读取两个CSV文件的第一列数据
    first_df = pd.read_csv(f_path, usecols=[0])
    second_df = pd.read_csv(s_path, usecols=[0])

    # 将第一列数据转为set
    first_set = set(first_df.iloc[:, 0])
    second_set = set(second_df.iloc[:, 0])

    # 计算差集
    difference_set = first_set - second_set

    return difference_set


def get_id_version_difference_set(f_path: str, s_path: str) -> Set[Tuple[str, str]]:
    # 读取两个CSV文件的第一列数据
    first_df = pd.read_csv(f_path, usecols=[0, 1])
    second_df = pd.read_csv(s_path, usecols=[0, 1])

    # 将第两列数据转为set
    first_set = set(tuple(x) for x in first_df.to_numpy())
    second_set = set(tuple(x) for x in second_df.to_numpy())

    # 计算差集
    difference_set = first_set - second_set

    return difference_set


def get_version_change_id_set(add_set: Set[str], f_path: str, s_path: str) -> Set[str]:
    result_set = set()
    diff_set = get_id_version_difference_set(f_path, s_path)

    for item in diff_set:
        if item[0] not in add_set:
            result_set.add(item[0])

    return result_set


def extract_data_by_id_set(file_path: str, id_set: Set) -> List:
    df = pd.read_csv(file_path)

    # 提取set对应的完整数据并转为列表
    result_data = df[df.iloc[:, 0].isin(id_set)].values.tolist()

    return result_data


def store_daily_result(store_path: str, result_data: List):
    store_writer = csv.writer(
        open(store_path, 'w', encoding='utf-8', newline='')
    )
    store_writer.writerows(result_data)


def process_daily_deleted(f_path: str, s_path: str, save_filename: str) -> None:
    if not os.path.isfile(f_path):
        raise FileNotFoundError
    if not os.path.isfile(s_path):
        raise FileNotFoundError

    deleted_ids = get_id_difference_set(s_path, f_path)
    deleted_extensions = extract_data_by_id_set(s_path, deleted_ids)

    # 将结果存储到结果文件夹中
    store_file = os.path.join(CHROME_DAILY_PROCESSING, save_filename)
    store_daily_result(store_file, deleted_extensions)