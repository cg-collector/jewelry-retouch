#!/usr/bin/env python3
"""
基础提示词批量测试脚本
测试所有珠宝类型 + 基础提示词
"""
import subprocess
import os
from pathlib import Path

# 测试配置
JEWELRY_TYPES = [
    {
        "name": "ring",
        "image": "数据/Jewelry理想效果图/大图/Ring-angled.png",
        "label": "戒指"
    },
    {
        "name": "necklace",
        "image": "数据/Jewelry理想效果图/大图/Necklace-angled.png",
        "label": "项链"
    },
    {
        "name": "earring",
        "image": "数据/Jewelry理想效果图/大图/Earrings-angled.png",
        "label": "耳环"
    },
    {
        "name": "bracelet",
        "image": "数据/Jewelry理想效果图/大图/Bracele-angled.png",
        "label": "手链"
    },
]

PROMPT_FILE = "prompts/base_prompt.txt"
MODEL = "nano-banana-2-2k-vip"
STEPS = 40
OUTPUT_BASE = "outputs/base_prompt_test_all"

def run_test(jewelry_type):
    """运行单个珠宝类型的测试"""
    output_dir = os.path.join(OUTPUT_BASE, jewelry_type["name"])

    cmd = [
        "python", "tools/quick_prompt_test.py",
        "--image", jewelry_type["image"],
        "--prompt_file", PROMPT_FILE,
        "--single",
        "--model", MODEL,
        "--outdir", output_dir,
        "--steps", str(STEPS)
    ]

    print(f"\n{'='*60}")
    print(f"正在测试: {jewelry_type['label']} ({jewelry_type['name']})")
    print(f"输入图片: {jewelry_type['image']}")
    print(f"{'='*60}")

    try:
        subprocess.run(cmd, check=True)
        print(f"✓ {jewelry_type['label']} 测试完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {jewelry_type['label']} 测试失败: {e}")
        return False

def main():
    print("基础提示词批量测试")
    print(f"提示词文件: {PROMPT_FILE}")
    print(f"模型: {MODEL}")
    print(f"步数: {STEPS}")
    print(f"输出目录: {OUTPUT_BASE}")

    # 创建输出目录
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    # 运行所有测试
    results = {}
    for jewelry_type in JEWELRY_TYPES:
        success = run_test(jewelry_type)
        results[jewelry_type["name"]] = {
            "label": jewelry_type["label"],
            "success": success,
            "output": os.path.join(OUTPUT_BASE, jewelry_type["name"], MODEL, "01.png")
        }

    # 打印结果摘要
    print(f"\n{'='*60}")
    print("测试结果摘要")
    print(f"{'='*60}")
    for name, result in results.items():
        status = "✓ 成功" if result["success"] else "✗ 失败"
        print(f"{result['label']:8} - {status}")
        if result["success"]:
            print(f"          输出: {result['output']}")

    print(f"\n所有测试完成！结果保存在: {OUTPUT_BASE}")

if __name__ == "__main__":
    main()
