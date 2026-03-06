#!/usr/bin/env python3
"""
批量VLM评估脚本 - 对所有测试结果进行评估
"""
import subprocess
import os
import sys
import time
from pathlib import Path

# 需要评估的目录列表（相对于check/0303/）
EVALUATION_DIRS = [
    "ring_flat",
    "ring_side",
    "ring_angled",
    "earring_frontal",
    "earring_crossed_vertical",
    "necklace_pendant_closeup",
    "necklace_v_shape",
    "necklace_full_loop",
    "necklace_full_frontal",
    "bracelet_topdown",
    "bangle_profile",
    "bangle_45degree",
]

BASE_DIR = "check/0303"
VLM_SCRIPT = "tools/vlm_evaluator.py"


def run_evaluation(eval_dir):
    """对单个目录运行VLM评估"""
    full_path = os.path.join(BASE_DIR, eval_dir)

    if not os.path.exists(full_path):
        print(f"⚠️  跳过: {eval_dir} - 目录不存在")
        return False

    results_file = os.path.join(full_path, "results.json")
    if not os.path.exists(results_file):
        print(f"⚠️  跳过: {eval_dir} - 没有results.json")
        return False

    print(f"\n{'='*80}")
    print(f"📊 评估: {eval_dir}")
    print(f"{'='*80}")

    cmd = [
        "python3", VLM_SCRIPT,
        "--batch", full_path,
        "--model", "gemini-3-pro-preview"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败: {eval_dir}")
        print(f"错误: {e.stdout}")
        return False
    except Exception as e:
        print(f"❌ 异常: {eval_dir} - {e}")
        return False


def main():
    print("\n" + "="*80)
    print("🔍 批量VLM评估脚本")
    print("="*80)
    print(f"基础目录: {BASE_DIR}")
    print(f"待评估目录数: {len(EVALUATION_DIRS)}")
    print("="*80 + "\n")

    results = {
        "success": [],
        "failed": [],
        "skipped": []
    }

    for idx, eval_dir in enumerate(EVALUATION_DIRS, 1):
        print(f"\n[{idx}/{len(EVALUATION_DIRS)}] 处理 {eval_dir}...")

        success = run_evaluation(eval_dir)

        if success:
            results["success"].append(eval_dir)
        else:
            results["failed"].append(eval_dir)

        # 每个评估之间等待，避免API限流
        if idx < len(EVALUATION_DIRS):
            print(f"\n⏳ 等待3秒后继续...")
            time.sleep(3)

    # 打印汇总
    print("\n" + "="*80)
    print("📋 评估完成汇总")
    print("="*80)
    print(f"✅ 成功: {len(results['success'])}/{len(EVALUATION_DIRS)}")
    print(f"❌ 失败: {len(results['failed'])}/{len(EVALUATION_DIRS)}")
    print(f"⚠️  跳过: {len(results['skipped'])}/{len(EVALUATION_DIRS)}")

    if results['success']:
        print(f"\n✅ 成功的目录:")
        for d in results['success']:
            print(f"   - {d}")

    if results['failed']:
        print(f"\n❌ 失败的目录:")
        for d in results['failed']:
            print(f"   - {d}")

    print("="*80 + "\n")

    # 返回退出码
    return 0 if not results['failed'] else 1


if __name__ == "__main__":
    sys.exit(main())
