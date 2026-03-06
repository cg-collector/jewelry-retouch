#!/usr/bin/env python3
"""
关键版本测试脚本 - 测试每个品类最重要的版本
"""
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
import time

# 配置
MODEL = "nano-banana-2"
STRENGTH = 1.0
STEPS = 40
TIMEOUT = 180  # 缩短到3分钟

# 关键版本配置（每个品类选1个最重要的）
KEY_VERSIONS = [
    {
        "version": "v4.1",
        "name": "项链完整环形",
        "file": "prompts/versions/v4.1_necklace_full_loop.txt",
        "category": "项链",
        "test_data_dir": "数据/项链"
    },
    {
        "version": "v4.2",
        "name": "戒指平放俯视",
        "file": "prompts/versions/v4.2_ring_flat_texture_aware.txt",
        "category": "戒指",
        "test_data_dir": "数据/戒指"
    },
    {
        "version": "v4.5",
        "name": "耳环正面双只",
        "file": "prompts/versions/v4.5_earring_frontal_pair.txt",
        "category": "耳环",
        "test_data_dir": "数据/耳环"
    },
    {
        "version": "v4.6",
        "name": "手环平放俯视",
        "file": "prompts/versions/v4.6_bangle_flat_topdown.txt",
        "category": "手环",
        "test_data_dir": "数据/手环"
    },
    {
        "version": "v3.3",
        "name": "手链俯视",
        "file": "prompts/versions/v3.3_bracelet_topdown.txt",
        "category": "手链",
        "test_data_dir": "数据/手链"
    }
]


def collect_images(test_data_dir):
    """收集测试图片"""
    images = []
    if not os.path.exists(test_data_dir):
        return images

    for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
        images.extend(list(Path(test_data_dir).glob(ext)))

    return sorted([str(img) for img in images])


def run_single_test_with_retry(image, prompt_file, output_dir, index, max_retries=2):
    """运行单个测试，支持重试"""
    model_dir_name = MODEL.replace(".", "_")

    for attempt in range(max_retries + 1):
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
            result = subprocess.run(cmd, check=True, capture_output=True, text=True,
                                  timeout=TIMEOUT + 10)

            src = os.path.join(output_dir, model_dir_name, "01.png")
            dst = os.path.join(output_dir, f"{index:03d}.png")

            if os.path.exists(src):
                import shutil
                os.makedirs(output_dir, exist_ok=True)
                shutil.move(src, dst)
                shutil.rmtree(os.path.join(output_dir, model_dir_name))
                return True, None, attempt + 1
            else:
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return False, "输出文件未生成", attempt + 1

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            if attempt < max_retries:
                print(f"  重试 {attempt + 1}/{max_retries}...", end=" ")
                time.sleep(3)
                continue
            return False, str(e), attempt + 1
        except Exception as e:
            return False, str(e), attempt + 1


def test_prompt_version(prompt_config, base_output_dir):
    """测试单个提示词版本"""
    version = prompt_config["version"]
    name = prompt_config["name"]
    prompt_file = prompt_config["file"]
    test_data_dir = prompt_config["test_data_dir"]
    category = prompt_config["category"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_output_dir, f"{version}_{category}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    # 收集测试图片
    images = collect_images(test_data_dir)
    total = len(images)

    if total == 0:
        print(f"\n⚠️  跳过 {version} ({name}): 没有找到测试图片")
        return None

    print(f"\n{'='*80}")
    print(f"测试: {version} - {name}")
    print(f"{'='*80}")
    print(f"品类: {category}")
    print(f"提示词: {prompt_file}")
    print(f"图片数量: {total}")
    print(f"输出目录: {output_dir}")
    print(f"{'='*80}\n")

    results = []
    success_count = 0
    retry_count = 0

    for idx, image in enumerate(images, 1):
        img_name = Path(image).name
        print(f"[{idx}/{total}] {img_name}...", end=" ", flush=True)

        success, error, attempts = run_single_test_with_retry(
            image, prompt_file, output_dir, idx
        )

        if success:
            print(f"✓ (尝试{attempts}次)")
            results.append({
                "input": os.path.abspath(image),
                "image": img_name,
                "output": os.path.join(output_dir, f"{idx:03d}.png"),
                "status": "success"
            })
            success_count += 1
        else:
            print(f"✗ (尝试{attempts}次) {error}")
            results.append({
                "input": os.path.abspath(image),
                "image": img_name,
                "status": "failed",
                "error": error
            })

        if attempts > 1:
            retry_count += 1

    # 保存结果到JSON
    results_file = os.path.join(output_dir, "results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "version": version,
            "name": name,
            "category": category,
            "prompt_file": prompt_file,
            "model": MODEL,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    rate = success_count/total*100 if total > 0 else 0
    print(f"\n{version} ({name}) 测试完成: {success_count}/{total} 成功 ({rate:.1f}%)")
    if retry_count > 0:
        print(f"   重试次数: {retry_count}")

    return {
        "version": version,
        "name": name,
        "category": category,
        "output_dir": output_dir,
        "results_file": results_file,
        "total": total,
        "success": success_count,
        "rate": rate
    }


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output_dir = f"temp/key_versions_test_{timestamp}"
    os.makedirs(base_output_dir, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"关键版本测试 - 每个品类最重要的版本")
    print(f"{'='*80}")
    print(f"模型: {MODEL}")
    print(f"Strength: {STRENGTH}")
    print(f"Timeout: {TIMEOUT}秒")
    print(f"基础输出目录: {base_output_dir}")
    print(f"版本数量: {len(KEY_VERSIONS)}")
    print(f"{'='*80}\n")

    # 测试每个提示词版本
    all_results = {}
    for prompt_config in KEY_VERSIONS:
        result = test_prompt_version(prompt_config, base_output_dir)
        if result:
            all_results[result["version"]] = result

    # 生成汇总报告
    print(f"\n{'='*80}")
    print(f"关键版本测试完成")
    print(f"{'='*80}")

    total_images = sum(r["total"] for r in all_results.values())
    total_success = sum(r["success"] for r in all_results.values())

    print(f"\n总体统计:")
    print(f"  总计: {total_success}/{total_images} 成功 ({total_success/total_images*100:.1f}%)")

    print(f"\n各版本统计:")
    print(f"{'版本':<8} {'品类':<8} {'成功/总数':<12} {'成功率':<10} {'输出目录'}")
    print(f"{'-'*80}")

    for version in sorted(all_results.keys()):
        data = all_results[version]
        print(f"{version:<8} {data['category']:<8} {data['success']}/{data['total']:<10} {data['rate']:>6.1f}%   {data['output_dir']}")

    # 保存汇总结果
    summary_file = os.path.join(base_output_dir, "test_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "model": MODEL,
            "base_output_dir": base_output_dir,
            "versions": {k: {
                "name": v["name"],
                "category": v["category"],
                "output_dir": v["output_dir"],
                "total": v["total"],
                "success": v["success"],
                "rate": v["rate"]
            } for k, v in all_results.items()},
            "overall": {
                "total_versions": len(all_results),
                "total_images": total_images,
                "success": total_success,
                "rate": total_success/total_images*100
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n汇总结果已保存到: {summary_file}")
    print(f"{'='*80}\n")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
