#!/usr/bin/env python3
"""
提示词版本切换工具
"""
import os
import sys
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent
VERSIONS_DIR = PROMPTS_DIR / "versions"
CURRENT_LINK = PROMPTS_DIR / "current.txt"


def list_versions():
    """列出所有可用版本"""
    versions = sorted(VERSIONS_DIR.glob("*.txt"))
    if not versions:
        print("没有找到版本文件")
        return

    print("\n可用版本:")
    print("=" * 60)
    for v in versions:
        is_current = (CURRENT_LINK.exists() and
                     os.path.realpath(CURRENT_LINK) == str(v))
        prefix = "→" if is_current else " "
        print(f"{prefix} {v.name}")
    print("=" * 60)


def get_current():
    """获取当前版本"""
    if not CURRENT_LINK.exists():
        print("当前版本: 未设置")
        return None

    target = os.path.realpath(CURRENT_LINK)
    version_name = Path(target).name
    print(f"当前版本: {version_name}")
    return version_name


def switch_version(version_file):
    """切换到指定版本"""
    version_path = VERSIONS_DIR / version_file

    if not version_path.exists():
        print(f"错误: 版本文件不存在: {version_file}")
        return False

    # 删除旧链接
    if CURRENT_LINK.exists():
        CURRENT_LINK.unlink()

    # 创建新链接
    os.symlink(version_path, CURRENT_LINK)
    print(f"✓ 已切换到版本: {version_file}")
    return True


def show_version_info(version_file):
    """显示版本详细信息"""
    version_path = VERSIONS_DIR / version_file

    if not version_path.exists():
        print(f"错误: 版本文件不存在: {version_file}")
        return

    print(f"\n版本: {version_file}")
    print("=" * 60)

    with open(version_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 显示前30行预览
    lines = content.split('\n')[:30]
    for line in lines:
        print(line)

    if len(content.split('\n')) > 30:
        print("\n... (内容已截断)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="提示词版本管理工具")
    parser.add_argument("command", nargs="?",
                       choices=["list", "current", "switch", "info"],
                       default="list",
                       help="命令: list(列出版本), current(当前版本), switch(切换), info(查看详情)")
    parser.add_argument("version", nargs="?",
                       help="版本文件名 (用于 switch 和 info 命令)")

    args = parser.parse_args()

    if args.command == "list":
        get_current()
        print()
        list_versions()

    elif args.command == "current":
        get_current()

    elif args.command == "switch":
        if not args.version:
            print("错误: 请指定版本文件名")
            print("用法: python switch_version.py switch <version_file>")
            return 1
        return 0 if switch_version(args.version) else 1

    elif args.command == "info":
        if not args.version:
            print("错误: 请指定版本文件名")
            print("用法: python switch_version.py info <version_file>")
            return 1
        show_version_info(args.version)

    return 0


if __name__ == "__main__":
    sys.exit(main())
