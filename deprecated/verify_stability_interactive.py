#!/usr/bin/env python3
"""
交互式稳定性验证工具
一组一组地打开图片，支持前后导航
"""
import subprocess
import sys
from pathlib import Path

# 两次测试的目录
TEST1 = "outputs/test_control_strength_20260203_163926"
TEST2 = "outputs/test_control_strength_20260204_103810"
MODEL = "nano-banana-2-2k-vip"

TYPES = ["necklace", "earring", "bangle"]
STRENGTHS = [1.0, 0.8, 0.6, 0.4]

TYPE_NAMES = {
    "necklace": "项链",
    "earring": "耳环",
    "bangle": "手环"
}


class VerificationNavigator:
    """验证导航器"""

    def __init__(self, type_name=None):
        self.type_name = type_name
        self.items = self._build_items()
        self.current_index = 0

    def _build_items(self):
        """构建验证项列表"""
        items = []

        types_to_check = [self.type_name] if self.type_name else TYPES

        for type_name in types_to_check:
            for strength in STRENGTHS:
                strength_dir = str(strength).replace('.', '_')
                img1 = Path(TEST1) / f"{type_name}_strength_{strength_dir}" / MODEL / "01.png"
                img2 = Path(TEST2) / f"{type_name}_strength_{strength_dir}" / MODEL / "01.png"

                if img1.exists() and img2.exists():
                    items.append({
                        "type": type_name,
                        "strength": strength,
                        "img1": img1,
                        "img2": img2,
                        "label": f"{TYPE_NAMES.get(type_name, type_name)} - strength={strength}"
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
        """打开当前项的图片"""
        item = self.current()
        if item:
            subprocess.run(["open", str(item["img1"])])
            subprocess.run(["open", str(item["img2"])])

    def show_status(self):
        """显示当前状态"""
        item = self.current()
        if item:
            print("\n" + "=" * 60)
            print(f"[{self.current_index + 1}/{len(self.items)}] {item['label']}")
            print("=" * 60)
            print(f"🖼️  第1张图片: 【第一次测试】{item['img1'].parent}")
            print(f"   目录: ...{item['img1']}")
            print(f"🖼️  第2张图片: 【第二次测试】{item['img2'].parent}")
            print(f"   目录: ...{item['img2']}")
            print("=" * 60)
            print(f"💡 对比要点: 检查两张图的构图、裁切程度、清晰度是否相似")


def show_help():
    """显示帮助信息"""
    print("\n操作说明:")
    print("  Enter 或 n    - 下一组")
    print("  b             - 上一组")
    print("  q             - 退出")
    print("  h 或 ?        - 显示帮助")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="交互式稳定性验证工具")
    parser.add_argument("--type", choices=TYPES + ["all"],
                       default="all", help="珠宝类型")

    args = parser.parse_args()

    if not Path(TEST1).exists():
        print(f"错误: 第一次测试目录不存在: {TEST1}")
        return 1

    if not Path(TEST2).exists():
        print(f"错误: 第二次测试目录不存在: {TEST2}")
        return 1

    type_name = None if args.type == "all" else args.type

    nav = VerificationNavigator(type_name)

    if not nav.items:
        print("没有找到可对比的图片")
        return 1

    print("\n" + "=" * 60)
    print("交互式稳定性验证工具")
    print("=" * 60)
    print(f"第一次测试: {TEST1}")
    print(f"第二次测试: {TEST2}")
    print(f"共 {len(nav.items)} 组对比")
    print("=" * 60)

    show_help()

    # 打开第一组
    nav.show_status()
    nav.open_current()
    print("\n请对比两张图片的相似度...")
    print("输入命令 (h 查看帮助):")

    while True:
        try:
            cmd = input("\n> ").strip().lower()

            if cmd in ["", "n", "next"]:
                if nav.has_next():
                    nav.next()
                    nav.show_status()
                    nav.open_current()
                    print("\n请对比两张图片的相似度...")
                else:
                    print("\n已经是最后一组了")
                    print("输入 q 退出，或 b 返回上一组")

            elif cmd in ["b", "back", "prev"]:
                if nav.has_prev():
                    nav.prev()
                    nav.show_status()
                    nav.open_current()
                    print("\n请对比两张图片的相似度...")
                else:
                    print("\n已经是第一组了")
                    print("输入 q 退出，或 Enter 查看下一组")

            elif cmd in ["q", "quit", "exit"]:
                print("\n退出验证工具")
                break

            elif cmd in ["h", "help", "?"]:
                show_help()

            elif cmd.isdigit():
                # 跳转到指定组
                index = int(cmd) - 1
                if 0 <= index < len(nav.items):
                    nav.current_index = index
                    nav.show_status()
                    nav.open_current()
                    print("\n请对比两张图片的相似度...")
                else:
                    print(f"\n无效的组号，请输入 1-{len(nav.items)}")

            else:
                print(f"\n未知命令: {cmd}")
                print("输入 h 查看帮助")

        except KeyboardInterrupt:
            print("\n\n检测到 Ctrl+C，退出验证工具")
            break
        except EOFError:
            print("\n\n退出验证工具")
            break

    print("\n" + "=" * 60)
    print("验证完成！")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
