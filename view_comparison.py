#!/usr/bin/env python3
"""
原图 vs 生成图 一对一对比查看
每次只显示一对对比图，左边原图，右边生成图
"""
import subprocess
import sys
import json
import time
import os
from pathlib import Path

RESULT_DIR = "outputs/quick_final_test_20260205_111109"


def close_preview_windows():
    """关闭 Preview 的所有窗口"""
    try:
        script = '''
tell application "Preview"
    close every window
end tell
'''
        subprocess.run(["osascript", "-e", script],
                        capture_output=True, timeout=5)
        time.sleep(0.5)
        return True
    except:
        try:
            subprocess.run(["pkill", "-9", "Preview"],
                          capture_output=True, timeout=3)
            time.sleep(0.5)
            return True
        except:
            return False


def open_comparison_pair(original_path, generated_path):
    """打开一对对比图：左边原图，右边生成图"""
    # 第一列：原图
    x1 = 100
    y1 = 100
    open_image_at_position(original_path, x1, y1)

    # 第二列：生成图
    x2 = 800
    y2 = 100
    open_image_at_position(generated_path, x2, y2)


def open_image_at_position(img_path, x, y):
    """打开图片并设置窗口位置"""
    abs_path = Path(img_path).resolve()

    # 先打开
    subprocess.run(["open", "-a", "Preview", str(abs_path)],
                  capture_output=True, timeout=5)
    time.sleep(0.8)

    # 设置位置
    try:
        script = f'''
tell application "System Events"
    tell process "Preview"
    try
        set frontWindow to front window
        set position of frontWindow to {{{x}, {y}}}
        set size of frontWindow to {{600, 700}}
    end try
end tell
'''
        subprocess.run(["osascript", "-e", script],
                      capture_output=True, timeout=3)
    except:
        pass


class PairViewer:
    """图片对查看器"""

    def __init__(self, result_dir):
        self.result_dir = Path(result_dir)
        self.pairs = self._load_pairs()
        self.current_index = 0

    def _load_pairs(self):
        """加载所有对比对"""
        pairs = []
        json_file = self.result_dir / "results.json"

        if not json_file.exists():
            print(f"错误: 未找到结果文件 {json_file}")
            return []

        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        # 只保留成功的，每个result就是一个原图-生成图对
        for r in results:
            if r["status"] == "success":
                pairs.append({
                    "type": r["type"],
                    "jewelry_type": r["jewelry_type"],
                    "original": r["image"],
                    "generated": r["output"],
                    "original_name": Path(r["image"]).name
                })

        return pairs

    def current(self):
        """当前对"""
        if 0 <= self.current_index < len(self.pairs):
            return self.pairs[self.current_index]
        return None

    def next(self):
        """下一对"""
        if self.current_index < len(self.pairs) - 1:
            self.current_index += 1
            return True
        return False

    def prev(self):
        """上一对"""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def has_next(self):
        """是否有下一对"""
        return self.current_index < len(self.pairs) - 1

    def has_prev(self):
        """是否有上一对"""
        return self.current_index > 0

    def open_current(self):
        """打开当前对比对"""
        pair = self.current()
        if not pair:
            return

        print(f"\n  正在打开对比图...")
        print(f"    左边: 原图 ({pair['original_name']})")
        print(f"    右边: 生成图")

        # 先关闭之前的窗口
        close_preview_windows()

        # 打开对比
        open_comparison_pair(pair["original"], pair["generated"])

    def show_status(self):
        """显示当前状态"""
        pair = self.current()
        if pair:
            print("\n" + "=" * 70)
            print(f"[{self.current_index + 1}/{len(self.pairs)}] {pair['type']} - {pair['original_name']}")
            print("=" * 70)
            print(f"窗口布局:")
            print(f"  ┌─────────────────────────┬─────────────────────────┐")
            print(f"  │        原图           │       生成图            │")
            print(f"  │    (左边窗口)         │      (右边窗口)         │")
            print(f"  └─────────────────────────┴─────────────────────────┘")
            print("=" * 70)
            print(f"💡 对比要点:")
            print(f"  1. 角度是否保持一致？")
            print(f"  2. 裁切问题是否改善？")
            print(f"  3. 整体质量如何？")


def show_help():
    """显示帮助"""
    print("\n操作说明:")
    print("  Enter 或 n    - 下一张")
    print("  b             - 上一张")
    print("  r             - 重新打开当前对")
    print("  c             - 关闭所有窗口")
    print("  q             - 退出")
    print("  1-20          - 跳转到指定图片")
    print("  h 或 ?        - 显示帮助")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="原图 vs 生成图一对一对比")
    parser.add_argument("--result-dir", default=RESULT_DIR,
                       help="结果目录")

    args = parser.parse_args()

    if not Path(args.result_dir).exists():
        print(f"错误: 结果目录不存在: {args.result_dir}")
        return 1

    viewer = PairViewer(args.result_dir)

    if not viewer.pairs:
        print("没有找到测试结果")
        return 1

    print("\n" + "=" * 70)
    print("原图 vs 生成图 - 一对一对比查看")
    print("=" * 70)
    print(f"结果目录: {args.result_dir}")
    print(f"共 {len(viewer.pairs)} 张对比图")
    print("=" * 70)

    show_help()

    # 打开第一对
    viewer.show_status()
    viewer.open_current()
    print("\n请查看对比效果...")
    print("输入命令 (h 查看帮助):")

    while True:
        try:
            cmd = input("\n> ").strip().lower()

            if cmd in ["", "n", "next"]:
                if viewer.has_next():
                    viewer.next()
                    viewer.show_status()
                    viewer.open_current()
                    print("\n请查看对比效果...")
                else:
                    print("\n已经是最后一张了")
                    print("输入 q 退出，或 b 返回上一张")

            elif cmd in ["b", "back", "prev"]:
                if viewer.has_prev():
                    viewer.prev()
                    viewer.show_status()
                    viewer.open_current()
                    print("\n请查看对比效果...")
                else:
                    print("\n已经是第一张了")
                    print("输入 q 退出，或 Enter 查看下一张")

            elif cmd == "r":
                print("\n重新打开当前对...")
                close_preview_windows()
                viewer.open_current()

            elif cmd == "c":
                print("\n关闭所有窗口...")
                close_preview_windows()

            elif cmd in ["q", "quit", "exit"]:
                print("\n关闭所有窗口...")
                close_preview_windows()
                print("\n退出对比工具")
                break

            elif cmd in ["h", "help", "?"]:
                show_help()

            elif cmd.isdigit():
                index = int(cmd) - 1
                if 0 <= index < len(viewer.pairs):
                    viewer.current_index = index
                    viewer.show_status()
                    viewer.open_current()
                    print("\n请查看对比效果...")
                else:
                    print(f"\n无效的图片编号，请输入 1-{len(viewer.pairs)}")

            else:
                print(f"\n未知命令: {cmd}")
                print("输入 h 查看帮助")

        except KeyboardInterrupt:
            print("\n\n关闭所有窗口...")
            close_preview_windows()
            print("退出对比工具")
            break
        except EOFError:
            print("\n\n关闭所有窗口...")
            close_preview_windows()
            print("退出对比工具")
            break

    print("\n" + "=" * 70)
    print("对比查看完成！")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
