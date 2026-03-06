#!/usr/bin/env python3
"""
移动无效图片到单独目录
基于图像质量检测报告移动文件
"""
import os
import sys
import json
import shutil
from pathlib import Path


def move_invalid_images(report_file: str, input_dir: str, invalid_dir: str = "data/invalid_images"):
    """根据检测报告移动无效图片"""

    # 读取报告
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)

    input_path = Path(input_dir)
    invalid_path = Path(invalid_dir)

    # 创建无效图片目录
    invalid_path.mkdir(parents=True, exist_ok=True)

    # 统计信息
    moved_count = 0
    skip_count = 0

    print(f"\n{'='*80}")
    print(f"📦 移动无效图片")
    print(f"{'='*80}")
    print(f"输入目录: {input_dir}")
    print(f"无效图片目录: {invalid_dir}")
    print(f"{'='*80}\n")

    # 移动每张无效图片
    for result in report['results']:
        if not result['valid']:
            filename = result['filename']
            src_file = input_path / filename
            dst_file = invalid_path / filename

            if src_file.exists():
                try:
                    shutil.move(str(src_file), str(dst_file))
                    moved_count += 1
                    if moved_count <= 10 or moved_count % 50 == 0:
                        print(f"[{moved_count}] 移动: {filename}")
                        print(f"        原因: {result['reason']}")
                except Exception as e:
                    print(f"❌ 移动失败: {filename} - {e}")
                    skip_count += 1
            else:
                skip_count += 1

    print(f"\n{'='*80}")
    print(f"📊 移动统计")
    print(f"{'='*80}")
    print(f"成功移动: {moved_count}")
    print(f"跳过: {skip_count}")
    print(f"剩余有效图片: {report['valid_images']}")
    print(f"{'='*80}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='移动无效图片到单独目录',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 使用最新报告移动无效图片
  python tools/move_invalid_images.py \\
    --report data/image_quality_report_20260304_194642.json \\
    --input data/all
        """
    )

    parser.add_argument('--report', type=str, required=True, help='检测报告文件路径')
    parser.add_argument('--input', type=str, default='data/all', help='输入目录')
    parser.add_argument('--output', type=str, default='data/invalid_images', help='无效图片输出目录')

    args = parser.parse_args()

    if not Path(args.report).exists():
        print(f"❌ 错误: 报告文件不存在 - {args.report}")
        return 1

    move_invalid_images(args.report, args.input, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
