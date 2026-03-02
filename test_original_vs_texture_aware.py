#!/usr/bin/env python3
"""
对比测试：原版 vs 纹理感知版 (v3.3, v3.4, v3.5)
"""
import subprocess
import os
from pathlib import Path
import datetime

# 配置
SAMPLE_SIZE = 2  # 测试2张图片

VERSIONS = {
    "v3.3": {
        "original": "prompts/versions/v3.3_bracelet_topdown.txt",
        "texture_aware": "prompts/versions/v3.3_bracelet_topdown_texture_aware.txt",
        "name": "手链俯视平放",
        "dir": "数据/手链",
        "original_words": 42,
        "texture_words": 152
    },
    "v3.4": {
        "original": "prompts/versions/v3.4_bangle_profile.txt",
        "texture_aware": "prompts/versions/v3.4_bangle_profile_texture_aware.txt",
        "name": "手镯平放",
        "dir": "数据/手链",
        "original_words": 42,
        "texture_words": 149
    },
    "v3.5": {
        "original": "prompts/versions/v3.5_bangle_45degree.txt",
        "texture_aware": "prompts/versions/v3.5_bangle_45_texture_aware.txt",
        "name": "手镯45度",
        "dir": "数据/手链",
        "original_words": 80,
        "texture_words": 165
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

def run_single_test(image, prompt_file, output_dir, label, index):
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
        print(f"Testing {label}")
        print(f"Image: {Path(image).name}")
        print(f"{'='*70}")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # 移动生成的文件到正确位置
        src = os.path.join(temp_dir, MODEL, "01.png")
        dst = os.path.join(output_dir, f"{label}_{index:02d}_{Path(image).stem}.png")

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
    print(f"\n{'='*70}")
    print(f"原版 vs 纹理感知版对比测试")
    print(f"{'='*70}")
    print(f"测试版本: {len(VERSIONS)} 个（每个版本测试2个提示词版本）")
    for v, info in VERSIONS.items():
        print(f"  - {v}: {info['name']}")
        print(f"    原版: {info['original_words']}词")
        print(f"    纹理感知版: {info['texture_words']}词")
    print(f"模型: {MODEL}")
    print(f"重点: 对比纹理保持效果")
    print(f"{'='*70}\n")

    # 创建输出目录
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"outputs/original_vs_texture_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # 扫描测试图片（使用相同的图片）
    test_dir = list(VERSIONS.values())[0]["dir"]
    images = scan_images(test_dir, SAMPLE_SIZE)

    if not images:
        print(f"❌ No images found in {test_dir}")
        return

    print(f"测试图片: {len(images)} 张\n")

    # 运行所有测试
    total_tests = len(VERSIONS) * 2 * len(images)  # 3版本 × 2变体 × 2图片
    completed_tests = 0
    success_count = 0
    all_results = {}
    test_commands = []

    for version_name in VERSIONS:
        all_results[version_name] = {
            "original": [],
            "texture_aware": []
        }

        for variant in ["original", "texture_aware"]:
            prompt_file = VERSIONS[version_name][variant]
            label = f"{version_name}_{variant}"

            for idx, image in enumerate(images, 1):
                success, error, image_path = run_single_test(
                    image, prompt_file, output_dir, label, idx
                )

                result = {
                    'image': image_path,
                    'success': success,
                    'error': error
                }

                all_results[version_name][variant].append(result)
                completed_tests += 1

                if success:
                    success_count += 1
                    print(f"✓ Success ({success_count}/{completed_tests}/{total_tests})")

                    # 保存VLM评估命令
                    output_file = os.path.join(output_dir, f"{label}_{idx:02d}_{Path(image).stem}.png")
                    test_commands.append({
                        'version': version_name,
                        'variant': variant,
                        'name': VERSIONS[version_name]['name'],
                        'variant_name': '原版' if variant == 'original' else '纹理感知版',
                        'words': VERSIONS[version_name]['original_words'] if variant == 'original' else VERSIONS[version_name]['texture_words'],
                        'image': image,
                        'output': output_file,
                        'index': idx
                    })
                else:
                    print(f"✗ Failed: {error}")

    # 打印总结
    print(f"\n{'='*70}")
    print(f"Test Summary")
    print(f"{'='*70}")
    if total_tests > 0:
        print(f"成功: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    print(f"输出目录: {output_dir}")
    print(f"{'='*70}\n")

    # 生成VLM评估命令
    if test_commands:
        print("下一步: VLM评估（对比原版 vs 纹理感知版）")
        print("\n" + "="*70)
        for cmd in test_commands:
            print(f"\n{cmd['version']} {cmd['variant_name']} ({cmd['words']}词), 图片{cmd['index']}:")
            print(f"python tools/vlm_consistency_evaluator_v3.py \\")
            print(f"  --original '{cmd['image']}' \\")
            print(f"  --generated '{cmd['output']}' \\")
            print(f"  --business '{cmd['name']}，保持纹理和装饰一致' \\")
            print(f"  --output 'outputs/{cmd['version']}_{cmd['variant']}_image_{cmd['index']}_eval.json'")

if __name__ == "__main__":
    main()
