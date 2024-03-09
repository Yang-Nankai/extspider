import csv
import os.path
import pandas as pd
from collections import Counter
from datetime import datetime, timedelta
from typing import Iterable, Optional, List, Set, Tuple
from extspider.common.context import DATA_PATH

CHROME_DAILY_RESULT = os.path.join(DATA_PATH, "chrome_daily_result")
CHROME_DAILY_PROCESSING = os.path.join(DATA_PATH, "chrome_daily_processing")
CHROME_V2_V3_CHANGE = os.path.join(CHROME_DAILY_PROCESSING, "chrome_daily_v2_v3_change.csv")


# TODO: 后续将这个设置为一个类
# TODO: 完成测试类，还没有完全完成测试类


def get_daily_v2_v3_change(result_path: str, date_str: str) -> List:
    if not os.path.exists(result_path):
        raise FileNotFoundError("Daily result file not found.")
    manifest_version_df = pd.read_csv(result_path, usecols=[2])
    # 将其转为list
    manifest_version_list = list(manifest_version_df.iloc[:, 0])
    counter_dict = Counter(manifest_version_list)

    # 这里不太好看，需要做review
    return [date_str, counter_dict[3], counter_dict[2]]


def get_daily_manifest_version_change(start_date: str, end_date: str):
    date_format = "%Y_%m_%d"  # 我们期望的日期格式
    result_data = []

    try:
        # 尝试将字符串转换为 datetime 对象
        start_date = datetime.strptime(start_date, date_format)
        end_date = datetime.strptime(end_date, date_format)
        # 得到天数
        date_diff = end_date - start_date
        for day in range(date_diff.days + 1):
            current_date = start_date + timedelta(days=day)
            # 得到日期和文件
            date_str = current_date.strftime(date_format)
            result_path = os.path.join(CHROME_DAILY_RESULT, f"{date_str}_results.csv")
            # 得到数据并写入
            daily_data = get_daily_v2_v3_change(result_path, date_str)
            result_data.append(daily_data)

        store_writer = csv.writer(
            open(CHROME_V2_V3_CHANGE, 'a', encoding='utf-8', newline='')
        )
        store_writer.writerows(result_data)

    except ValueError as e:
        # 如果输入的字符串不符合期望的格式就报错
        print(f"Error: '{e}'")


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


def find_daily_deleted(now_day_path: str, pre_day_path: str, save_filename: str) -> None:
    if not os.path.isfile(now_day_path):
        raise FileNotFoundError("Now day file not found")
    if not os.path.isfile(pre_day_path):
        raise FileNotFoundError("Previous day file not found")

    deleted_ids = get_id_difference_set(pre_day_path, now_day_path)
    deleted_extensions = extract_data_by_id_set(pre_day_path, deleted_ids)

    # 将结果存储到结果文件夹中
    store_file = os.path.join(CHROME_DAILY_PROCESSING, save_filename)
    store_daily_result(store_file, deleted_extensions)



