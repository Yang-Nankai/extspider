import matplotlib.pyplot as plt
from extspider.common.context import DATA_PATH

def parse_file_content(file_path):
    with open(file_path, 'r') as file:
        file_content = list(file.readlines())

    # 解析文件内容，返回减少和增加的数量
    decrease_count = 0
    increase_count = 0

    for line in file_content:
        if line.startswith("[-]"):
            decrease_count += 1
        elif line.startswith("[+]"):
            increase_count += 1

    return decrease_count, increase_count

def plot_bar_chart(decrease_counts, increase_counts):
    # 绘制柱形图
    labels = ['28_29', '29_30', '30_31', '31_1']
    x = range(len(labels))

    plt.bar(x, decrease_counts, width=0.4, label='Decrease', color='red')
    plt.bar(x, increase_counts, width=0.4, label='Increase', color='green', bottom=decrease_counts)

    plt.xlabel('Files')
    plt.ylabel('Count')
    plt.title('Decrease and Increase Count for Each File')
    plt.xticks(x, labels)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    file_paths = [
        f"{DATA_PATH}/28_29_diff_result.txt",
        f"{DATA_PATH}/29_30_diff_result.txt",
        f"{DATA_PATH}/30_31_diff_result.txt",
        f"{DATA_PATH}/31_1_diff_result.txt",
    ]

    decrease_counts = []
    increase_counts = []

    for file_content in file_paths:
        decrease_count, increase_count = parse_file_content(file_content)
        decrease_counts.append(decrease_count)
        increase_counts.append(increase_count)

    plot_bar_chart(decrease_counts, increase_counts)
