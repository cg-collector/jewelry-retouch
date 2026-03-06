#!/usr/bin/env python3
"""
实时对比查看工具
不保存图片，直接在 Preview 中打开对比图（左右并排）
支持网格布局，兼容不同格式的结果文件
"""
import subprocess
import json
import time
import os
from pathlib import Path
import argparse


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


def open_images_at_positions(images_info, start_x=100, start_y=100):
    """
    在指定位置打开多张图片

    Args:
        images_info: 列表，每个元素是 {"path": 图片路径, "x": x坐标, "y": y坐标}
        start_x: 起始X坐标
        start_y: 起始Y坐标
    """
    for img_info in images_info:
        img_path = img_info["path"]
        x = img_info.get("x", start_x)
        y = img_info.get("y", start_y)

        # 先打开图片
        subprocess.run(["open", "-a", "Preview", str(img_path)],
                      capture_output=True, timeout=5)
        time.sleep(0.6)

        # 设置窗口位置
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
end tell
'''
            subprocess.run(["osascript", "-e", script],
                          capture_output=True, timeout=3)
        except:
            pass


def find_original_image(image_name, result_dir):
    """
    查找原图文件

    Args:
        image_name: 图片文件名（如 "image_1.jpeg"）
        result_dir: 结果目录

    Returns:
        原图完整路径，如果找不到返回 None
    """
    # 可能的原图目录
    search_dirs = [
        Path("数据/项链"),
        Path("数据/耳环"),
        Path("数据/手链"),
        Path("数据/手环"),
        Path("数据"),
        Path(result_dir).parent.parent.parent / "数据" / "项链",
        Path(result_dir).parent.parent.parent / "数据" / "耳环",
        Path(result_dir).parent.parent.parent / "数据" / "手链",
        Path(result_dir).parent.parent.parent / "数据" / "手环",
    ]

    # 在每个目录中搜索
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # 直接匹配
        full_path = search_dir / image_name
        if full_path.exists():
            return str(full_path)

        # 模糊匹配（处理扩展名差异）
        try:
            matching = list(search_dir.glob(image_name.split('.')[0] + '.*'))
            if matching:
                return str(matching[0])
        except:
            continue

    return None


class LiveComparisonViewer:
    """实时对比查看器"""

    def __init__(self, result_dir, cols=2):
        self.result_dir = Path(result_dir)
        self.cols = cols
        self.pairs = self._load_pairs()
        self.current_index = 0

    def _load_pairs(self):
        """加载所有对比对"""
        pairs = []
        json_files = [
            self.result_dir / "results.json",
            self.result_dir / "test_results.json"
        ]

        json_file = None
        for jf in json_files:
            if jf.exists():
                json_file = jf
                break

        if not json_file:
            print(f"错误: 未找到结果文件（尝试了 results.json 和 test_results.json）")
            return []

        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        # 处理不同格式的数据
        for r in results:
            if r.get("status") != "success":
                continue

            # 获取生成图路径
            generated = r.get("output")
            if not generated:
                continue

            if not os.path.exists(generated):
                print(f"警告: 生成图不存在 {generated}")
                continue

            # 获取原图路径
            image_field = r.get("image")
            if not image_field:
                continue

            # 判断是完整路径还是只有文件名
            if os.path.exists(image_field):
                original = image_field
            else:
                # 只有文件名，需要查找原图
                original = find_original_image(image_field, self.result_dir)
                if not original:
                    print(f"警告: 找不到原图 {image_field}")
                    continue

            pairs.append({
                "type": r.get("type", "unknown"),
                "jewelry_type": r.get("jewelry_type", ""),
                "original": original,
                "generated": generated,
                "original_name": Path(image_field).name,
                "strength": r.get("strength", 1.0)
            })

        return pairs

    def current(self):
        """当前组"""
        if 0 <= self.current_index < len(self.pairs):
            return self.pairs[self.current_index:self.current_index + self.cols]
        return None

    def next(self):
        """下一组"""
        if self.current_index + self.cols < len(self.pairs):
            self.current_index += self.cols
            return True
        return False

    def prev(self):
        """上一组"""
        if self.current_index > 0:
            self.current_index = max(0, self.current_index - self.cols)
            return True
        return False

    def has_next(self):
        """是否有下一组"""
        return self.current_index + self.cols < len(self.pairs)

    def has_prev(self):
        """是否有上一组"""
        return self.current_index > 0

    def open_current(self):
        """打开当前组的对比图"""
        current_pairs = self.current()
        if not current_pairs:
            return

        print(f"\n  正在打开对比图...")

        # 先关闭之前的窗口
        close_preview_windows()

        # 计算布局
        images_info = []
        start_x = 100
        start_y = 100
        col_width = 650
        row_height = 750

        for i, pair in enumerate(current_pairs):
            row = i // 2
            col = i % 2

            # 原图（左列）
            original_x = start_x + col * col_width
            original_y = start_y + row * row_height
            images_info.append({
                "path": pair["original"],
                "x": original_x,
                "y": original_y
            })

            # 生成图（右列）
            generated_x = original_x + 620
            generated_y = original_y
            images_info.append({
                "path": pair["generated"],
                "x": generated_x,
                "y": generated_y
            })

            print(f"    [{i+1}] {pair['type']} - {pair['original_name']}")

        # 打开所有图片
        open_images_at_positions(images_info)

        print(f"    ✓ 已打开 {len(current_pairs)} 对对比图")

    def show_status(self):
        """显示当前状态"""
        current_pairs = self.current()
        if current_pairs:
            total = len(self.pairs)
            start = self.current_index + 1
            end = min(self.current_index + self.cols, total)

            print("\n" + "=" * 70)
            print(f"[{start}-{end}/{total}] 实时对比查看")
            print("=" * 70)
            print(f"窗口布局: 每对图片左右并排")
            print(f"  ┌─────────────────┬─────────────────┐")
            print(f"  │     原图        │    生成图        │")
            for i, pair in enumerate(current_pairs):
                print(f"  ├─────────────────┼─────────────────┤")
                print(f"  │ {pair['original_name'][:15]:15} │ 生成结果        │")
            print(f"  └─────────────────┴─────────────────┘")
            print("=" * 70)
            print(f"💡 对比要点:")
            print(f"  1. 角度是否保持一致？")
            print(f"  2. 裁切问题是否改善？")
            print(f"  3. 整体质量如何？")


def show_help():
    """显示帮助"""
    print("\n操作说明:")
    print("  Enter 或 n    - 下一组")
    print("  b             - 上一组")
    print("  r             - 重新打开当前组")
    print("  c             - 关闭所有窗口")
    print("  q             - 退出")
    print("  1-N           - 跳转到指定组")
    print("  h 或 ?        - 显示帮助")


def main():
    parser = argparse.ArgumentParser(
        description="实时对比查看工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 查看指定目录的对比
  python tools/live_comparison.py \\
    --result-dir outputs/test_all_jewelry_20260212_204834

  # 每次显示3对图片
  python tools/live_comparison.py \\
    --result-dir outputs/quick_final_test_20260205_111109 \\
    --cols 3
        """
    )

    parser.add_argument("--result-dir", required=True,
                       help="结果目录路径")
    parser.add_argument("--cols", type=int, default=2,
                       help="每次显示的对比对数量（默认2对）")

    args = parser.parse_args()

    if not Path(args.result_dir).exists():
        print(f"错误: 结果目录不存在 - {args.result_dir}")
        return 1

    viewer = LiveComparisonViewer(args.result_dir, cols=args.cols)

    if not viewer.pairs:
        print("没有找到可用的对比图")
        return 1

    print("\n" + "=" * 70)
    print("实时对比查看工具")
    print("=" * 70)
    print(f"结果目录: {args.result_dir}")
    print(f"共 {len(viewer.pairs)} 对对比图，每次显示 {args.cols} 对")
    print("=" * 70)

    show_help()

    # 打开第一组
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
                    print("\n已经是最后一组了")
                    print("输入 q 退出，或 b 返回上一组")

            elif cmd in ["b", "back", "prev"]:
                if viewer.has_prev():
                    viewer.prev()
                    viewer.show_status()
                    viewer.open_current()
                    print("\n请查看对比效果...")
                else:
                    print("\n已经是第一组了")
                    print("输入 q 退出，或 Enter 查看下一组")

            elif cmd == "r":
                print("\n重新打开当前组...")
                viewer.open_current()

            elif cmd == "c":
                print("\n关闭所有窗口...")
                close_preview_windows()

            elif cmd in ["q", "quit", "exit"]:
                print("\n关闭所有窗口...")
                close_preview_windows()
                print("\n退出查看工具")
                break

            elif cmd in ["h", "help", "?"]:
                show_help()

            elif cmd.isdigit():
                index = (int(cmd) - 1) * args.cols
                if 0 <= index < len(viewer.pairs):
                    viewer.current_index = index
                    viewer.show_status()
                    viewer.open_current()
                    print("\n请查看对比效果...")
                else:
                    max_group = (len(viewer.pairs) + args.cols - 1) // args.cols
                    print(f"\n无效的组号，请输入 1-{max_group}")

            else:
                print(f"\n未知命令: {cmd}")
                print("输入 h 查看帮助")

        except KeyboardInterrupt:
            print("\n\n关闭所有窗口...")
            close_preview_windows()
            print("退出查看工具")
            break
        except EOFError:
            print("\n\n关闭所有窗口...")
            close_preview_windows()
            print("退出查看工具")
            break

    print("\n" + "=" * 70)
    print("查看完成！")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
