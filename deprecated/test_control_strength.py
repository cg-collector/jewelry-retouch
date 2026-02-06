#!/usr/bin/env python3
"""
测试不同 control_strength 值对裁切问题的影响
"""
import subprocess
import os
import datetime
from pathlib import Path

# 测试配置
TEST_CASES = [
    {
        "type": "necklace",
        "type_name": "项链",
        "image": "数据/项链/image_1.jpeg",
        "note": "容易出现裁切"
    },
    {
        "type": "earring",
        "type_name": "耳环",
        "image": "数据/耳环/image_1.jpeg",
        "note": "小件物品"
    },
    {
        "type": "bangle",
        "type_name": "手环",
        "image": "数据/手环/image_1.jpeg",
        "note": "透视问题严重"
    },
]

# 测试不同的 control_strength 值
CONTROL_STRENGTHS = [1.0, 0.8, 0.6, 0.4]

PROMPT_FILE = "prompts/current.txt"  # 使用 v2.0 电商版
MODEL = "nano-banana-2-2k-vip"
STEPS = 40
TIMEOUT = 300


def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def run_single_test(image, control_strength, output_dir, test_name):
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
        "--control_strength", str(control_strength)
    ]

    print(f"    strength={control_strength} ... ", end="", flush=True)

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓")
        return True, None
    except subprocess.CalledProcessError as e:
        print(f"✗")
        return False, str(e)


def main():
    timestamp = get_timestamp()
    base_output = f"outputs/test_control_strength_{timestamp}"

    print(f"\n{'='*70}")
    print(f"Control Strength 测试")
    print(f"{'='*70}")
    print(f"测试值: {CONTROL_STRENGTHS}")
    print(f"提示词: {PROMPT_FILE}")
    print(f"模型: {MODEL}")
    print(f"输出目录: {base_output}")
    print(f"{'='*70}\n")

    results = []

    for test_case in TEST_CASES:
        type_name = test_case["type_name"]
        jewelry_type = test_case["type"]
        image = test_case["image"]
        note = test_case["note"]

        print(f"\n>>> 测试: {type_name} ({note})")
        print(f"    输入: {image}")

        for strength in CONTROL_STRENGTHS:
            test_name = f"{jewelry_type}_strength_{str(strength).replace('.', '_')}"
            output_dir = os.path.join(base_output, test_name)

            success, error = run_single_test(image, strength, output_dir, test_name)

            results.append({
                "type": type_name,
                "image": Path(image).name,
                "strength": strength,
                "status": "success" if success else "failed",
                "error": error,
                "output": os.path.join(output_dir, MODEL, "01.png")
            })

    # 打印结果摘要
    print(f"\n{'='*70}")
    print(f"测试完成！结果摘要")
    print(f"{'='*70}")

    # 按类型和 strength 分组
    for test_case in TEST_CASES:
        type_name = test_case["type_name"]
        print(f"\n{type_name}:")
        print(f"{'Strength':<10} {'状态':<8} {'输出路径'}")

        type_results = [r for r in results if r["type"] == type_name]
        for r in type_results:
            status_icon = "✓" if r["status"] == "success" else "✗"
            print(f"{r['strength']:<10.1f} {status_icon:<8} {r['output']}")

    # 统计
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)

    print(f"\n总计: {success_count}/{total_count} 成功")
    print(f"结果保存在: {base_output}")

    # 生成查看命令
    print(f"\n{'='*70}")
    print(f"快速对比命令 (strength 从低到高):")
    print(f"{'='*70}")

    for test_case in TEST_CASES:
        t = test_case["type"]
        print(f"\n# {test_case['type_name']}:")
        for strength in CONTROL_STRENGTHS:
            strength_dir = str(strength).replace('.', '_')
            path = f"{base_output}/{t}_strength_{strength_dir}/{MODEL}/01.png"
            print(f"open '{path}'  # strength={strength}")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
