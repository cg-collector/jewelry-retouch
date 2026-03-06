#!/usr/bin/env python3
"""
快速随机测试 - 10张图片并发测试（品类自动识别）
"""
import subprocess
import os
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime

# 配置
MODEL = "nano-banana-2"
STRENGTH = 1.0
STEPS = 40
TIMEOUT = 300
MAX_WORKERS = 1  # 串行测试，避免API冲突
SAMPLE_SIZE = 10

# 品类到提示词的映射配置（使用v4.x生产版本）
JEWELRY_PROMPT_MAP = {
    "项链": "prompts/versions/v4.1_necklace_full_loop.txt",
    "耳环": "prompts/versions/v4.5_earring_frontal_pair.txt",
    "手链": "prompts/versions/v3.3_bracelet_topdown.txt",
    "手环": "prompts/versions/v4.6_bangle_flat_topdown.txt",
    "戒指": "prompts/versions/v4.2_ring_flat_texture_aware.txt",
}


def get_prompt_for_jewelry_type(jewelry_type):
    """根据珠宝类型获取对应的提示词文件"""
    return JEWELRY_PROMPT_MAP.get(jewelry_type, "prompts/versions/v2.1_ecommerce_universal.txt")


def collect_all_images():
    """收集所有珠宝图片，返回 (image_path, jewelry_type) 元组列表"""
    all_images = []
    jewelry_dirs = {
        "项链": "数据/项链",
        "耳环": "数据/耳环",
        "手链": "数据/手链",
        "手环": "数据/手环",
        "戒指": "数据/戒指",
    }

    for jewelry_type, jewelry_dir in jewelry_dirs.items():
        if not os.path.exists(jewelry_dir):
            continue

        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            images = list(Path(jewelry_dir).glob(ext))
            for img in images:
                all_images.append((str(img), jewelry_type))

    return all_images


def run_single_test(image, jewelry_type, prompt_file, output_dir, index):
    """运行单个测试"""
    cmd = [
        "python", "tools/quick_prompt_test.py",
        "--image", image,
        "--prompt_file", prompt_file,
        "--single",
        "--model", MODEL,
        "--outdir", output_dir,
        "--steps", str(STEPS),
        "--timeout", str(TIMEOUT),
        "--control_strength", str(STRENGTH)
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        # 移动生成的文件到正确位置（模型名中的.会被替换成_）
        model_dir_name = MODEL.replace(".", "_")
        src = os.path.join(output_dir, model_dir_name, "01.png")
        dst = os.path.join(output_dir, f"{index:02d}.png")

        if os.path.exists(src):
            import shutil
            os.makedirs(output_dir, exist_ok=True)
            shutil.move(src, dst)
            # 清理临时目录
            shutil.rmtree(os.path.join(output_dir, model_dir_name))
            return True, None, image, jewelry_type, prompt_file
        else:
            return False, "输出文件未生成", image, jewelry_type, prompt_file
    except subprocess.CalledProcessError as e:
        return False, str(e), image, jewelry_type, prompt_file


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"temp/quick_random_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # 收集并随机抽样
    all_images = collect_all_images()

    if len(all_images) < SAMPLE_SIZE:
        print(f"图片不足 {SAMPLE_SIZE} 张，只测试 {len(all_images)} 张")
        sample_images = all_images
    else:
        sample_images = random.sample(all_images, SAMPLE_SIZE)

    print(f"\n{'='*60}")
    print(f"快速随机测试 - 品类自适应提示词")
    print(f"{'='*60}")
    print(f"配置:")
    print(f"  模型: {MODEL}")
    print(f"  Strength: {STRENGTH}")
    print(f"  并发数: {MAX_WORKERS}")
    print(f"  样本数: {len(sample_images)}")
    print(f"  输出目录: {output_dir}")
    print(f"\n品类-提示词映射:")
    for jewelry_type, prompt_file in JEWELRY_PROMPT_MAP.items():
        print(f"  {jewelry_type:6} -> {Path(prompt_file).name}")
    print(f"{'='*60}\n")

    # 显示测试列表
    for i, (img, jewelry_type) in enumerate(sample_images, 1):
        img_name = Path(img).name
        prompt_file = get_prompt_for_jewelry_type(jewelry_type)
        print(f"  [{i}] {jewelry_type:6} - {img_name}")
        print(f"      -> {Path(prompt_file).name}")

    print(f"\n开始并发测试...\n")

    # 并发执行测试
    results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_index = {
            executor.submit(run_single_test, img, jewelry_type, get_prompt_for_jewelry_type(jewelry_type), output_dir, i): (img, jewelry_type, i)
            for i, (img, jewelry_type) in enumerate(sample_images, 1)
        }

        # 处理完成的任务
        for future in future_to_index:
            img, jewelry_type, idx = future_to_index[future]
            completed += 1

            try:
                success, error, image, j_type, prompt_file = future.result()
                img_name = Path(img).name
                results.append({
                    "image": img,
                    "image_name": img_name,
                    "jewelry_type": jewelry_type,
                    "prompt_file": prompt_file,
                    "status": "success" if success else "failed",
                    "error": error,
                    "output": os.path.join(output_dir, f"{idx:02d}.png")
                })

                status_icon = "✓" if success else "✗"
                print(f"[{completed}/{len(sample_images)}] {jewelry_type:6} {img_name:20} {status_icon}")

            except Exception as e:
                img_name = Path(img).name
                results.append({
                    "image": img,
                    "image_name": img_name,
                    "jewelry_type": jewelry_type,
                    "status": "error",
                    "error": str(e)
                })
                print(f"[{completed}/{len(sample_images)}] {jewelry_type:6} {img_name:20} ✗ 异常")

    # 统计结果
    success_count = sum(1 for r in results if r["status"] == "success")

    print(f"\n{'='*60}")
    print(f"测试完成！")
    print(f"{'='*60}")
    print(f"总计: {success_count}/{len(results)} 成功 ({success_count/len(results)*100:.1f}%)")
    print(f"结果目录: {output_dir}")

    # 按品类统计
    print(f"\n品类统计:")
    type_stats = {}
    for r in results:
        j_type = r.get("jewelry_type", "未知")
        if j_type not in type_stats:
            type_stats[j_type] = {"total": 0, "success": 0}
        type_stats[j_type]["total"] += 1
        if r["status"] == "success":
            type_stats[j_type]["success"] += 1

    for j_type, stats in type_stats.items():
        rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {j_type:6}: {stats['success']}/{stats['total']} ({rate:.1f}%)")

    print(f"{'='*60}\n")

    # 显示查看命令
    print(f"查看所有结果:")
    print(f"  open \"{output_dir}\"\n")

    for r in results:
        if r["status"] == "success":
            print(f'open "{r["output"]}"  # {r["jewelry_type"]} - {r["image_name"]}')

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
    