#!/usr/bin/env python3
"""
真实珠宝数据测试脚本
使用时间戳目录保存结果
"""
import subprocess
import os
import sys
import datetime
from pathlib import Path

# 测试配置 - 每种类型选择1-2张代表性图片
TEST_CASES = [
    {
        "type": "necklace",
        "type_name": "项链",
        "images": [
            "数据/项链/image_1.jpeg",
            "数据/项链/image_3.jpeg",  # 小图测试
        ]
    },
    {
        "type": "earring",
        "type_name": "耳环",
        "images": [
            "数据/耳环/image_1.jpeg",
            "数据/耳环/image_2.jpeg",
        ]
    },
    {
        "type": "bracelet",
        "type_name": "手链",
        "images": [
            "数据/手链/image_1.jpeg",
            "数据/手链/image_2.jpeg",
        ]
    },
    {
        "type": "bangle",
        "type_name": "手环",
        "images": [
            "数据/手环/image_1.jpeg",
        ]
    },
]

PROMPT_FILE = "prompts/base_prompt.txt"
MODEL = "nano-banana-2-2k-vip"
STEPS = 40
TIMEOUT = 300

def get_timestamp():
    """生成时间戳"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def run_single_test(image_path, output_dir, test_name):
    """运行单个图片测试"""
    cmd = [
        "python", "tools/quick_prompt_test.py",
        "--image", image_path,
        "--prompt_file", PROMPT_FILE,
        "--single",
        "--model", MODEL,
        "--outdir", output_dir,
        "--steps", str(STEPS),
        "--timeout", str(TIMEOUT)
    ]

    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"输入: {image_path}")
    print(f"输出: {output_dir}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return True, None
    except subprocess.CalledProcessError as e:
        return False, str(e)

def main():
    timestamp = get_timestamp()
    base_output_dir = f"outputs/test_results_{timestamp}"

    print(f"\n{'='*60}")
    print(f"真实珠宝数据测试")
    print(f"提示词: {PROMPT_FILE}")
    print(f"模型: {MODEL}")
    print(f"步数: {STEPS}")
    print(f"输出目录: {base_output_dir}")
    print(f"{'='*60}\n")

    results = []

    for test_case in TEST_CASES:
        type_name = test_case["type_name"]
        jewelry_type = test_case["type"]

        print(f"\n>>> 测试类型: {type_name}")

        for idx, image_path in enumerate(test_case["images"], 1):
            if not os.path.exists(image_path):
                print(f"  ⚠️  图片不存在: {image_path}")
                results.append({
                    "type": type_name,
                    "image": image_path,
                    "status": "skipped",
                    "reason": "文件不存在"
                })
                continue

            # 生成子目录名: 类型_序号
            test_name = f"{jewelry_type}_{idx:02d}"
            output_dir = os.path.join(base_output_dir, test_name)

            success, error = run_single_test(image_path, output_dir, test_name)

            results.append({
                "type": type_name,
                "image": image_path,
                "status": "success" if success else "failed",
                "error": error,
                "output": os.path.join(output_dir, MODEL, "01.png")
            })

    # 打印结果摘要
    print(f"\n{'='*60}")
    print(f"测试完成！结果摘要")
    print(f"{'='*60}")

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")

    for r in results:
        status_icon = {
            "success": "✓",
            "failed": "✗",
            "skipped": "⚠️"
        }.get(r["status"], "?")

        print(f"{status_icon} {r['type']:8} - {Path(r['image']).name}")
        if r["status"] == "success":
            print(f"          输出: {r['output']}")
        elif r["status"] == "failed":
            print(f"          错误: {r['error']}")

    print(f"\n总计: {success_count} 成功, {failed_count} 失败, {skipped_count} 跳过")
    print(f"结果保存在: {base_output_dir}")

    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
