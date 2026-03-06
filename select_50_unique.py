#!/usr/bin/env python3
"""选择50张与user_images不重复的图片"""
import json
from collections import Counter

def main():
    # 读取所有唯一图片
    all_unique = {}
    with open("outputs/jewelry_export_large/ghost_jewelry_20260302_115626.jsonl", 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            url = record.get('original_image_url')
            if url and url not in all_unique:
                all_unique[url] = record

    # 读取user_images中的URL
    user_urls = set()
    with open("outputs/jewelry_export_large/selected_20.jsonl", 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            url = record.get('original_image_url')
            if url:
                user_urls.add(url)

    print(f"总唯一图片: {len(all_unique)}")
    print(f"user_images已用: {len(user_urls)}")

    # 排除user_images中的
    available = {url: rec for url, rec in all_unique.items() if url not in user_urls}
    print(f"可用新图片: {len(available)}")

    # 选择50张（如果有的话）
    num_to_select = min(50, len(available))
    selected = list(available.values())[:num_to_select]

    print(f"选择: {len(selected)} 张")

    # 保存
    output_path = "outputs/jewelry_export_large/selected_50_new.jsonl"
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in selected:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    # 统计日期
    dates = [r.get('date') for r in selected]
    date_dist = Counter(dates)
    print(f"\n日期分布:")
    for date, count in sorted(date_dist.items()):
        print(f"  {date}: {count}张")

    print(f"\n时间范围: {selected[0].get('date')} 到 {selected[-1].get('date')}")
    print(f"已保存到: {output_path}")

if __name__ == "__main__":
    main()
