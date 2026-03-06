#!/usr/bin/env python3
"""
详细测试进度报告
"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

BASE_OUTPUT_DIR = "temp/all_versions_test_20260305_010655"


def get_file_age(filepath):
    """获取文件年龄（分钟）"""
    mtime = os.path.getmtime(filepath)
    age = (datetime.now() - datetime.fromtimestamp(mtime)).total_seconds() / 60
    return age


def detailed_report():
    """生成详细进度报告"""
    base_path = Path(BASE_OUTPUT_DIR)

    print(f"\n{'='*80}")
    print(f"详细测试进度报告")
    print(f"{'='*80}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    # 检查所有版本目录
    versions = []
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            versions.append(item)

    if len(versions) == 0:
        print("❌ 测试目录为空")
        return

    print(f"总版本数: 14")
    print(f"已开始测试: {len(versions)}\n")

    for version_dir in sorted(versions):
        print(f"{'─'*80}")
        print(f"📁 {version_dir.name}")
        print(f"{'─'*80}")

        results_file = version_dir / "results.json"

        if results_file.exists():
            # 已完成
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results = data.get("results", [])
                total = len(results)
                success = sum(1 for r in results if r.get("status") == "success")
                failed = sum(1 for r in results if r.get("status") == "failed")

            print(f"✅ 状态: 已完成")
            print(f"   成功: {success}/{total} ({success/total*100:.1f}%)")
            print(f"   失败: {failed}/{total}")

        else:
            # 进行中或未开始
            png_files = sorted(list(version_dir.glob("*.png")))

            if len(png_files) == 0:
                print(f"⏸️  状态: 未开始")
            else:
                print(f"⏳ 状态: 进行中")
                print(f"   已生成: {len(png_files)} 张图片")

                if png_files:
                    latest_file = png_files[-1]
                    age = get_file_age(latest_file)
                    print(f"   最新: {latest_file.name} ({age:.1f} 分钟前)")

                    if age > 10:
                        print(f"   ⚠️  警告: 超过10分钟未生成新图片，可能卡住")

                # 检查是否有临时目录
                temp_dirs = [d for d in version_dir.iterdir() if d.is_dir() and d.name.startswith('nano')]
                if temp_dirs:
                    print(f"   📂 临时目录存在，可能正在处理中")

        print()

    print(f"{'='*80}\n")


if __name__ == "__main__":
    detailed_report()
