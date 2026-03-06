#!/usr/bin/env python3
"""
将batch文件夹中的图片按类别组织到子文件夹
"""
import shutil
from pathlib import Path


def organize_batch_by_category():
    """按类别组织batch数据"""

    batch_dir = Path("data/batch")

    # 类别列表
    categories = ["戒指", "项链", "耳环", "手镯", "手链"]

    print("📁 组织batch数据")
    print("="*80)

    for category in categories:
        # 创建子文件夹
        category_dir = batch_dir / category
        category_dir.mkdir(exist_ok=True)

        # 找到该类别的所有图片
        pattern = f"{category}_*.jpg"
        images = sorted(list(batch_dir.glob(pattern)))

        print(f"\n{category}: {len(images)}张")

        # 移动图片到子文件夹
        for img_path in images:
            dest_path = category_dir / img_path.name
            shutil.move(str(img_path), str(dest_path))
            print(f"  {img_path.name} -> {category}/")

    print(f"\n{'='*80}")
    print(f"✅ 完成！数据已按类别组织到子文件夹")
    print(f"{'='*80}\n")

    # 显示最终结构
    print("📊 数据结构:")
    for category in categories:
        category_dir = batch_dir / category
        if category_dir.exists():
            count = len(list(category_dir.glob("*.jpg")))
            print(f"  batch/{category}/: {count}张")


if __name__ == "__main__":
    organize_batch_by_category()
