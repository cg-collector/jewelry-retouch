#!/usr/bin/env python3
"""
验证两次测试结果的稳定性
对比两次运行的相似度
"""
import subprocess
import sys
from pathlib import Path

# 两次测试的目录
TEST1 = "outputs/test_control_strength_20260203_163926"
TEST2 = "outputs/test_control_strength_20260204_103810"
MODEL = "nano-banana-2-2k-vip"

TYPES = ["necklace", "earring", "bangle"]
STRENGTHS = [1.0, 0.8, 0.6, 0.4]


def open_pair(type_name, strength):
    """打开同一个配置的两次测试结果，左右对比"""
    strength_dir = str(strength).replace('.', '_')

    img1 = Path(TEST1) / f"{type_name}_strength_{strength_dir}" / MODEL / "01.png"
    img2 = Path(TEST2) / f"{type_name}_strength_{strength_dir}" / MODEL / "01.png"

    if not img1.exists():
        print(f"  ⚠️  第一次测试图片不存在: {img1.name}")
        return False

    if not img2.exists():
        print(f"  ⚠️  第二次测试图片不存在: {img2.name}")
        return False

    # 同时打开两张图进行对比
    subprocess.run(["open", str(img1)])
    subprocess.run(["open", str(img2)])

    print(f"  ✓ 已打开: {img1.parent.name}")
    print(f"           {img2.parent.name}")
    return True


def verify_all():
    """验证所有配置的稳定性"""
    print("\n" + "=" * 60)
    print("稳定性验证 - 对比两次测试结果")
    print("=" * 60)
    print(f"第一次测试: {TEST1}")
    print(f"第二次测试: {TEST2}")
    print("=" * 60)

    for type_name in TYPES:
        cn_name = {"necklace": "项链", "earring": "耳环", "bangle": "手环"}.get(type_name, type_name)
        print(f"\n>>> {cn_name} ({type_name}):")

        for strength in STRENGTHS:
            print(f"\n  strength={strength}:", end=" ")
            open_pair(type_name, strength)


def verify_single(type_name, strength=None):
    """验证单个类型或单个 strength"""
    cn_name = {"necklace": "项链", "earring": "耳环", "bangle": "手环"}.get(type_name, type_name)

    print(f"\n>>> {cn_name} ({type_name}):")

    if strength:
        print(f"  strength={strength}:", end=" ")
        open_pair(type_name, strength)
    else:
        for s in STRENGTHS:
            print(f"\n  strength={s}:", end=" ")
            open_pair(type_name, s)


def print_comparison_commands():
    """打印手动对比命令"""
    print("\n" + "=" * 60)
    print("手动对比命令")
    print("=" * 60)

    for type_name in TYPES:
        cn_name = {"necklace": "项链", "earring": "耳环", "bangle": "手环"}.get(type_name, type_name)
        print(f"\n# {cn_name}:")

        for strength in STRENGTHS:
            strength_dir = str(strength).replace('.', '_')
            img1 = Path(TEST1) / f"{type_name}_strength_{strength_dir}" / MODEL / "01.png"
            img2 = Path(TEST2) / f"{type_name}_strength_{strength_dir}" / MODEL / "01.png"

            print(f"# strength={strength}")
            print(f'open "{img1}"  # 第一次测试')
            print(f'open "{img2}"  # 第二次测试')
            print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="验证测试结果稳定性")
    parser.add_argument("--type", choices=TYPES + ["all"],
                       default="all", help="珠宝类型")
    parser.add_argument("--strength", type=float,
                       choices=STRENGTHS, help="指定 strength 值")

    args = parser.parse_args()

    if not Path(TEST1).exists():
        print(f"错误: 第一次测试目录不存在: {TEST1}")
        return 1

    if not Path(TEST2).exists():
        print(f"错误: 第二次测试目录不存在: {TEST2}")
        return 1

    if args.type == "all":
        verify_all()
    else:
        verify_single(args.type, args.strength)

    print_comparison_commands()

    return 0


if __name__ == "__main__":
    sys.exit(main())
