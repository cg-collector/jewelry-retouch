#!/usr/bin/env python3
"""从导出的数据中选择时间分散的唯一图片"""

import json
import sys
from collections import OrderedDict

def select_diverse_images(jsonl_path, num_images=20):
    """选择时间分散的唯一图片"""

    # 读取数据并按original URL去重
    unique_images = {}
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            url = record.get('original_image_url')
            if url and url not in unique_images:
                unique_images[url] = record

    # 按日期排序
    sorted_by_date = sorted(
        unique_images.values(),
        key=lambda x: x.get('create_at', '')
    )

    # 均匀采样
    total = len(sorted_by_date)
    step = max(1, total // num_images)

    selected = []
    for i in range(0, min(total, num_images * step), step):
        selected.append(sorted_by_date[i])
        if len(selected) >= num_images:
            break

    # 如果不够20张，从后面补充
    if len(selected) < num_images and total > num_images:
        remaining = num_images - len(selected)
        selected.extend(sorted_by_date[-remaining:])

    print(f"从 {total} 张唯一图片中选择了 {len(selected)} 张")
    print(f"时间范围: {selected[0].get('date')} 到 {selected[-1].get('date')}")

    return selected

def main():
    jsonl_path = "outputs/jewelry_export_large/ghost_jewelry_20260302_115626.jsonl"
    output_path = "outputs/jewelry_export_large/selected_20.jsonl"

    selected = select_diverse_images(jsonl_path, num_images=20)

    # 保存选择的记录
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in selected:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"已保存到: {output_path}")

    # 打印选择的图片信息
    print("\n=== 选择的20张图片 ===")
    for i, r in enumerate(selected, 1):
        print(f"{i:2d}. {r.get('date')} - record_id: {r.get('record_id')}")

if __name__ == "__main__":
    main()
