#!/usr/bin/env python3
"""
从各个类别抽取图片到batch文件夹的子文件夹
- 戒指、项链、耳环、手链：各取15张
- 手镯：只有9张，全部取
- 按顺序编号：类别_序号.jpg，存放在batch/类别/下
"""
import shutil
from pathlib import Path


def create_batch_dataset():
    """创建批量数据集"""

    # 配置
    categories = {
        "戒指": 15,
        "项链": 15,
        "耳环": 15,
        "手镯": 9,  # 全部
        "手链": 15
    }

    batch_dir = Path("data/batch")
    batch_dir.mkdir(exist_ok=True)

    # 清空batch目录
    for item in batch_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    print("📦 创建批量数据集（按类别组织）")
    print("="*80)

    for category, count in categories.items():
        source_dir = Path(f"data/{category}")

        if not source_dir.exists():
            print(f"⚠️  {category} 目录不存在，跳过")
            continue

        # 创建类别子文件夹
        category_batch_dir = batch_dir / category
        category_batch_dir.mkdir(exist_ok=True)

        # 获取所有图片并按名称排序
        images = sorted(list(source_dir.glob("*.jpg")))

        # 取前N张
        images_to_copy = images[:count]

        print(f"\n{category}/: {len(images_to_copy)}张")

        # 复制并编号（从01开始）
        for idx, img_path in enumerate(images_to_copy, 1):
            # 生成新文件名：类别_序号.jpg
            new_name = f"{category}_{idx:02d}.jpg"
            dest_path = category_batch_dir / new_name

            shutil.copy2(img_path, dest_path)
            print(f"  {new_name}")

    print(f"\n{'='*80}")
    print(f"✅ 完成！图片已保存到 {batch_dir}")
    print(f"{'='*80}\n")

    # 统计
    total = sum(categories.values())
    print(f"📊 总计: {total}张")
    for category, count in categories.items():
        print(f"  {category}/: {count}张")


if __name__ == "__main__":
    create_batch_dataset()
