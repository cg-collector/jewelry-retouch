#!/usr/bin/env python3
"""
统一珠宝测试脚本 - 支持配置文件，多版本测试
整合了 test_all_jewelry.py 的所有功能
"""
import subprocess
import os
import json
import datetime
import argparse
import glob
import time
from pathlib import Path

# 默认配置
DEFAULT_MODEL = "nano-banana-2"
DEFAULT_STEPS = 40
DEFAULT_TIMEOUT = 300
DEFAULT_CONTROL_STRENGTH = 1.0

TYPE_NAMES = {
    "necklace": "项链",
    "ring": "戒指",
    "earring": "耳环",
    "bracelet": "手链",
    "bangle": "手镯",
}

def load_config(config_file):
    """加载测试配置文件"""
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def scan_images(directory, max_images=None):
    """扫描目录中的图片"""
    images = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
        images.extend(Path(directory).glob(ext))

    images = sorted([str(img) for img in images])
    if max_images:
        images = images[:max_images]

    return images

def extract_api_error(output):
    """从API输出中提取错误信息"""
    if not output:
        return "无错误信息"

    import re

    if "503 Server Error" in output:
        match = re.search(r'"message":"([^"]+)"', output)
        return f"503错误: {match.group(1)}" if match else "503错误: 服务不可用"

    if "500 Server Error" in output:
        match = re.search(r'"message":"([^"]+)"', output)
        return f"500错误: {match.group(1)}" if match else "500错误: 服务器内部错误"

    if "Generation failed:" in output:
        match = re.search(r"Generation failed: (.+)", output)
        return match.group(1).strip() if match else "生成失败"

    lines = output.strip().split('\n')
    return " | ".join(lines[-3:]) if len(lines) > 3 else output[-200:]

def read_prompt_file(prompt_file):
    """读取提示词文件内容"""
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"⚠️  无法读取提示词文件 {prompt_file}: {e}")
        return ""

def run_single_test(image, prompt_file, output_path, model, steps, timeout, strength, max_retries=3, delay_between_attempts=5):
    """运行单个测试，支持重试和延迟"""
    import shutil

    for attempt in range(1, max_retries + 1):
        temp_dir = output_path + "_temp"

        cmd = [
            "python", "tools/quick_prompt_test.py",
            "--image", image,
            "--prompt_file", prompt_file,
            "--single",
            "--model", model,
            "--outdir", temp_dir,
            "--steps", str(steps),
            "--timeout", str(timeout),
            "--control_strength", str(strength)
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            # sanitize model name to match quick_prompt_test.py's behavior
            def sanitize_name(s, max_len=40):
                s = "".join(c if c.isalnum() or c in "-_" else "_" for c in s.lower())
                if len(s) > max_len:
                    s = s[:max_len] + "_"
                return s or "prompt"

            sanitized_model = sanitize_name(model)
            src = os.path.join(temp_dir, sanitized_model, "01.png")

            if os.path.exists(src):
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.move(src, output_path)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                return True, None, output_path
            else:
                # 输出文件未生成，准备重试
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if attempt < max_retries:
                    print(f"  [重试 {attempt}/{max_retries}] 输出文件未生成，{delay_between_attempts}秒后重试...", flush=True)
                    time.sleep(delay_between_attempts)
                else:
                    return False, f"输出文件未生成 (重试{max_retries}次后仍失败)", None

        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            error_msg = extract_api_error(e.stdout) if e.stdout else str(e)

            if attempt < max_retries:
                print(f"  [重试 {attempt}/{max_retries}] 命令失败: {error_msg[:100]}, {delay_between_attempts}秒后重试...", flush=True)
                time.sleep(delay_between_attempts)
            else:
                return False, f"命令失败(退出码{e.returncode}): {error_msg}", None

        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

            if attempt < max_retries:
                print(f"  [重试 {attempt}/{max_retries}] 异常: {str(e)[:100]}, {delay_between_attempts}秒后重试...", flush=True)
                time.sleep(delay_between_attempts)
            else:
                return False, f"异常: {str(e)}", None

    return False, "未知错误", None

def run_tests_from_config(config_file, model, steps, timeout, strength, max_images, max_retries=3, retry_delay=5, test_delay=5):
    """从配置文件运行测试"""
    config = load_config(config_file)
    if not config:
        print("错误: 无法加载配置文件")
        return

    timestamp = get_timestamp()
    all_results = []
    base_output_dir = "v2check"
    os.makedirs(base_output_dir, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"从配置文件运行测试")
    print(f"{'='*70}")
    print(f"配置文件: {config_file}")
    print(f"模型: {model}")
    print(f"{'='*70}\n")

    total_tests = 0
    for suite_key, suite_config in config.get("test_suites", {}).items():
        total_tests += len(suite_config.get("versions", [])) * min(len(scan_images(suite_config["dir"])), max_images if max_images else 9999)

    print(f"总测试数: {total_tests}")
    print(f"{'='*70}\n")

    for suite_key, suite_config in config.get("test_suites", {}).items():
        jewelry_type = suite_key
        type_name = suite_config.get("type", suite_key)
        dir_path = suite_config.get("dir")
        versions = suite_config.get("versions", [])

        if not os.path.exists(dir_path):
            print(f"⚠️  跳过 {type_name}: 目录不存在")
            continue

        images = scan_images(dir_path, max_images)
        if not images:
            print(f"⚠️  跳过 {type_name}: 没有找到图片")
            continue

        print(f"\n{'='*70}")
        print(f">>> 测试套件: {type_name} ({len(images)} 张图片, {len(versions)} 个版本)")
        print(f"{'='*70}\n")

        for version_config in versions:
            version_id = version_config["id"]
            version_name = version_config["name"]
            prompt_file = version_config["prompt"]
            angle = version_config.get("angle", version_id)

            # 读取提示词内容（用于评估脚本）
            prompt_content = read_prompt_file(prompt_file)

            # 创建输出目录 - outputs/{jewelry_type}_{angle}_{timestamp}/
            output_dir = os.path.join(base_output_dir, f"{jewelry_type}_{angle}_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)

            print(f"\n--- {version_id}: {version_name} ---")
            print(f"提示词文件: {prompt_file}")

            for img_idx, image in enumerate(images, 1):
                image_name = Path(image).name
                print(f"\n  [{img_idx}/{len(images)}] {image_name}")

                output_filename = f"{img_idx:02d}.png"
                output_path = os.path.join(output_dir, output_filename)

                print(f"    生成中...", end="", flush=True)

                success, error, actual_output = run_single_test(
                    image, prompt_file, output_path, model, steps, timeout, strength,
                    max_retries=max_retries, delay_between_attempts=retry_delay
                )

                # 每个测试后等待，避免API限流
                if img_idx < len(images):  # 最后一个测试不需要等待
                    print(f"\n    等待{test_delay}秒后继续...", flush=True)
                    time.sleep(test_delay)

                result_entry = {
                    "type": type_name,
                    "suite": jewelry_type,
                    "version": version_id,
                    "version_name": version_name,
                    "angle": angle,
                    "words": version_config.get("words", 0),
                    "image": image_name,
                    "input": image,
                    "image_index": img_idx,
                    "strength": strength,
                    "model": model,
                    "status": "success" if success else "failed",
                    "error": error,
                    "output": actual_output,
                    # 新增：保存提示词信息，供评估脚本使用
                    "prompt_file": prompt_file,
                    "prompt_content": prompt_content
                }

                all_results.append(result_entry)

                if success:
                    print(f" ✓")
                else:
                    print(f" ✗")
                    if error:
                        print(f"    错误: {error}")

        # 为每个套件的每个版本保存results.json
        for version_config in versions:
            version_id = version_config["id"]
            version_results = [r for r in all_results if r["suite"] == jewelry_type and r["version"] == version_id]

            if version_results:
                # 使用 output_dir 变量而不是从 results 获取，因为失败时 output 可能为 None
                result_file = os.path.join(output_dir, "results.json")

                # 保存结果（包含提示词信息）
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(version_results, f, ensure_ascii=False, indent=2)

                # 同时保存提示词到单独的文件，方便评估脚本读取
                prompt_file = version_results[0].get("prompt_file")
                if prompt_file:
                    prompt_backup_file = os.path.join(output_dir, "prompt_used.txt")
                    prompt_content = version_results[0].get("prompt_content", "")
                    if prompt_content:
                        with open(prompt_backup_file, 'w', encoding='utf-8') as f:
                            f.write(prompt_content)
                        print(f"\n✅ 已保存提示词: {prompt_backup_file}")

                print(f"\n✅ 已保存结果: {result_file}")

    # 保存汇总文件到 outputs 目录
    summary_file = os.path.join(base_output_dir, f"all_tests_summary_{timestamp}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": datetime.datetime.now().isoformat(),
            "config_file": config_file,
            "total_tests": len(all_results),
            "model": model,
            "results": all_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已保存汇总: {summary_file}")

    # 打印统计
    print(f"\n{'='*70}")
    print(f"测试完成摘要")
    print(f"{'='*70}")

    success_count = sum(1 for r in all_results if r["status"] == "success")
    print(f"成功: {success_count}/{len(all_results)} ({success_count/len(all_results)*100:.1f}%)")

    for suite_key in config.get("test_suites", {}).keys():
        suite_results = [r for r in all_results if r["suite"] == suite_key]
        if suite_results:
            suite_success = sum(1 for r in suite_results if r["status"] == "success")
            print(f"\n{suite_results[0]['type']}: {suite_success}/{len(suite_results)}")

            for version_config in config.get("test_suites", {})[suite_key].get("versions", []):
                version_id = version_config["id"]
                version_results = [r for r in suite_results if r["version"] == version_id]
                if version_results:
                    v_success = sum(1 for r in version_results if r["status"] == "success")
                    print(f"  {version_id} ({version_config['name']}): {v_success}/{len(version_results)}")

    print(f"{'='*70}\n")

    return 0 if success_count == len(all_results) else 1

def main():
    parser = argparse.ArgumentParser(
        description='统一珠宝测试脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用配置文件测试（推荐）
  python %(prog)s --config test_config.json

  # 测试特定类型的所有图片
  python %(prog)s --type ring --prompts "prompts/versions/v4.2_ring_flat_texture_aware.txt,prompts/versions/v4.3_ring_side_texture_aware.txt"

  # 限制测试图片数量
  python %(prog)s --config test_config.json --max-images 2

  # 查看配置文件中的测试套件
  python %(prog)s --config test_config.json --list
        """
    )

    parser.add_argument('--config', '-c', help='测试配置文件（JSON格式）')
    parser.add_argument('--type', '-t', help='珠宝类型 (ring, earring, necklace等)')
    parser.add_argument('--dir', '-d', help='图片目录（如果与默认不同）')
    parser.add_argument('--prompts', '-p', help='提示词文件（多个用逗号分隔）')
    parser.add_argument('--max-images', '-n', type=int, default=0, help='最大测试图片数（0=全部）')
    parser.add_argument('--model', '-m', default=DEFAULT_MODEL, help=f'使用的模型 (默认: {DEFAULT_MODEL})')
    parser.add_argument('--steps', '-s', type=int, default=DEFAULT_STEPS, help=f'生成步数 (默认: {DEFAULT_STEPS})')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help=f'超时时间(秒) (默认: {DEFAULT_TIMEOUT})')
    parser.add_argument('--strength', type=float, default=DEFAULT_CONTROL_STRENGTH, help=f'Control strength (默认: {DEFAULT_CONTROL_STRENGTH})')
    parser.add_argument('--max-retries', type=int, default=3, help='失败重试次数 (默认: 3)')
    parser.add_argument('--retry-delay', type=int, default=5, help='重试间隔秒数 (默认: 5)')
    parser.add_argument('--test-delay', type=int, default=5, help='每个测试后等待秒数 (默认: 5)')
    parser.add_argument('--list', '-l', action='store_true', help='列出配置文件中的测试套件')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认直接开始测试')

    args = parser.parse_args()

    # 列出配置
    if args.list and args.config:
        config = load_config(args.config)
        if config:
            print(f"\n配置文件: {args.config}")
            print(f"{'='*70}\n")

            for suite_key, suite_config in config.get("test_suites", {}).items():
                print(f"📦 {suite_config.get('type', suite_key)}")
                print(f"  目录: {suite_config.get('dir')}")
                print(f"  版本数: {len(suite_config.get('versions', []))}")
                print()

                for v in suite_config.get("versions", []):
                    print(f"    • {v['id']}: {v['name']}")
                    print(f"      提示词: {v['prompt']}")
                    print(f"      角度: {v.get('angle', 'N/A')}")
                    print()
            return 0

    # 使用配置文件运行测试
    if args.config:
        return run_tests_from_config(
            args.config, args.model, args.steps, args.timeout, args.strength, args.max_images,
            args.max_retries, args.retry_delay, args.test_delay
        )

    # TODO: 添加命令行参数模式（类似test_all_jewelry.py）
    print("错误: 请指定 --config 参数或配置测试参数")
    print("使用 --help 查看帮助")
    return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
