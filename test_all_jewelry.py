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

# 自动扫描所有珠宝目录（测试项链v4.1 完整环形）
JEWELRY_DIRS = {
    "necklace": "数据/项链",
}

TYPE_NAMES = {
    "necklace": "项链",
    "ring": "戒指",
    "earring": "耳环",
    "bracelet": "手链",
    "bangle": "手环",
}

# 饰品类型到提示词的映射
JEWELRY_PROMPTS = {
    "necklace": "prompts/versions/v4.1_necklace_full_loop.txt",
    "ring": "prompts/versions/v4.2_ring_flat.txt",
}

# 测试配置
CONTROL_STRENGTHS = [1.0]
MODEL = "gemini-3-pro-image-preview-2k-vip"
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


def run_single_test(image, control_strength, output_path, prompt_file):
    """运行单个测试"""
    # 使用临时目录
    temp_dir = output_path + "_temp"

    cmd = [
        "python", "tools/quick_prompt_test.py",
        "--image", image,
        "--prompt_file", prompt_file,
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
            # 从stdout中提取API错误信息
            error_msg = extract_api_error(result.stdout)
            return False, error_msg
    except subprocess.CalledProcessError as e:
        # 命令执行失败（非零退出码）
        error_msg = f"命令失败(退出码{e.returncode}): {extract_api_error(e.stdout) if e.stdout else str(e)}"
        return False, error_msg
    except Exception as e:
        # 其他异常
        return False, f"异常: {str(e)}"


def extract_api_error(output):
    """从API输出中提取错误信息"""
    if not output:
        return "无错误信息"

    # 查找常见错误模式
    import re

    # 503错误
    if "503 Server Error" in output:
        match = re.search(r'"message":"([^"]+)"', output)
        if match:
            return f"503错误: {match.group(1)}"
        return "503错误: 服务不可用"

    # 500错误
    if "500 Server Error" in output:
        match = re.search(r'"message":"([^"]+)"', output)
        if match:
            return f"500错误: {match.group(1)}"
        return "500错误: 服务器内部错误"

    # 400错误
    if "400 Bad Request" in output:
        match = re.search(r'"message":"([^"]+)"', output)
        if match:
            return f"400错误: {match.group(1)}"
        return "400错误: 请求格式错误"

    # Generation failed
    if "Generation failed:" in output:
        match = re.search(r"Generation failed: (.+)", output)
        if match:
            return match.group(1).strip()
        return "生成失败"

    # API Request failed
    if "API Request failed:" in output:
        match = re.search(r"API Request failed: (.+)", output)
        if match:
            return match.group(1).strip()
        return "API请求失败"

    # 返回最后几行作为fallback
    lines = output.strip().split('\n')
    if len(lines) > 3:
        return " | ".join(lines[-3:])
    elif lines:
        return lines[-1]

    return output[-200:] if len(output) > 200 else output


def main():
    import argparse
    parser = argparse.ArgumentParser(description='全量珠宝数据测试')
    parser.add_argument('--workers', type=int, default=1, help='并发线程数 (默认: 1)')
    parser.add_argument('--yes', action='store_true', help='跳过确认直接开始测试')
    args = parser.parse_args()

    MAX_WORKERS = args.workers

    timestamp = get_timestamp()

    print(f"\n{'='*70}")
    print(f"全量珠宝数据测试")
    print(f"{'='*70}")
    print(f"测试值: {CONTROL_STRENGTHS}")
    print(f"模型: {MODEL}")
    print(f"并发数: {MAX_WORKERS}")
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

        # 获取该饰品类型对应的提示词
        prompt_file = JEWELRY_PROMPTS.get(jewelry_type, list(JEWELRY_PROMPTS.values())[0])

        # 从提示词文件名提取角度信息
        prompt_filename = prompt_file.split("/")[-1]
        if "V_shape" in prompt_filename:
            item_angle = "V_shape"
        elif "full_loop" in prompt_filename:
            item_angle = "full_loop"
        elif "flat" in prompt_filename:
            item_angle = "flat"
        elif "pendant_closeup" in prompt_filename:
            item_angle = "pendant_closeup"
        elif "threequarter" in prompt_filename:
            item_angle = "threequarter"
        elif "frontal" in prompt_filename:
            item_angle = "frontal"
        elif "topdown" in prompt_filename:
            item_angle = "topdown"
        elif "profile" in prompt_filename:
            item_angle = "profile"
        else:
            item_angle = "universal"

        # 为每个类型创建独立的输出目录：饰品名_角度_时间戳
        type_output_dir = f"outputs/{jewelry_type}_{item_angle}_{timestamp}"
        os.makedirs(type_output_dir, exist_ok=True)

        print(f"\n{'='*70}")
        print(f">>> 测试类型: {type_name} ({len(images)} 张图片)")
        print(f"{'='*70}")

        for img_idx, image in enumerate(images, 1):
            image_name = Path(image).name
            print(f"\n  [{img_idx}/{len(images)}] {image_name}")

            for strength in CONTROL_STRENGTHS:
                # 生成文件名：01.png, 02.png, ...（与 quick_final_test 保持一致）
                output_filename = f"{img_idx:02d}.png"
                output_path = os.path.join(type_output_dir, output_filename)

                print(f"    strength={strength} ... ", end="", flush=True)

                success, error = run_single_test(image, strength, output_path, prompt_file)

                results.append({
                    "type": type_name,
                    "jewelry_type": jewelry_type,
                    "image": image_name,
                    "input": image,  # 添加输入图像路径
                    "image_index": img_idx,
                    "strength": strength,
                    "model": MODEL,  # 添加使用的模型
                    "status": "success" if success else "failed",
                    "error": error,
                    "output": output_path
                })

                completed += 1

                if success:
                    print(f"✓ ({completed}/{total_tests})")
                else:
                    print(f"✗ ({completed}/{total_tests})")

    # 保存结果到JSON（每个饰品类型独立保存）
    result_files = []
    for test_case in test_cases:
        jewelry_type = test_case["type"]
        type_results = [r for r in results if r["jewelry_type"] == jewelry_type]
        if type_results:
            # 从该类型的第一个结果中获取输出路径，提取角度
            first_result = type_results[0]
            output_dir = os.path.dirname(first_result["output"])
            result_file = os.path.join(output_dir, "results.json")
            result_files.append(result_file)
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(type_results, f, ensure_ascii=False, indent=2)

    # 打印统计摘要
    print(f"\n{'='*70}")
    print(f"测试完成！结果摘要")
    print(f"{'='*70}")

    for test_case in test_cases:
        type_name = test_case["type_name"]
        jewelry_type = test_case["type"]
        type_results = [r for r in results if r["jewelry_type"] == jewelry_type]
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
    print(f"{'='*70}")

    # 快速查看命令
    print(f"\n快速查看命令:")
    for test_case in test_cases:
        type_name = test_case["type_name"]
        jewelry_type = test_case["type"]
        type_results = [r for r in results if r["jewelry_type"] == jewelry_type]
        if type_results:
            type_dir = os.path.dirname(type_results[0]["output"])
            print(f"\n# {type_name}:")
            print(f"open \"{type_dir}\"")

    print(f"\n\n# 单独查看某张图片:")
    for r in results:
        if r["status"] == "success":
            print(f'open "{r["output"]}"  # {r["type"]} - {r["image"]}')

    return 0 if overall_success == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
