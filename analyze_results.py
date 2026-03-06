#!/usr/bin/env python3
"""
分析戒指测试结果JSON文件
"""
import json
import sys
import glob
from pathlib import Path

def analyze_results(json_file):
    """分析测试结果JSON"""
    with open(json_file) as f:
        data = json.load(f)

    print(f"\n{'='*70}")
    print(f"戒指测试结果分析")
    print(f"{'='*70}")
    print(f"测试时间: {data.get('test_time', 'N/A')}")
    print(f"测试图片: {data['total_images']} 张")
    print(f"测试版本: {data['total_versions']} 个")
    print(f"总测试数: {data['total_tests']}")
    print(f"模型: {data['model']}")
    print(f"{'='*70}\n")

    # 按版本统计
    for version in ["v4.2", "v4.3", "v4.4"]:
        results = [r for r in data["results"] if r["version"] == version]
        if not results:
            continue

        success = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - success

        print(f"{version} - {results[0]['version_name']}")
        print(f"  角度: {results[0]['angle']}")
        print(f"  词数: {results[0]['words']}")
        print(f"  成功: {success}/{len(results)}")
        print(f"  失败: {failed}/{len(results)}")

        if failed > 0:
            failed_results = [r for r in results if r["status"] == "failed"]
            print(f"  失败详情:")
            for r in failed_results:
                print(f"    - {r['image']}: {r['error']}")
        print()

    # 列出所有成功的测试
    print(f"{'='*70}")
    print(f"成功测试列表（可快速查看图片）")
    print(f"{'='*70}")
    print(f"{'版本':5} | {'图片文件':<15} | {'输出路径'}")
    print(f"{'-'*5}-+-{'-'*15}-+-{'-'*40}")

    for r in data["results"]:
        if r["status"] == "success":
            output_short = r['output'].replace('/Users/edy/Desktop/i2i/', '')[:40]
            print(f"{r['version']:5} | {r['image']:<15} | {output_short}")

    print(f"\n汇总文件: {json_file}")
    print(f"{'='*70}\n")

    # 显示查看命令
    print("快速查看命令:")
    print(f"  # 查看所有图片")
    first_result = next((r for r in data["results"] if r["status"] == "success"), None)
    if first_result:
        output_dir = str(Path(first_result["output"]).parent)
        print(f"  open {output_dir}")

    print(f"\n  # 查看JSON")
    print(f"  cat {json_file} | python3 -m json.tool")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_results(sys.argv[1])
    else:
        # 查找最新的汇总文件
        files = glob.glob("check/ring_all_versions_*.json")
        if files:
            latest = max(files)
            print(f"使用最新文件: {latest}\n")
            analyze_results(latest)
        else:
            print("错误: 找不到汇总文件")
            print("请检查测试是否完成，或手动指定文件路径")
