import csv
import os.path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from extspider.common.context import DATA_PATH


def daily_manifest_version_counter():
    # CSV 文件路径
    csv_file_path = os.path.join(DATA_PATH,"chrome_daily_processing",
                                 "chrome_daily_v2_v3_change.csv")

    # 使用日期格式
    date_format = "%Y_%m_%d"

    # 初始化数据存储列表
    dates = []
    version2_counts = []
    version3_counts = []

    # 打开并读取 CSV 文件
    with open(csv_file_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            dates.append(datetime.strptime(row[0], date_format))  # 转换日期字符串为 datetime 对象
            print(dates)
            version2_counts.append(int(row[1]))  # version3 的个数
            version3_counts.append(int(row[2]))  # version2 的个数

    # 使用matplotlib绘制趋势图
    plt.figure(figsize=(10, 5))  # 设置图的大小
    plt.plot(dates, version2_counts, label='version3', marker='o', linestyle='-')  # 绘制 version3 趋势线
    plt.plot(dates, version3_counts, label='version2', marker='s', linestyle='-')  # 绘制 version2 趋势线

    # 设置标题和标签
    plt.title('Version 2 and Version 3 Counts Over Time')
    plt.xlabel('Date')
    plt.ylabel('Count')

    # 更好的日期格式化
    formatter = mdates.DateFormatter('%Y-%m-%d')  # 日期显示格式
    plt.gca().xaxis.set_major_formatter(formatter)

    plt.legend()  # 显示图例
    plt.tight_layout()  # 调整布局
    plt.show()  # 显示图形
