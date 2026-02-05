#!/usr/bin/env python3
"""
快速最终测试 - 每个类别5张图片
并行调用API加速测试
"""
import subprocess
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import json

# 配置
JEWELRY_TYPES = {
    "necklace": {"name": "项链", "dir": "数据/项链", "sample": 5},
    "earring": {"name": "耳环", "dir": "数据/耳环", "sample": 5},
    "bracelet": {"name": "手链", "dir": "数据/手链", "sample": 5},
    "bangle": {"name": "手环", "dir": "数据/手环", "sample": 5},
}

PROMPT_FILE = "prompts/versions/v2.1_ecommerce_universal.txt"
MODEL = "nano-banana-2-2k-vip"
STRENGTH = 1.0
STEPS = 40
TIMEOUT = 300
MAX_WORKERS = 1  # 串行执行，避免并发冲突


def scan_images(jewelry_dir, sample_size):
    """扫描并抽样图片"""
    if not os.path.exists(jewelry_dir):
        return []

    images = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
        images.extend(Path(jewelry_dir).glob(ext))

    images = sorted([str(img) for img in images])

    # 返回前sample_size张
    return images[:sample_size]


def run_single_test(image, output_dir, index):
    """运行单个测试"""
    # 先使用quick_prompt_test生成，然后移动文件
    temp_dir = output_dir + "_temp"

    cmd = [
        "python", "tools/quick_prompt_test.py",
        "--image", image,
        "--prompt_file", PROMPT_FILE,
        "--single",
        "--model", MODEL,
        "--outdir", temp_dir,
        "--steps", str(STEPS),
        "--timeout", str(TIMEOUT),
        "--control_strength", str(STRENGTH)
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        # 移动生成的文件到正确位置
        src = os.path.join(temp_dir, MODEL, "01.png")
        dst = os.path.join(output_dir, f"{index:02d}.png")

        if os.path.exists(src):
            import shutil
            os.makedirs(output_dir, exist_ok=True)
            shutil.move(src, dst)
            # 清理临时目录
            shutil.rmtree(temp_dir)
            return True, None, image
        else:
            return False, "输出文件未生成", image
    except subprocess.CalledProcessError as e:
        return False, str(e), image


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = f"outputs/quick_final_test_{timestamp}"

    print(f"\n{'='*70}")
    print(f"快速最终测试 - v2.1 通用提示词")
    print(f"{'='*70}")
    print(f"配置:")
    print(f"  提示词: {PROMPT_FILE}")
    print(f"  Strength: {STRENGTH}")
    print(f"  并发数: {MAX_WORKERS}")
    print(f"  输出目录: {output_base}")
    print(f"{'='*70}\n")

    # 收集所有测试任务
    all_tasks = []
    total_tests = 0

    for jewelry_type, config in JEWELRY_TYPES.items():
        images = scan_images(config["dir"], config["sample"])

        if not images:
            print(f"⚠️  {config['name']}: 未找到图片")
            continue

        # 为每个类别创建一个文件夹
        type_output_dir = os.path.join(output_base, jewelry_type)
        os.makedirs(type_output_dir, exist_ok=True)

        for idx, img in enumerate(images, 1):
            img_name = Path(img).name
            all_tasks.append({
                "type": config["name"],
                "jewelry_type": jewelry_type,
                "image": img,
                "image_name": img_name,
                "output_dir": type_output_dir,
                "index": idx
            })

        total_tests += len(images)
        print(f"✓ {config['name']:8} - {len(images)} 张图片 → {jewelry_type}/")

    print(f"\n总测试数: {total_tests}")
    print(f"预计耗时: ~{total_tests * 25 / MAX_WORKERS / 60:.1f} 分钟")
    print(f"{'='*70}\n")

    if not all_tasks:
        print("没有找到任何测试图片")
        return 1

    # 并行执行测试
    results = []
    completed = 0

    print("开始并行测试...\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(run_single_test, task["image"], task["output_dir"], task["index"]): task
            for task in all_tasks
        }

        # 处理完成的任务
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            completed += 1

            try:
                success, error, image = future.result()
                results.append({
                    "type": task["type"],
                    "jewelry_type": task["jewelry_type"],
                    "image": task["image"],  # 保存完整路径
                    "image_name": task["image_name"],
                    "status": "success" if success else "failed",
                    "error": error,
                    "output": os.path.join(task["output_dir"], f"{task['index']:02d}.png")
                })

                status_icon = "✓" if success else "✗"
                print(f"[{completed}/{total_tests}] {task['type']:8} - {task['image_name']:20} {status_icon}")

            except Exception as e:
                results.append({
                    "type": task["type"],
                    "jewelry_type": task["jewelry_type"],
                    "image": task["image"],  # 保存完整路径
                    "image_name": task["image_name"],
                    "status": "error",
                    "error": str(e)
                })
                print(f"[{completed}/{total_tests}] {task['type']:8} - {task['image_name']:20} ✗ 异常")

    # 保存结果
    result_file = os.path.join(output_base, "results.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 统计结果
    success_count = sum(1 for r in results if r["status"] == "success")

    print(f"\n{'='*70}")
    print(f"测试完成！")
    print(f"{'='*70}")

    for jewelry_type in JEWELRY_TYPES.keys():
        type_name = JEWELRY_TYPES[jewelry_type]["name"]
        type_results = [r for r in results if r["jewelry_type"] == jewelry_type]
        type_success = sum(1 for r in type_results if r["status"] == "success")

        print(f"\n{type_name}:")
        print(f"  成功: {type_success}/{len(type_results)}")

    print(f"\n{'='*70}")
    print(f"总计: {success_count}/{len(results)} 成功 ({success_count/len(results)*100:.1f}%)")
    print(f"结果目录: {output_base}")
    print(f"结果文件: {result_file}")
    print(f"{'='*70}")

    # 生成查看命令
    print(f"\n快速查看命令:")
    print(f"\n# 按类别查看所有结果:")
    for jewelry_type in JEWELRY_TYPES.keys():
        type_name = JEWELRY_TYPES[jewelry_type]["name"]
        type_dir = os.path.join(output_base, jewelry_type)
        print(f"\n# {type_name}:")
        print(f"open \"{type_dir}\"")

    print(f"\n\n# 单独查看某张图片:")
    for r in results:
        if r["status"] == "success":
            print(f'open "{r["output"]}"  # {r["type"]} - {r["image"]}')

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
