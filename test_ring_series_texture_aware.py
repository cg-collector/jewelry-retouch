#!/usr/bin/env python3
"""
测试戒指系列纹理感知版 (v4.2, v4.3, v4.4)
"""
import subprocess
import os
from pathlib import Path
import datetime

# 配置
JEWELRY_DIR = "数据/戒指"
SAMPLE_SIZE = 2  # 测试2张图片

MODELS = {
    "v4.2": {
        "file": "prompts/versions/v4.2_ring_flat_texture_aware.txt",
        "name": "戒指平放俯视",
        "words": 154
    },
    "v4.3": {
        "file": "prompts/versions/v4.3_ring_side_texture_aware.txt",
        "name": "戒指侧向视角",
        "words": 158
    },
    "v4.4": {
        "file": "prompts/versions/v4.4_ring_angled_texture_aware.txt",
        "name": "钻戒倾斜俯视",
        "words": 163
    }
}

MODEL = "gemini-3-pro-image-preview-2k-vip"
STRENGTH = 1.0
STEPS = 40
TIMEOUT = 300

def scan_images(jewelry_dir, sample_size):
    """扫描并抽样图片"""
    if not os.path.exists(jewelry_dir):
        return []

    images = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
        images.extend(Path(jewelry_dir).glob(ext))

    images = sorted([str(img) for img in images])
    return images[:sample_size]

def run_single_test(image, prompt_file, output_dir, version_name, index):
    """运行单个测试"""
    temp_dir = output_dir + "_temp"

    cmd = [
        "python", "tools/quick_prompt_test.py",
        "--image", image,
        "--prompt_file", prompt_file,
        "--single",
        "--model", MODEL,
        "--outdir", temp_dir,
        "--steps", str(STEPS),
        "--timeout", str(TIMEOUT),
        "--control_strength", str(STRENGTH)
    ]

    try:
        print(f"\n{'='*70}")
        print(f"Testing {version_name} - {MODELS[version_name]['name']}")
        print(f"Image: {Path(image).name}")
        print(f"词数: {MODELS[version_name]['words']}")
        print(f"{'='*70}")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # 移动生成的文件到正确位置
        src = os.path.join(temp_dir, MODEL, "01.png")
        dst = os.path.join(output_dir, f"{version_name}_{index:02d}_{Path(image).stem}.png")

        if os.path.exists(src):
            import shutil
            os.makedirs(output_dir, exist_ok=True)
            shutil.move(src, dst)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return True, None, image
        else:
            return False, "输出文件未生成", image

    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        return False, str(e), image

def main():
    """主函数"""
    # 扫描测试图片
    images = scan_images(JEWELRY_DIR, SAMPLE_SIZE)

    if not images:
        print(f"❌ No images found in {JEWELRY_DIR}")
        return

    print(f"\n{'='*70}")
    print(f"戒指系列纹理感知版测试")
    print(f"{'='*70}")
    print(f"测试图片: {len(images)} 张")
    print(f"测试版本: {len(MODELS)} 个")
    for v, info in MODELS.items():
        print(f"  - {v}: {info['name']} ({info['words']}词)")
    print(f"模型: {MODEL}")
    print(f"重点: 纹理保持 + 角度转换")
    print(f"{'='*70}\n")

    # 创建输出目录
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"outputs/ring_series_texture_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # 运行所有测试
    total_tests = len(images) * len(MODELS)
    completed_tests = 0
    success_count = 0
    all_results = {}

    for version_name in MODELS:
        all_results[version_name] = []

        for idx, image in enumerate(images, 1):
            prompt_file = MODELS[version_name]["file"]
            success, error, image_path = run_single_test(
                image, prompt_file, output_dir, version_name, idx
            )

            all_results[version_name].append({
                'image': image_path,
                'success': success,
                'error': error
            })

            completed_tests += 1
            if success:
                success_count += 1
                print(f"✓ Success ({success_count}/{completed_tests}/{total_tests})")
            else:
                print(f"✗ Failed: {error}")

    # 打印总结
    print(f"\n{'='*70}")
    print(f"Test Summary")
    print(f"{'='*70}")
    print(f"成功: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    print(f"输出目录: {output_dir}")
    print(f"{'='*70}\n")

    # 生成VLM评估命令
    print("下一步: VLM评估（聚焦纹理和装饰）")
    for version_name in MODELS:
        print(f"\n{version_name} ({MODELS[version_name]['name']}):")
        for idx, image in enumerate(images, 1):
            output_file = os.path.join(output_dir, f"{version_name}_{idx:02d}_{Path(image).stem}.png")
            print(f"\n图片{idx}:")
            print(f"python tools/vlm_consistency_evaluator_v3.py \\")
            print(f"  --original '{image}' \\")
            print(f"  --generated '{output_file}' \\")
            print(f"  --business '{MODELS[version_name]['name']}，保持纹理和装饰一致' \\")
            print(f"  --output 'outputs/{version_name}_image_{idx}_eval.json'")

if __name__ == "__main__":
    main()
