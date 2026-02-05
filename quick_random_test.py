#!/usr/bin/env python3
"""
快速随机测试 - 10张图片并发测试
"""
import subprocess
import os
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime

# 配置
PROMPT_FILE = "prompts/versions/v2.1_ecommerce_universal.txt"
MODEL = "nano-banana-2-2k-vip"
STRENGTH = 1.0
STEPS = 40
TIMEOUT = 300
MAX_WORKERS = 1  # 串行测试，避免API冲突
SAMPLE_SIZE = 10


def collect_all_images():
    """收集所有珠宝图片"""
    all_images = []
    jewelry_dirs = ["数据/项链", "数据/耳环", "数据/手链", "数据/手环"]

    for jewelry_dir in jewelry_dirs:
        if not os.path.exists(jewelry_dir):
            continue

        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            images = list(Path(jewelry_dir).glob(ext))
            for img in images:
                all_images.append(str(img))

    return all_images


def run_single_test(image, output_dir, index):
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
        # 移动生成的文件到正确位置
        src = os.path.join(output_dir, MODEL, "01.png")
        dst = os.path.join(output_dir, f"{index:02d}.png")

        if os.path.exists(src):
            import shutil
            os.makedirs(output_dir, exist_ok=True)
            shutil.move(src, dst)
            # 清理临时目录
            shutil.rmtree(os.path.join(output_dir, MODEL))
            return True, None, image
        else:
            return False, "输出文件未生成", image
    except subprocess.CalledProcessError as e:
        return False, str(e), image


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"outputs/quick_random_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # 收集并随机抽样
    all_images = collect_all_images()

    if len(all_images) < SAMPLE_SIZE:
        print(f"图片不足 {SAMPLE_SIZE} 张，只测试 {len(all_images)} 张")
        sample_images = all_images
    else:
        sample_images = random.sample(all_images, SAMPLE_SIZE)

    print(f"\n{'='*60}")
    print(f"快速随机测试 - v2.1 通用提示词（简化版）")
    print(f"{'='*60}")
    print(f"配置:")
    print(f"  提示词: {PROMPT_FILE}")
    print(f"  Strength: {STRENGTH}")
    print(f"  并发数: {MAX_WORKERS}")
    print(f"  样本数: {len(sample_images)}")
    print(f"  输出目录: {output_dir}")
    print(f"{'='*60}\n")

    # 显示测试列表
    for i, img in enumerate(sample_images, 1):
        img_name = Path(img).name
        img_dir = Path(img).parent.name
        print(f"  [{i}] {img_dir:8} - {img_name}")

    print(f"\n开始并发测试...\n")

    # 并发执行测试
    results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_index = {
            executor.submit(run_single_test, img, output_dir, i): (img, i)
            for i, img in enumerate(sample_images, 1)
        }

        # 处理完成的任务
        for future in future_to_index:
            img, idx = future_to_index[future]
            completed += 1

            try:
                success, error, image = future.result()
                img_name = Path(img).name
                results.append({
                    "image": img,
                    "image_name": img_name,
                    "status": "success" if success else "failed",
                    "error": error,
                    "output": os.path.join(output_dir, f"{idx:02d}.png")
                })

                status_icon = "✓" if success else "✗"
                print(f"[{completed}/{len(sample_images)}] {img_name:20} {status_icon}")

            except Exception as e:
                img_name = Path(img).name
                results.append({
                    "image": img,
                    "image_name": img_name,
                    "status": "error",
                    "error": str(e)
                })
                print(f"[{completed}/{len(sample_images)}] {img_name:20} ✗ 异常")

    # 统计结果
    success_count = sum(1 for r in results if r["status"] == "success")

    print(f"\n{'='*60}")
    print(f"测试完成！")
    print(f"{'='*60}")
    print(f"总计: {success_count}/{len(results)} 成功 ({success_count/len(results)*100:.1f}%)")
    print(f"结果目录: {output_dir}")
    print(f"{'='*60}\n")

    # 显示查看命令
    print(f"查看所有结果:")
    print(f"  open \"{output_dir}\"\n")

    for r in results:
        if r["status"] == "success":
            print(f'open "{r["output"]}"  # {r["image_name"]}')

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
    