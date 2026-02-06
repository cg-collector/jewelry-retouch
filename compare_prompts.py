#!/usr/bin/env python3
"""
提示词对比测试脚本
用于对比不同提示词版本的效果

使用方法：
1. 修改下方 TEST_CASES 和 PROMPTS 配置
2. 运行: python compare_prompts.py

预设场景：
- 角度测试：对比 v2.1 (保持原图) vs v3.0 (三分角度)
- 版本对比：对比历史版本效果
- 单类型深度测试：针对某类珠宝的多张图测试
"""
import subprocess
import os
import datetime
from pathlib import Path

# ============================================================
# 配置区域 - 根据测试需求修改以下配置
# ============================================================

# 【预设场景1】角度测试 - 项链
# 测试 v2.1 保持原图角度 vs v3.0 强制三分角度
SCENARIO_ANGLE_TEST = {
    "TEST_CASES": [
        {
            "type": "necklace",
            "type_name": "项链",
            "image": "数据/项链/image_1.jpeg"
        },
        {
            "type": "necklace",
            "type_name": "项链",
            "image": "数据/项链/image_2.jpeg"
        },
        {
            "type": "necklace",
            "type_name": "项链",
            "image": "数据/项链/image_3.jpeg"
        },
    ],
    "PROMPTS": [
        {
            "name": "v2.1_universal",
            "file": "prompts/versions/v2.1_ecommerce_universal.txt",
            "label": "v2.1 保持原图角度"
        },
        {
            "name": "v3.0_threequarter",
            "file": "prompts/versions/v3.0_necklace_threequarter.txt",
            "label": "v3.0 三分角度"
        },
    ]
}

# 【预设场景2】全类型对比 - 每类1张
SCENARIO_ALL_TYPES = {
    "TEST_CASES": [
        {"type": "necklace", "type_name": "项链", "image": "数据/项链/image_1.jpeg"},
        {"type": "earring", "type_name": "耳环", "image": "数据/耳环/image_1.jpeg"},
        {"type": "bracelet", "type_name": "手链", "image": "数据/手链/image_1.jpeg"},
        {"type": "bangle", "type_name": "手环", "image": "数据/手环/image_1.jpeg"},
    ],
    "PROMPTS": [
        {
            "name": "v2.1_universal",
            "file": "prompts/versions/v2.1_ecommerce_universal.txt",
            "label": "v2.1 通用版"
        },
        {
            "name": "v3.0_necklace",
            "file": "prompts/versions/v3.0_necklace_threequarter.txt",
            "label": "v3.0 项链专用"
        },
    ]
}

# 【默认场景】使用场景1 - 角度测试
# 修改这里来切换测试场景
CURRENT_SCENARIO = SCENARIO_ANGLE_TEST

TEST_CASES = CURRENT_SCENARIO["TEST_CASES"]
PROMPTS = CURRENT_SCENARIO["PROMPTS"]

# ============================================================
# 技术配置 - 通常不需要修改
# ============================================================
MODEL = "nano-banana-2-2k-vip"
STEPS = 40
TIMEOUT = 300
CONTROL_STRENGTH = 1.0

MODEL = "nano-banana-2-2k-vip"
STEPS = 40
TIMEOUT = 300

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def run_test(image, prompt_file, output_dir):
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
        "--control_strength", str(CONTROL_STRENGTH)
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # 移动生成的文件到正确位置
        temp_output = os.path.join(output_dir, MODEL, "01.png")
        final_output = os.path.join(output_dir, "result.png")

        if os.path.exists(temp_output):
            import shutil
            shutil.move(temp_output, final_output)
            # 清理model目录
            model_dir = os.path.dirname(temp_output)
            if os.path.exists(model_dir):
                shutil.rmtree(model_dir)
            return True, final_output
        else:
            return False, "输出文件未生成"
    except subprocess.CalledProcessError as e:
        return False, str(e)

def main():
    timestamp = get_timestamp()
    base_output = f"outputs/compare_prompts_{timestamp}"

    print(f"\n{'='*70}")
    print(f"提示词对比测试")
    print(f"{'='*70}")
    print(f"配置:")
    print(f"  模型: {MODEL}")
    print(f"  Strength: {CONTROL_STRENGTH}")
    print(f"  测试图片: {len(TEST_CASES)} 张")
    print(f"\n对比方案:")
    for p in PROMPTS:
        print(f"  - {p['name']}: {p['label']}")
        print(f"    文件: {p['file']}")
    print(f"\n输出目录: {base_output}")
    print(f"{'='*70}\n")

    results = []

    for test_case in TEST_CASES:
        type_name = test_case["type_name"]
        image = test_case["image"]
        image_name = Path(image).name

        print(f"\n>>> 测试: {type_name} ({image_name})")

        for prompt in PROMPTS:
            prompt_name = prompt["name"]
            prompt_label = prompt["label"]

            output_dir = os.path.join(base_output, f"{test_case['type']}_{prompt_name}")

            print(f"    [{prompt_name}] {prompt_label}...", end=" ")

            success, result = run_test(image, prompt["file"], output_dir)

            if success:
                print("✓")
                results.append({
                    "type": type_name,
                    "image": image_name,
                    "image_path": image,
                    "prompt": prompt_label,
                    "prompt_name": prompt_name,
                    "status": "success",
                    "output": result
                })
            else:
                print(f"✗ {result}")
                results.append({
                    "type": type_name,
                    "image": image_name,
                    "image_path": image,
                    "prompt": prompt_label,
                    "status": "failed",
                    "error": result
                })

    # 打印结果摘要
    print(f"\n{'='*70}")
    print(f"测试完成！结果摘要")
    print(f"{'='*70}")

    for r in results:
        if r["status"] == "success":
            print(f"✓ {r['type']:8} - {r['prompt']:20}")
            print(f"          {r['output']}")

    print(f"\n所有结果保存在: {base_output}")

    # 生成对比命令
    print(f"\n{'='*70}")
    print(f"快速对比命令:")
    print(f"{'='*70}")

    # 按图片分组生成对比命令
    for test_case in TEST_CASES:
        t = test_case["type"]
        print(f"\n# {test_case['type_name']}: {Path(test_case['image']).name}")

        # 为每个prompt生成命令
        for i, prompt in enumerate(PROMPTS):
            output_path = f"{base_output}/{t}_{prompt['name']}/result.png"
            if os.path.exists(output_path):
                print(f"open '{output_path}'  # {prompt['label']}")

        # 生成并排对比命令
        if len(PROMPTS) >= 2:
            paths = " ".join([f"'{base_output}/{t}_{p['name']}/result.png'" for p in PROMPTS])
            print(f"# 并排对比所有版本:")
            print(f"open {paths}")

    # 原图对比
    print(f"\n# 原图对比:")
    for test_case in TEST_CASES:
        print(f"open '{test_case['image']}'  # {test_case['type_name']} 原图")

if __name__ == "__main__":
    main()
