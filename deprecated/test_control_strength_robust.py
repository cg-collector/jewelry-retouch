#!/usr/bin/env python3
"""
稳健版 Control Strength 测试
使用每种类型的多张输入图片进行测试
"""
import subprocess
import os
import datetime
from pathlib import Path

# 测试配置 - 使用多张图片
TEST_CASES = [
    {
        "type": "necklace",
        "type_name": "项链",
        "images": [
            "数据/项链/image_1.jpeg",
            "数据/项链/image_3.jpeg",
            "数据/项链/image_5.jpeg",
        ]
    },
    {
        "type": "earring",
        "type_name": "耳环",
        "images": [
            "数据/耳环/image_1.jpeg",
            "数据/耳环/image_2.jpeg",
            "数据/耳环/image_3.jpeg",
        ]
    },
    {
        "type": "bracelet",
        "type_name": "手链",
        "images": [
            "数据/手链/image_1.jpeg",
            "数据/手链/image_2.jpeg",
        ]
    },
    {
        "type": "bangle",
        "type_name": "手环",
        "images": [
            "数据/手环/image_1.jpeg",
        ]
    },
]

# 测试不同的 control_strength 值
CONTROL_STRENGTHS = [1.0, 0.8, 0.6, 0.4]

PROMPT_FILE = "prompts/current.txt"
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

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, None
    except subprocess.CalledProcessError as e:
        return False, str(e)


def main():
    timestamp = get_timestamp()
    base_output = f"outputs/test_control_robust_{timestamp}"

    print(f"\n{'='*70}")
    print(f"稳健版 Control Strength 测试")
    print(f"{'='*70}")
    print(f"测试值: {CONTROL_STRENGTHS}")
    print(f"提示词: {PROMPT_FILE}")
    print(f"模型: {MODEL}")
    print(f"输出目录: {base_output}")
    print(f"{'='*70}\n")

    total_tests = 0
    for test_case in TEST_CASES:
        total_tests += len(test_case["images"]) * len(CONTROL_STRENGTHS)

    print(f"总测试数: {total_tests} (每种类型的每张图片 × 4种strength值)")

    results = []

    for test_case in TEST_CASES:
        type_name = test_case["type_name"]
        jewelry_type = test_case["type"]

        print(f"\n{'='*70}")
        print(f">>> 测试类型: {type_name}")
        print(f"    图片数量: {len(test_case['images'])} 张")
        print(f"{'='*70}")

        for img_idx, image in enumerate(test_case["images"], 1):
            if not os.path.exists(image):
                print(f"    ⚠️  图片不存在: {image}")
                continue

            image_name = Path(image).name
            print(f"\n    [{img_idx}/{len(test_case['images'])}] {image_name}")

            for strength in CONTROL_STRENGTHS:
                test_name = f"{jewelry_type}_img{img_idx}_strength_{str(strength).replace('.', '_')}"
                output_dir = os.path.join(base_output, test_name)

                print(f"        strength={strength} ... ", end="", flush=True)

                success, error = run_single_test(image, strength, output_dir, test_name)

                results.append({
                    "type": type_name,
                    "image": image_name,
                    "image_index": img_idx,
                    "strength": strength,
                    "status": "success" if success else "failed",
                    "error": error,
                    "output": os.path.join(output_dir, MODEL, "01.png")
                })

                if success:
                    print("✓")
                else:
                    print(f"✗ {error}")

    # 打印结果摘要
    print(f"\n{'='*70}")
    print(f"测试完成！结果摘要")
    print(f"{'='*70}")

    # 按类型分组统计
    for test_case in TEST_CASES:
        type_name = test_case["type_name"]
        type_results = [r for r in results if r["type"] == type_name]

        success_count = sum(1 for r in type_results if r["status"] == "success")

        print(f"\n{type_name}:")
        print(f"  成功: {success_count}/{len(type_results)}")

        # 按图片分组显示
        for img_idx in range(1, len(test_case["images"]) + 1):
            img_results = [r for r in type_results if r["image_index"] == img_idx]
            if img_results:
                img_name = img_results[0]["image"]
                print(f"\n  📷 {img_name}:")
                for r in img_results:
                    if r["status"] == "success":
                        print(f"     strength={r['strength']:.1f}: ✓")
                    else:
                        print(f"     strength={r['strength']:.1f}: ✗")

    # 总体统计
    overall_success = sum(1 for r in results if r["status"] == "success")
    print(f"\n{'='*70}")
    print(f"总计: {overall_success}/{len(results)} 成功")
    print(f"结果保存在: {base_output}")
    print(f"{'='*70}")

    return 0 if overall_success == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
