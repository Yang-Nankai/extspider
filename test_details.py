import re

def is_valid_extension_version(version: str) -> bool:
    # 正则表达式匹配以点分隔的数字序列
    pattern = re.compile(r'^(\d+\.)?(\d+\.)?(\d+)(\.\d+)*$')
    return bool(pattern.match(version))

# 示例使用
print(is_valid_extension_version("0.1.2"))        # 应该输出: True
print(is_valid_extension_version("2025.12.32.123")) # 应该输出: True
print(is_valid_extension_version("82.123"))        # 应该输出: True
print(is_valid_extension_version("1..2"))          # 应该输出: False
print(is_valid_extension_version("a.b.c"))         # 应该输出: False
print(is_valid_extension_version("123"))           # 应该输出: True
print(is_valid_extension_version(""))           # 应该输出: False