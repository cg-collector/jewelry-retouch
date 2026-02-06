#!/usr/bin/env python3
"""
全量数据 Control Strength 测试
测试所有珠宝目录下的所有图片
"""
import subprocess
import os
import datetime
from pathlib import Path
import json

# 自动扫描所有珠宝目录（测试项链）
JEWELRY_DIRS = {
    "necklace": "数据/项链",
}

TYPE_NAMES = {
    "necklace": "项链",
    "earring": "耳环",
    "bracelet": "手链",
    "bangle": "手环",
}

# 测试配置
CONTROL_STRENGTHS = [1.0]
PROMPT_FILE = "prompts/versions/v3.0_necklace_threequarter.txt"
MODEL = "nano-banana-2-2k-vip"
STEPS = 40
TIMEOUT = 300


def scan_images():
    """扫描所有珠宝目录下的图片"""
    test_cases = []

    for jewelry_type, dir_path in JEWELRY_DIRS.items():
        if not os.path.exists(dir_path):
            print(f"⚠️  目录不存在: {dir_path}")
            continue

        # 找到所有图片文件
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            images.extend(Path(dir_path).glob(ext))

        # 排序并转换为字符串
        images = sorted([str(img) for img in images])

        if images:
            test_cases.append({
                "type": jewelry_type,
                "type_name": TYPE_NAMES[jewelry_type],
                "dir": dir_path,
                "images": images
            })
            print(f"✓ {TYPE_NAMES[jewelry_type]}: 找到 {len(images)} 张图片")
        else:
            print(f"⚠️  {TYPE_NAMES[jewelry_type]}: 没有找到图片")

    return test_cases


def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def run_single_test(image, control_strength, output_path):
    """运行单个测试"""
    # 使用临时目录
    temp_dir = output_path + "_temp"

    cmd = [
        "python", "tools/quick_prompt_test.py",
        "--image", image,
        "--prompt_file", PROMPT_FILE,
        "--single",
        "--model", MODEL,
        "--outdir", temp_dir,
        "--steps", str(STEPS),
        "--timeout", str(TIMEOUT),
        "--control_strength", str(control_strength)
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        # 移动生成的文件到正确位置
        src = os.path.join(temp_dir, MODEL, "01.png")

        if os.path.exists(src):
            import shutil
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.move(src, output_path)
            # 清理临时目录
            shutil.rmtree(temp_dir)
            return True, None
        else:
            return False, "输出文件未生成"
    except subprocess.CalledProcessError as e:
        return False, str(e)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='全量珠宝数据测试')
    parser.add_argument('--workers', type=int, default=1, help='并发线程数 (默认: 1)')
    parser.add_argument('--yes', action='store_true', help='跳过确认直接开始测试')
    args = parser.parse_args()

    MAX_WORKERS = args.workers

    timestamp = get_timestamp()
    base_output = f"outputs/test_all_jewelry_{timestamp}"

    print(f"\n{'='*70}")
    print(f"全量珠宝数据测试")
    print(f"{'='*70}")
    print(f"测试值: {CONTROL_STRENGTHS}")
    print(f"提示词: {PROMPT_FILE}")
    print(f"模型: {MODEL}")
    print(f"并发数: {MAX_WORKERS}")
    print(f"输出目录: {base_output}")
    print(f"{'='*70}\n")

    # 扫描图片
    print("扫描图片文件...")
    test_cases = scan_images()

    if not test_cases:
        print("错误: 没有找到任何图片")
        return 1

    # 统计总测试数
    total_tests = sum(len(tc["images"]) * len(CONTROL_STRENGTHS) for tc in test_cases)
    print(f"\n总测试数: {total_tests} 次")
    print(f"预计耗时: ~{total_tests * 25 // 60} 分钟")

    # 确认
    print(f"\n{'='*70}")
    if not args.yes:
        response = input("是否开始测试? (y/n): ")
        if response.lower() != 'y':
            print("已取消")
            return 0

    print(f"\n开始测试...")
    print(f"{'='*70}\n")

    results = []
    completed = 0

    for test_case in test_cases:
        type_name = test_case["type_name"]
        jewelry_type = test_case["type"]
        images = test_case["images"]

        # 为每个类型创建一个目录
        type_output_dir = os.path.join(base_output, jewelry_type)
        os.makedirs(type_output_dir, exist_ok=True)

        print(f"\n{'='*70}")
        print(f">>> 测试类型: {type_name} ({len(images)} 张图片)")
        print(f"{'='*70}")

        for img_idx, image in enumerate(images, 1):
            image_name = Path(image).name
            print(f"\n  [{img_idx}/{len(images)}] {image_name}")

            for strength in CONTROL_STRENGTHS:
                # 生成文件名：img{idx}_strength{x.x}.png
                strength_str = str(strength).replace('.', '_')
                output_filename = f"img{img_idx:02d}_strength_{strength_str}.png"
                output_path = os.path.join(type_output_dir, output_filename)

                print(f"    strength={strength} ... ", end="", flush=True)

                success, error = run_single_test(image, strength, output_path)

                results.append({
                    "type": type_name,
                    "jewelry_type": jewelry_type,
                    "image": image_name,
                    "image_index": img_idx,
                    "strength": strength,
                    "status": "success" if success else "failed",
                    "error": error,
                    "output": output_path
                })

                completed += 1

                if success:
                    print(f"✓ ({completed}/{total_tests})")
                else:
                    print(f"✗ ({completed}/{total_tests})")

    # 保存结果到JSON
    result_file = os.path.join(base_output, "test_results.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印统计摘要
    print(f"\n{'='*70}")
    print(f"测试完成！结果摘要")
    print(f"{'='*70}")

    for test_case in test_cases:
        type_name = test_case["type_name"]
        type_results = [r for r in results if r["type"] == type_name]
        success_count = sum(1 for r in type_results if r["status"] == "success")

        print(f"\n{type_name}:")
        print(f"  成功: {success_count}/{len(type_results)}")

        # 按strength统计成功率
        for strength in CONTROL_STRENGTHS:
            strength_results = [r for r in type_results if r["strength"] == strength]
            strength_success = sum(1 for r in strength_results if r["status"] == "success")
            print(f"    strength={strength}: {strength_success}/{len(strength_results)}")

    # 总体统计
    overall_success = sum(1 for r in results if r["status"] == "success")
    print(f"\n{'='*70}")
    print(f"总计: {overall_success}/{len(results)} 成功 ({overall_success/len(results)*100:.1f}%)")
    print(f"结果目录: {base_output}")
    print(f"结果文件: {result_file}")
    print(f"{'='*70}")

    # 生成查看指南
    guide_file = os.path.join(base_output, "view_guide.txt")
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write("查看结果指南\n")
        f.write("=" * 60 + "\n\n")

        for test_case in test_cases:
            type_name = test_case["type_name"]
            jewelry_type = test_case["type"]
            type_dir = os.path.join(base_output, jewelry_type)
            f.write(f"\n# {type_name}\n")
            f.write(f"cd \"{type_dir}\"\n\n")

            for img_idx, image in enumerate(test_case["images"], 1):
                image_name = Path(image).name
                f.write(f"## 图片 {img_idx}: {image_name}\n")

                for strength in CONTROL_STRENGTHS:
                    strength_str = str(strength).replace('.', '_')
                    output_filename = f"img{img_idx:02d}_strength_{strength_str}.png"
                    f.write(f'open "{output_filename}"  # strength={strength}\n')

                f.write("\n")

    print(f"查看指南: {guide_file}")
    print(f"运行以下命令查看: cat {guide_file}")

    return 0 if overall_success == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
