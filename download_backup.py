#!/usr/bin/env python3
"""下载50张备用图片"""
import json
import urllib.request
from pathlib import Path

jsonl_path = "outputs/jewelry_export_large/selected_50.jsonl"
output_dir = Path("data/backup")
output_dir.mkdir(parents=True, exist_ok=True)

downloaded = 0
failed = 0

with open(jsonl_path, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        record = json.loads(line)
        url = record.get('original_image_url')
        record_id = record.get('record_id')
        date = record.get('date')

        if not url:
            continue

        filename = f"original_{date}_{record_id:05d}.jpg"
        dest_path = output_dir / filename

        try:
            urllib.request.urlretrieve(url, dest_path)
            print(f"✓ [{date}] {filename}")
            downloaded += 1
        except Exception as e:
            print(f"✗ Failed: {filename} - {e}")
            failed += 1

print(f"\n总计: {downloaded} 成功, {failed} 失败")
