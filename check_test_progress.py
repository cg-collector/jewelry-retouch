#!/usr/bin/env python3
"""
测试进度监控脚本 - 实时查看全版本测试进度
"""
import os
import json
from pathlib import Path
from datetime import datetime

BASE_OUTPUT_DIR = "temp/all_versions_test_20260305_010655"


def check_progress():
    """检查测试进度"""
    base_path = Path(BASE_OUTPUT_DIR)

    if not base_path.exists():
        print(f"❌ 测试目录不存在: {BASE_OUTPUT_DIR}")
        return

    print(f"\n{'='*80}")
    print(f"全版本测试进度监控")
    print(f"{'='*80}")
    print(f"测试目录: {BASE_OUTPUT_DIR}")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    # 检查所有子目录
    versions = []
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            versions.append(item)

    if len(versions) == 0:
        print("⏳ 测试尚未开始")
        return

    # 统计进度
    completed = []
    in_progress = []
    pending = []

    for version_dir in sorted(versions):
        results_file = version_dir / "results.json"

        if results_file.exists():
            # 已完成
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total = len(data.get("results", []))
                success = sum(1 for r in data.get("results", []) if r.get("status") == "success")
                completed.append({
                    "name": version_dir.name,
                    "total": total,
                    "success": success,
                    "rate": success/total*100 if total > 0 else 0
                })
        else:
            # 检查是否有生成的图片
            png_files = list(version_dir.glob("*.png"))
            if len(png_files) > 0:
                in_progress.append({
                    "name": version_dir.name,
                    "generated": len(png_files)
                })
            else:
                pending.append(version_dir.name)

    # 显示进度
    print(f"总版本数: 14")
    print(f"✅ 已完成: {len(completed)}")
    print(f"⏳ 进行中: {len(in_progress)}")
    print(f"⏸️  待开始: {len(pending)}")
    print(f"\n{'='*80}\n")

    if completed:
        print(f"✅ 已完成的版本 ({len(completed)}):")
        print(f"{'版本':<30} {'成功/总数':<12} {'成功率'}")
        print(f"{'-'*60}")
        for v in completed:
            print(f"{v['name']:<30} {v['success']}/{v['total']:<10} {v['rate']:>6.1f}%")
        print()

    if in_progress:
        print(f"⏳ 正在测试的版本 ({len(in_progress)}):")
        for v in in_progress:
            print(f"  - {v['name']} (已生成 {v['generated']} 张图片)")
        print()

    if pending:
        print(f"⏸️  待开始的版本 ({len(pending)}):")
        for v in pending:
            print(f"  - {v}")
        print()

    print(f"{'='*80}\n")


if __name__ == "__main__":
    check_progress()
