# -*- coding: utf-8 -*-

import os
from extspider.common.context import DATA_PATH
from extspider.processing.extension_daily_change import process_daily_deleted

CHROME_DAILY_RESULT = os.path.join(DATA_PATH, "chrome_daily_result")


def main():
    # TODO: 传入指定的文件名，到data文件夹去查找，得到文件名多久的日期，然后去做比较，然后写入结果，这里目前只考虑del掉的
    now_result_file = os.path.join(CHROME_DAILY_RESULT, '2024_03_02_results.csv')
    pre_result_file = os.path.join(CHROME_DAILY_RESULT, '2024_03_01_results.csv')
    str_result_file = '2024_03_02_deleted.csv'
    process_daily_deleted(now_result_file, pre_result_file, str_result_file)


if __name__ == '__main__':
    main()
