#!/usr/bin/env python3
"""
快速验证工具 - 15分钟完成上线决策
随机抽样 + 快速评估
"""
import subprocess
import os
import random
import sys
from pathlib import Path
import json

# 配置
PROMPT_FILE = "prompts/current.txt"
MODEL = "nano-banana-2-2k-vip"
STRENGTH = 0.6  # 建议的默认值
STEPS = 40
TIMEOUT = 300


def scan_all_images():
    """扫描所有珠宝图片"""
    jewelry_dirs = {
        "necklace": "数据/项链",
        "earring": "数据/耳环",
        "bracelet": "数据/手链",
        "bangle": "数据/手环",
    }

    type_names = {
        "necklace": "项链",
        "earring": "耳环",
        "bracelet": "手链",
        "bangle": "手环",
    }

    all_images = []

    for jewelry_type, dir_path in jewelry_dirs.items():
        if not os.path.exists(dir_path):
            continue

        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            images.extend(Path(dir_path).glob(ext))

        images = sorted([str(img) for img in images])

        for img in images:
            all_images.append({
                "type": jewelry_type,
                "type_name": type_names[jewelry_type],
                "path": img
            })

    return all_images


def sample_images(all_images, n=5):
    """随机抽取n张图片"""
    if len(all_images) <= n:
        return all_images

    # 分层抽样：每种类型至少1张
    types = list(set(img["type"] for img in all_images))
    sampled = []

    # 每种类型抽1张
    for jewelry_type in types:
        type_images = [img for img in all_images if img["type"] == jewelry_type]
        if type_images:
            sampled.append(random.choice(type_images))

    # 剩余随机抽取
    remaining = [img for img in all_images if img not in sampled]
    while len(sampled) < n and remaining:
        img = random.choice(remaining)
        sampled.append(img)
        remaining.remove(img)

    return sampled


def run_test(image, output_dir):
    """运行单个测试"""
    cmd = [
        "python", "tools/quick_prompt_test.py",
        "--image", image,
        "--prompt_file", PROMPT_FILE,
        "--single",
        "--model", MODEL,
        "--outdir", output_dir,
        "--steps", str(STEPS),
        "--timeout", str(TIMEOUT),
        "--control_strength", str(STRENGTH)
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, None
    except subprocess.CalledProcessError as e:
        return False, str(e)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="快速验证工具")
    parser.add_argument("--sample", type=int, default=5,
                       help="抽样数量（默认5张）")
    parser.add_argument("--strength", type=float, default=0.6,
                       help="Control strength（默认0.6）")

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"快速验证工具 - 15分钟上线决策")
    print(f"{'='*70}")
    print(f"配置:")
    print(f"  抽样数量: {args.sample}张")
    print(f"  Control Strength: {args.strength}")
    print(f"  模型: {MODEL}")
    print(f"{'='*70}\n")

    # 扫描所有图片
    print("1. 扫描图片...")
    all_images = scan_all_images()
    print(f"   共找到 {len(all_images)} 张图片")

    # 抽样
    print(f"\n2. 随机抽样 {args.sample} 张...")
    sampled = sample_images(all_images, args.sample)
    for i, img in enumerate(sampled, 1):
        print(f"   {i}. {img['type_name']:8} - {Path(img['path']).name}")

    # 确认
    print(f"\n{'='*70}")
    response = input("是否开始测试? (y/n): ")
    if response.lower() != 'y':
        print("已取消")
        return 0

    # 运行测试
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = f"outputs/quick_check_{timestamp}"

    print(f"\n3. 开始测试...")
    print(f"   预计耗时: ~{args.sample * 0.5:.0f}分钟\n")

    results = []

    for i, img in enumerate(sampled, 1):
        img_name = Path(img['path']).name
        output_dir = os.path.join(output_base, f"{i:02d}_{img['type']}")

        print(f"  [{i}/{args.sample}] {img['type_name']} - {img_name}")

        success, error = run_test(img['path'], output_dir)

        results.append({
            "index": i,
            "type": img["type_name"],
            "image": img_name,
            "status": "success" if success else "failed",
            "error": error,
            "output": os.path.join(output_dir, MODEL, "01.png")
        })

        if success:
            print(f"          ✓")
        else:
            print(f"          ✗ {error}")

    # 保存结果
    result_file = os.path.join(output_base, "results.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 统计
    success_count = sum(1 for r in results if r["status"] == "success")

    print(f"\n{'='*70}")
    print(f"测试完成！")
    print(f"{'='*70}")
    print(f"成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    print(f"结果目录: {output_base}")

    # 快速查看指南
    print(f"\n{'='*70}")
    print(f"下一步：人工检查")
    print(f"{'='*70}")
    print(f"\n打开所有结果图片:")
    for r in results:
        if r["status"] == "success":
            print(f'  open "{r["output"]}"  # {r["type"]} - {r["image"]}')

    print(f"\n检查清单:")
    print(f"  □ 有无严重裁切？（珠宝主体被切掉）")
    print(f"  □ 珠保样式是否保持？（颜色、形状、细节）")
    print(f"  □ 清晰度如何？（主要细节可见）")
    print(f"  □ 背景是否纯白？")

    print(f"\n决策标准:")
    print(f"  ✓ 全部通过 → 可以准备上线")
    print(f"  ⚠️  1-2张有问题 → 修复或调整strength后再验证")
    print(f"  ✗ 3张以上有问题 → 需要重新设计提示词")

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    import datetime
    sys.exit(main())
