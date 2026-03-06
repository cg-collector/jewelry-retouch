#!/usr/bin/env python3
"""
原图 vs 生成图对比工具
支持单对对比和批量多对对比模式
"""
import sys
import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_single_comparison(before_path, after_path, output_path="comparison.png",
                            scale=1, label_before="BEFORE", label_after="AFTER",
                            show_labels=True):
    """
    创建单对对比图（左右并排）

    Args:
        before_path: 原图路径
        after_path: 生成图路径
        output_path: 输出路径
        scale: 缩放倍数（1=原始尺寸, 2=2倍分辨率）
        label_before: 左图标签
        label_after: 右图标签
        show_labels: 是否显示标签
    """
    try:
        # 打开图片
        before = Image.open(before_path)
        after = Image.open(after_path)

        # 获取原始尺寸
        bw, bh = before.size
        aw, ah = after.size

        # 计算输出尺寸
        max_height = max(bh, ah)
        padding = 50  # 中间间距
        total_width = bw + aw + padding

        # 创建新图片
        comparison = Image.new('RGB', (total_width, max_height), (255, 255, 255))

        # 粘贴图片（居中对齐）
        comparison.paste(before, (0, (max_height - bh) // 2))
        comparison.paste(after, (bw + padding, (max_height - ah) // 2))

        # 添加标签
        if show_labels:
            draw = ImageDraw.Draw(comparison)

            # 尝试加载字体
            try:
                # macOS 系统字体
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(36 * scale))
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(24 * scale))
            except:
                try:
                    # Linux 备用字体
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(36 * scale))
                    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(24 * scale))
                except:
                    font = None
                    font_small = None

            # 绘制标签背景和文字
            label_y = 20

            # BEFORE 标签
            if font:
                bbox = draw.textbbox((0, 0), label_before, font=font)
                text_width = bbox[2] - bbox[0]
                draw.rectangle([10, label_y, 10 + text_width + 20, label_y + int(50 * scale)],
                             fill=(255, 200, 200))
                draw.text((20, label_y + int(10 * scale)), label_before,
                         fill=(200, 0, 0), font=font)
            else:
                draw.text((20, label_y), label_before, fill=(255, 0, 0))

            # AFTER 标签
            if font:
                bbox = draw.textbbox((0, 0), label_after, font=font)
                text_width = bbox[2] - bbox[0]
                draw.rectangle([bw + padding + 10, label_y,
                              bw + padding + 10 + text_width + 20, label_y + int(50 * scale)],
                             fill=(200, 255, 200))
                draw.text((bw + padding + 20, label_y + int(10 * scale)), label_after,
                         fill=(0, 150, 0), font=font)
            else:
                draw.text((bw + padding + 20, label_y), label_after, fill=(0, 200, 0))

            # 添加图片信息
            if font_small:
                info_y = max_height - int(60 * scale)
                draw.text((20, info_y), f"{bw}×{bh}", fill=(100, 100, 100), font=font_small)
                draw.text((bw + padding + 20, info_y), f"{aw}×{ah}", fill=(100, 100, 100), font=font_small)

        # 应用缩放
        if scale != 1:
            new_width = int(total_width * scale)
            new_height = int(max_height * scale)
            comparison = comparison.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 保存
        comparison.save(output_path, quality=95, optimize=True)

        # 获取文件信息
        before_size = os.path.getsize(before_path) / (1024 * 1024)
        after_size = os.path.getsize(after_path) / (1024 * 1024)
        comparison_size = os.path.getsize(output_path) / (1024 * 1024)

        print(f"\n✅ 对比图已生成: {output_path}")
        print(f"   原图: {before_path}")
        print(f"   大小: {before_size:.2f} MB, 尺寸: {bw}×{bh}")
        print(f"   生成图: {after_path}")
        print(f"   大小: {after_size:.2f} MB, 尺寸: {aw}×{ah}")
        print(f"   对比图: {output_path}")
        print(f"   大小: {comparison_size:.2f} MB, 尺寸: {comparison.size[0]}×{comparison.size[1]}")
        print(f"   缩放倍数: {scale}x")

        return output_path

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_batch_comparison(result_dir, output_dir=None, mode="grid", cols=2, scale=1):
    """
    批量生成对比图

    Args:
        result_dir: 结果目录（包含 results.json）
        output_dir: 输出目录
        mode: 输出模式
            - "separate": 每对生成单独的对比图
            - "grid": 所有图片生成一个大网格
        cols: 网格列数
        scale: 缩放倍数
    """
    result_path = Path(result_dir)
    json_file = result_path / "results.json"

    if not json_file.exists():
        print(f"❌ 错误: 未找到结果文件 {json_file}")
        return False

    # 读取结果
    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # 筛选成功的结果
    success_results = [r for r in results if r["status"] == "success"]

    if not success_results:
        print("❌ 没有找到成功的测试结果")
        return False

    print(f"\n📊 找到 {len(success_results)} 对成功的图片")

    # 设置输出目录
    if output_dir is None:
        output_dir = result_path / "comparisons"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    if mode == "separate":
        # 每对生成单独的对比图
        print(f"\n📁 模式: 单独生成（每对一张）")
        print(f"📁 输出目录: {output_dir}\n")

        count = 0
        for i, r in enumerate(success_results, 1):
            before_path = r["image"]
            after_path = r["output"]

            # 检查文件是否存在
            if not os.path.exists(before_path):
                print(f"⚠️  [{i}/{len(success_results)}] 原图不存在: {before_path}")
                continue
            if not os.path.exists(after_path):
                print(f"⚠️  [{i}/{len(success_results)}] 生成图不存在: {after_path}")
                continue

            # 生成文件名
            jewelry_type = r.get("jewelry_type", "unknown")
            image_name = Path(r["image"]).stem
            output_name = f"{jewelry_type}_{image_name}_comparison.png"
            output_path = output_dir / output_name

            # 创建对比图
            print(f"📝 [{i}/{len(success_results)}] {r['type']} - {image_name}")
            result = create_single_comparison(
                before_path,
                after_path,
                str(output_path),
                scale=scale,
                label_before="原图",
                label_after="生成图"
            )

            if result:
                count += 1

        print(f"\n✅ 成功生成 {count}/{len(success_results)} 张对比图")
        print(f"📁 输出目录: {output_dir}")

        return True

    elif mode == "grid":
        # 生成网格对比图
        print(f"\n📊 模式: 网格布局（{cols}列）")

        # 计算网格大小
        rows = (len(success_results) + cols - 1) // cols

        print(f"📐 网格大小: {rows}行 × {cols}列")

        # 收集所有图片
        images_data = []
        for r in success_results:
            if os.path.exists(r["image"]) and os.path.exists(r["output"]):
                images_data.append({
                    "before": Image.open(r["image"]),
                    "after": Image.open(r["output"]),
                    "label": f"{r['type']} - {Path(r['image']).stem}"
                })

        if not images_data:
            print("❌ 没有有效的图片数据")
            return False

        # 统一尺寸（取最大值）
        max_before_w = max(img["before"].size[0] for img in images_data)
        max_before_h = max(img["before"].size[1] for img in images_data)
        max_after_w = max(img["after"].size[0] for img in images_data)
        max_after_h = max(img["after"].size[1] for img in images_data)

        cell_width = max_before_w + max_after_w + 50  # padding
        cell_height = max(max_before_h, max_after_h)

        # 创建网格画布
        grid_width = cols * cell_width + 100  # 边距
        grid_height = rows * cell_height + 150  # 标题区域

        grid = Image.new('RGB', (grid_width, grid_height), (250, 250, 250))

        # 绘制标题
        draw = ImageDraw.Draw(grid)
        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(40 * scale))
            font_label = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(24 * scale))
        except:
            font_title = None
            font_label = None

        if font_title:
            draw.text((50, 30), "原图 vs 生成图对比", fill=(50, 50, 50), font=font_title)
        else:
            draw.text((50, 30), "原图 vs 生成图对比", fill=(50, 50, 50))

        # 填充网格
        for idx, img_data in enumerate(images_data):
            row = idx // cols
            col = idx % cols

            x = col * cell_width + 50
            y = row * cell_height + 100

            # 绘制背景
            draw.rectangle([x, y, x + cell_width - 20, y + cell_height - 20],
                         fill=(255, 255, 255), outline=(200, 200, 200))

            # 粘贴图片
            inner_x = x + 10
            inner_y = y + 40  # 标签空间

            # 原图
            before = img_data["before"]
            grid.paste(before, (inner_x, inner_y + (cell_height - 40 - before.size[1]) // 2))

            # 生成图
            after = img_data["after"]
            grid.paste(after, (inner_x + max_before_w + 25,
                              inner_y + (cell_height - 40 - after.size[1]) // 2))

            # 标签
            if font_label:
                draw.text((inner_x, y + 10), "原图", fill=(200, 0, 0), font=font_label)
                draw.text((inner_x + max_before_w + 25, y + 10), "生成图", fill=(0, 150, 0), font=font_label)
                draw.text((inner_x, y + cell_height - 50), img_data["label"],
                         fill=(100, 100, 100), font=font_label)

        # 保存
        if scale != 1:
            grid = grid.resize((int(grid_width * scale), int(grid_height * scale)),
                              Image.Resampling.LANCZOS)

        output_path = output_dir / f"grid_comparison_{cols}cols.png"
        grid.save(output_path, quality=95, optimize=True)

        comparison_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\n✅ 网格对比图已生成")
        print(f"   文件: {output_path}")
        print(f"   大小: {comparison_size:.2f} MB")
        print(f"   尺寸: {grid.size[0]}×{grid.size[1]}")
        print(f"   内容: {len(images_data)} 对图片")

        return True

    else:
        print(f"❌ 未知的模式: {mode}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="原图 vs 生成图对比工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 单对模式 - 生成一张对比图
  python tools/side_by_side_comparison.py \\
    --before 数据/项链/image_1.jpeg \\
    --after outputs/test/necklace/01.png \\
    --output comparison.png \\
    --scale 2

  # 批量模式 - 单独生成每对
  python tools/side_by_side_comparison.py \\
    --result-dir outputs/quick_final_test_20260205_111109 \\
    --mode separate \\
    --scale 2

  # 批量模式 - 网格布局
  python tools/side_by_side_comparison.py \\
    --result-dir outputs/quick_final_test_20260205_111109 \\
    --mode grid \\
    --cols 3
        """
    )

    # 单对模式参数
    parser.add_argument("--before", help="原图路径（单对模式）")
    parser.add_argument("--after", help="生成图路径（单对模式）")
    parser.add_argument("--output", default="comparison.png", help="输出路径（单对模式）")

    # 批量模式参数
    parser.add_argument("--result-dir", help="结果目录（批量模式）")
    parser.add_argument("--mode", choices=["separate", "grid"], help="批量模式：separate=单独生成, grid=网格布局")
    parser.add_argument("--cols", type=int, default=2, help="网格列数（grid模式）")

    # 通用参数
    parser.add_argument("--scale", type=float, default=1.0, help="缩放倍数（1=原始, 2=2倍分辨率）")
    parser.add_argument("--output-dir", help="批量模式输出目录")

    args = parser.parse_args()

    # 判断模式
    if args.before and args.after:
        # 单对模式
        print("\n" + "="*70)
        print("单对对比模式")
        print("="*70)

        if not os.path.exists(args.before):
            print(f"❌ 错误: 原图不存在 - {args.before}")
            return 1

        if not os.path.exists(args.after):
            print(f"❌ 错误: 生成图不存在 - {args.after}")
            return 1

        result = create_single_comparison(
            args.before,
            args.after,
            args.output,
            scale=args.scale
        )

        return 0 if result else 1

    elif args.result_dir:
        # 批量模式
        if not args.mode:
            print("❌ 错误: 批量模式需要指定 --mode (separate 或 grid)")
            return 1

        print("\n" + "="*70)
        print("批量对比模式")
        print("="*70)

        if not os.path.exists(args.result_dir):
            print(f"❌ 错误: 结果目录不存在 - {args.result_dir}")
            return 1

        result = create_batch_comparison(
            args.result_dir,
            output_dir=args.output_dir,
            mode=args.mode,
            cols=args.cols,
            scale=args.scale
        )

        return 0 if result else 1

    else:
        parser.print_help()
        print("\n❌ 错误: 请指定单对模式（--before + --after）或批量模式（--result-dir + --mode）")
        return 1


if __name__ == "__main__":
    sys.exit(main())
