#!/usr/bin/env python3
"""
交互式结果分析工具
- 自动检测最新的测试结果目录
- 多张图片自动错开排列（使用AppleScript）
"""
import subprocess
import sys
import json
import time
import os
from pathlib import Path
from datetime import datetime

MODEL = "nano-banana-2-2k-vip"
STRENGTHS = [1.0, 0.8, 0.6, 0.4]


def find_latest_result_dir():
    """自动查找最新的测试结果目录"""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return None

    # 查找所有 test_all_jewelry_* 目录
    test_dirs = sorted(outputs_dir.glob("test_all_jewelry_*"),
                      key=lambda p: p.stat().st_mtime,
                      reverse=True)

    if not test_dirs:
        return None

    latest_dir = test_dirs[0]

    # 检查是否有 test_results.json
    if not (latest_dir / "test_results.json").exists():
        return None

    return str(latest_dir)


def close_preview_windows():
    """关闭 Preview 的所有窗口"""
    try:
        # 方法1: 使用 AppleScript 关闭所有窗口（更可靠）
        script = '''
tell application "Preview"
    close every window
end tell
'''
        result = subprocess.run(["osascript", "-e", script],
                                capture_output=True, timeout=5)
        time.sleep(0.5)
        return True
    except:
        try:
            # 方法2: 如果 AppleScript 失败，使用 pkill
            subprocess.run(["pkill", "-9", "Preview"],
                          capture_output=True, timeout=3)
            time.sleep(0.5)
            return True
        except:
            return False


def open_images_grid(images, start_x=100, start_y=100, cols=2):
    """以网格形式打开多张图片，设置窗口位置"""
    print(f"\n  正在打开 {len(images)} 张图片...")

    col_width = 550
    row_height = 650

    for i, (strength, img_path) in enumerate(images):
        row = i // cols
        col = i % cols

        x = start_x + col * col_width
        y = start_y + row * row_height

        # 先打开图片
        subprocess.run(["open", "-a", "Preview", str(img_path)],
                      capture_output=True, timeout=5)

        # 等待Preview启动
        time.sleep(0.8)

        # 设置窗口位置
        try:
            script = f'''
tell application "System Events"
    tell process "Preview"
        try
            set frontWindow to front window
            set position of frontWindow to {{{x}, {y}}}
            set size of frontWindow to {{500, 600}}
        end try
    end tell
end tell
'''
            subprocess.run(["osascript", "-e", script],
                          capture_output=True, timeout=3)
        except:
            pass  # 如果设置失败，至少图片已经打开了

        print(f"    ✓ strength={strength} (位置: 行{row+1}, 列{col+1})")

    # 最后等待所有窗口稳定
    time.sleep(1)


class ResultAnalyzer:
    """结果分析器"""

    def __init__(self, result_dir):
        self.result_dir = Path(result_dir)
        self.items = self._scan_results()
        self.current_index = 0

    def _scan_results(self):
        """扫描所有结果"""
        items = []
        json_file = self.result_dir / "test_results.json"

        if not json_file.exists():
            print(f"警告: 未找到测试结果文件 {json_file}")
            return []

        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        # 按图片分组
        by_image = {}
        for r in results:
            if r["status"] == "success":
                img_key = f"{r['image_index']:02d}_{r['image']}"
                if img_key not in by_image:
                    by_image[img_key] = {}
                by_image[img_key][r["strength"]] = r["output"]

        # 转换为列表
        for img_key, strengths in sorted(by_image.items()):
            img_idx, img_name = img_key.split('_', 1)
            items.append({
                "image_index": int(img_idx),
                "image_name": img_name,
                "strengths": strengths
            })

        return items

    def current(self):
        """当前项"""
        if 0 <= self.current_index < len(self.items):
            return self.items[self.current_index]
        return None

    def next(self):
        """下一项"""
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            return True
        return False

    def prev(self):
        """上一项"""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def has_next(self):
        """是否有下一项"""
        return self.current_index < len(self.items) - 1

    def has_prev(self):
        """是否有上一项"""
        return self.current_index > 0

    def open_current(self):
        """打开当前项的所有strength图片"""
        item = self.current()
        if item:
            # 按 strength 排序
            sorted_strengths = sorted(item["strengths"].items(),
                                     key=lambda x: x[0],
                                     reverse=True)  # 1.0, 0.8, 0.6, 0.4

            # 先关闭之前的窗口
            print("    关闭当前窗口...", end="", flush=True)
            closed = close_preview_windows()
            print(" ✓" if closed else " ⚠️ (未检测到窗口)")

            # 以网格形式打开（2列2行）
            open_images_grid(sorted_strengths,
                           start_x=100,
                           start_y=100,
                           cols=2)

    def show_status(self):
        """显示当前状态"""
        item = self.current()
        if item:
            print("\n" + "=" * 60)
            print(f"[{self.current_index + 1}/{len(self.items)}] 图片 {item['image_index']}: {item['image_name']}")
            print("=" * 60)
            print(f"窗口布局: 2列 × 2行 网格（自动错开）")
            print(f"  ┌─────────────┬─────────────┐")
            print(f"  │ strength=1.0│ strength=0.8│")
            print(f"  ├─────────────┼─────────────┤")
            print(f"  │ strength=0.6│ strength=0.4│")
            print(f"  └─────────────┴─────────────┘")
            print("=" * 60)
            print(f"💡 对比要点:")
            print(f"  1. 裁切程度 - 哪个strength的边缘最完整？")
            print(f"  2. 珠宝特征 - 哪个strength保持了样式？")
            print(f"  3. 整体质量 - 哪个strength视觉效果最好？")


def show_help():
    """显示帮助"""
    print("\n操作说明:")
    print("  Enter 或 n    - 下一张图片")
    print("  b             - 上一张图片")
    print("  r             - 重新打开当前组")
    print("  c             - 关闭所有窗口")
    print("  q             - 退出")
    print("  1-N           - 跳转到指定图片")
    print("  h 或 ?        - 显示帮助")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="交互式结果分析工具")
    parser.add_argument("--result-dir", default=None,
                       help="结果目录（不指定则自动检测最新）")

    args = parser.parse_args()

    # 确定结果目录
    if args.result_dir:
        result_dir = args.result_dir
    else:
        result_dir = find_latest_result_dir()
        if not result_dir:
            print("错误: 未找到测试结果目录")
            print("请指定 --result-dir 参数")
            return 1

    if not Path(result_dir).exists():
        print(f"错误: 结果目录不存在: {result_dir}")
        return 1

    analyzer = ResultAnalyzer(result_dir)

    if not analyzer.items:
        print("没有找到测试结果")
        return 1

    print("\n" + "=" * 60)
    print("交互式结果分析工具")
    print("=" * 60)
    print(f"结果目录: {result_dir}")
    print(f"共 {len(analyzer.items)} 张图片，每张4个strength值")
    print("=" * 60)

    show_help()

    # 打开第一组
    analyzer.show_status()
    analyzer.open_current()
    print("\n请查看4张图片，选择效果最好的strength值...")
    print("输入命令 (h 查看帮助):")

    while True:
        try:
            cmd = input("\n> ").strip().lower()

            if cmd in ["", "n", "next"]:
                if analyzer.has_next():
                    analyzer.next()
                    analyzer.show_status()
                    analyzer.open_current()
                    print("\n请查看4张图片，选择效果最好的strength值...")
                else:
                    print("\n已经是最后一张了")
                    print("输入 q 退出，或 b 返回上一张")

            elif cmd in ["b", "back", "prev"]:
                if analyzer.has_prev():
                    analyzer.prev()
                    analyzer.show_status()
                    analyzer.open_current()
                    print("\n请查看4张图片，选择效果最好的strength值...")
                else:
                    print("\n已经是第一张了")
                    print("输入 q 退出，或 Enter 查看下一张")

            elif cmd == "r":
                print("\n重新打开当前组...")
                close_preview_windows()
                analyzer.open_current()

            elif cmd == "c":
                print("\n关闭所有窗口...")
                close_preview_windows()

            elif cmd in ["q", "quit", "exit"]:
                print("\n关闭所有窗口...")
                close_preview_windows()
                print("\n退出分析工具")
                break

            elif cmd in ["h", "help", "?"]:
                show_help()

            elif cmd.isdigit():
                index = int(cmd) - 1
                if 0 <= index < len(analyzer.items):
                    analyzer.current_index = index
                    analyzer.show_status()
                    analyzer.open_current()
                    print("\n请查看4张图片，选择效果最好的strength值...")
                else:
                    print(f"\n无效的图片编号，请输入 1-{len(analyzer.items)}")

            else:
                print(f"\n未知命令: {cmd}")
                print("输入 h 查看帮助")

        except KeyboardInterrupt:
            print("\n\n关闭所有窗口...")
            close_preview_windows()
            print("退出分析工具")
            break
        except EOFError:
            print("\n\n关闭所有窗口...")
            close_preview_windows()
            print("退出分析工具")
            break

    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)
    print("\n建议: 记录每张图片效果最好的strength值")
    print("统计后选择整体表现最好的作为默认值")

    return 0


if __name__ == "__main__":
    sys.exit(main())
