#!/usr/bin/env python3
"""
快速对比查看工具
生成左右拼接的对比图，自动打开，支持快速切换
"""
import subprocess
import json
import time
import os
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse


def find_original_image(image_name, result_dir):
    """查找原图文件"""
    search_dirs = [
        Path("数据/项链"),
        Path("数据/耳环"),
        Path("数据/手链"),
        Path("数据/手环"),
        Path("数据"),
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # 直接匹配
        full_path = search_dir / image_name
        if full_path.exists():
            return str(full_path)

        # 模糊匹配
        try:
            matching = list(search_dir.glob(image_name.split('.')[0] + '.*'))
            if matching:
                return str(matching[0])
        except:
            continue

    return None


def create_comparison_image(before_path, after_path, output_path,
                            scale=1.5, use_jpeg=False):
    """创建对比图（左右并排，无标签）

    Args:
        use_jpeg: 是否使用 JPEG 格式（更快，文件更小）
    """
    try:
        before = Image.open(before_path)
        after = Image.open(after_path)

        bw, bh = before.size
        aw, ah = after.size

        # 计算尺寸
        max_height = max(bh, ah)
        padding = 50
        total_width = bw + aw + padding

        # 创建画布
        comparison = Image.new('RGB', (total_width, max_height), (255, 255, 255))

        # 粘贴图片（居中对齐）
        comparison.paste(before, (0, (max_height - bh) // 2))
        comparison.paste(after, (bw + padding, (max_height - ah) // 2))

        # 应用缩放
        if scale != 1:
            new_width = int(total_width * scale)
            new_height = int(max_height * scale)
            comparison = comparison.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 保存（选择格式）
        if use_jpeg:
            # JPEG 格式：更快，文件更小
            comparison.save(output_path, format='JPEG', quality=95, optimize=True)
        else:
            # PNG 格式：无损，较慢
            comparison.save(output_path, quality=95, optimize=True)

        return True, f"{comparison.size[0]}×{comparison.size[1]}"

    except Exception as e:
        return False, str(e)


class QuickComparisonViewer:
    """快速对比查看器"""

    def __init__(self, result_dir, scale=1.5, save_dir=None, use_jpeg=False):
        self.result_dir = Path(result_dir)
        self.scale = scale
        self.save_dir = save_dir
        self.use_jpeg = use_jpeg
        self.pairs = self._load_pairs()
        self.current_index = 0

        # 创建临时目录
        if save_dir:
            self.temp_dir = Path(save_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.cleanup = False
        else:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="comparison_"))
            self.cleanup = True

        self.current_comparison_path = None

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
            print(f"❌ 错误: 未找到结果文件")
            return []

        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        for r in results:
            if r.get("status") != "success":
                continue

            generated = r.get("output")
            if not generated or not os.path.exists(generated):
                continue

            # 优先读取 input 字段，如果没有则使用 image 字段
            image_field = r.get("input") or r.get("image")
            if not image_field:
                continue

            # 判断是完整路径还是只有文件名
            if os.path.exists(image_field):
                original = image_field
            else:
                # 只有文件名，需要查找原图
                original = find_original_image(image_field, self.result_dir)
                if not original:
                    continue

            pairs.append({
                "type": r.get("type", "unknown"),
                "original": original,
                "generated": generated,
                "original_name": Path(image_field).name
            })

        return pairs

    def current(self):
        """当前对"""
        if 0 <= self.current_index < len(self.pairs):
            return self.pairs[self.current_index]
        return None

    def next(self):
        """下一张"""
        if self.current_index < len(self.pairs) - 1:
            self.current_index += 1
            return True
        return False

    def prev(self):
        """上一张"""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def has_next(self):
        return self.current_index < len(self.pairs) - 1

    def has_prev(self):
        return self.current_index > 0

    def close_preview(self):
        """关闭 Preview"""
        try:
            subprocess.run(["osascript", "-e", 'tell application "Preview" to close every window'],
                          capture_output=True, timeout=5)
            time.sleep(0.3)
        except:
            pass

    def open_current(self):
        """生成并打开当前对比图"""
        pair = self.current()
        if not pair:
            return False

        # 生成文件名
        jewelry_type = pair.get("type", "unknown")
        image_name = Path(pair["original_name"]).stem
        ext = "jpg" if self.use_jpeg else "png"

        if self.save_dir:
            output_name = f"{jewelry_type}_{image_name}_comparison.{ext}"
        else:
            output_name = f"current_{self.current_index:02d}.{ext}"

        output_path = self.temp_dir / output_name

        # 生成对比图
        print(f"\n📝 生成对比图: {pair['type']} - {pair['original_name']}")
        success, result = create_comparison_image(
            pair["original"],
            pair["generated"],
            str(output_path),
            scale=self.scale,
            use_jpeg=self.use_jpeg
        )

        if not success:
            print(f"❌ 生成失败: {result}")
            return False

        # 获取文件大小
        file_size = output_path.stat().st_size / (1024 * 1024)

        print(f"✅ 对比图已生成: {output_path.name}")
        print(f"   尺寸: {result} | 大小: {file_size:.2f} MB | 格式: {'JPEG' if self.use_jpeg else 'PNG'}")

        # 关闭之前的窗口
        self.close_preview()

        # 打开新的对比图
        subprocess.run(["open", "-a", "Preview", str(output_path)],
                      capture_output=True, timeout=5)

        self.current_comparison_path = output_path
        time.sleep(0.5)
        return True

    def show_status(self):
        """显示当前状态"""
        pair = self.current()
        if pair:
            print("\n" + "=" * 70)
            print(f"[{self.current_index + 1}/{len(self.pairs)}] 快速对比查看")
            print("=" * 70)
            print(f"当前: {pair['type']} - {pair['original_name']}")
            print(f"布局: ┌──────────────┬──────────────┐")
            print(f"      │     原图     │    生成图    │")
            print(f"      └──────────────┴──────────────┘")
            print("=" * 70)

    def cleanup_temp(self):
        """清理临时文件"""
        if self.cleanup and self.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                print(f"\n🧹 已清理临时文件")
            except:
                pass


def show_help():
    """显示帮助"""
    print("\n操作说明:")
    print("  Enter 或 n    - 下一张")
    print("  b             - 上一张")
    print("  r             - 重新生成当前对比图")
    print("  s             - 保存当前对比图到文件")
    print("  q             - 退出")
    print("  1-N           - 跳转到指定图片")
    print("  h 或 ?        - 显示帮助")


def main():
    parser = argparse.ArgumentParser(
        description="快速对比查看工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 查看对比（临时文件，退出后自动删除）
  python tools/quick_comparison.py \\
    --result-dir outputs/test_all_jewelry_20260212_204834

  # 快速模式（JPEG 格式，生成更快）
  python tools/quick_comparison.py \\
    --result-dir outputs/test_all_jewelry_20260212_204834 \\
    --fast

  # 保存对比图到指定目录
  python tools/quick_comparison.py \\
    --result-dir outputs/quick_final_test_20260205_111109 \\
    --save-dir comparisons

  # 调整分辨率
  python tools/quick_comparison.py \\
    --result-dir outputs/test_all_jewelry_20260212_204834 \\
    --scale 2.0
        """
    )

    parser.add_argument("--result-dir", required=True,
                       help="结果目录路径")
    parser.add_argument("--scale", type=float, default=1.5,
                       help="缩放倍数（默认1.5，越大越清晰）")
    parser.add_argument("--save-dir", default=None,
                       help="保存目录（不指定则使用临时文件）")
    parser.add_argument("--fast", action="store_true",
                       help="快速模式：使用 JPEG 格式（生成更快，文件更小）")

    args = parser.parse_args()

    if not Path(args.result_dir).exists():
        print(f"❌ 错误: 结果目录不存在 - {args.result_dir}")
        return 1

    viewer = QuickComparisonViewer(
        args.result_dir,
        scale=args.scale,
        save_dir=args.save_dir,
        use_jpeg=args.fast
    )

    if not viewer.pairs:
        print("❌ 没有找到可用的对比图")
        return 1

    print("\n" + "=" * 70)
    print("快速对比查看工具")
    print("=" * 70)
    print(f"结果目录: {args.result_dir}")
    print(f"共 {len(viewer.pairs)} 对对比图")
    print(f"缩放倍数: {args.scale}x")
    print(f"格式: {'JPEG (快速模式)' if args.fast else 'PNG (高质量模式)'}")
    if args.save_dir:
        print(f"保存目录: {args.save_dir}")
    else:
        print(f"临时文件: 退出后自动删除")
    print("=" * 70)

    show_help()

    # 打开第一张
    viewer.show_status()
    viewer.open_current()
    print("\n💡 按 Enter 切换到下一张，或输入 h 查看帮助")

    try:
        while True:
            try:
                cmd = input("\n> ").strip().lower()

                if cmd in ["", "n", "next"]:
                    if viewer.has_next():
                        viewer.next()
                        viewer.show_status()
                        viewer.open_current()
                    else:
                        print(f"\n已经是最后一张了")
                        print(f"输入 q 退出，或 b 返回上一张")

                elif cmd in ["b", "back", "prev"]:
                    if viewer.has_prev():
                        viewer.prev()
                        viewer.show_status()
                        viewer.open_current()
                    else:
                        print(f"\n已经是第一张了")

                elif cmd == "r":
                    print(f"\n重新生成当前对比图...")
                    viewer.open_current()

                elif cmd == "s":
                    if viewer.current_comparison_path and viewer.current_comparison_path.exists():
                        # 保存到当前目录
                        import shutil
                        save_path = Path.cwd() / viewer.current_comparison_path.name
                        shutil.copy2(viewer.current_comparison_path, save_path)
                        print(f"\n✅ 已保存到: {save_path}")
                    else:
                        print(f"\n❌ 没有可保存的对比图")

                elif cmd in ["q", "quit", "exit"]:
                    print(f"\n退出查看工具...")
                    break

                elif cmd in ["h", "help", "?"]:
                    show_help()

                elif cmd.isdigit():
                    index = int(cmd) - 1
                    if 0 <= index < len(viewer.pairs):
                        viewer.current_index = index
                        viewer.show_status()
                        viewer.open_current()
                    else:
                        print(f"\n无效的图片编号，请输入 1-{len(viewer.pairs)}")

                else:
                    print(f"\n未知命令: {cmd}")
                    print("输入 h 查看帮助")

            except KeyboardInterrupt:
                print(f"\n\n退出查看工具...")
                break
            except EOFError:
                print(f"\n\n退出查看工具...")
                break

    finally:
        viewer.close_preview()
        viewer.cleanup_temp()

    print("\n" + "=" * 70)
    print("查看完成！")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
