#!/usr/bin/env python3
"""合并所有珠宝数据并下载唯一图片"""
import json
import os
from collections import OrderedDict

# 读取所有珠宝数据并去重（按original_image_url）
unique_images = OrderedDict()

files = [
    "outputs/all_jewelry_2025/ghost_jewelry_20260303_212014.jsonl",
    "outputs/all_jewelry_2026/ghost_jewelry_20260303_212135.jsonl",
]

for filepath in files:
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            url = record.get('original_image_url')
            if url and url not in unique_images:
                unique_images[url] = record

print(f"总唯一图片数: {len(unique_images)}")

# 保存合并后的数据
output_path = "outputs/all_jewelry_unique.jsonl"
os.makedirs("outputs", exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    for record in unique_images.values():
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

print(f"已保存到: {output_path}")

# 统计时间范围
dates = [r.get('date') for r in unique_images.values()]
if dates:
    print(f"时间范围: {min(dates)} 到 {max(dates)}")
