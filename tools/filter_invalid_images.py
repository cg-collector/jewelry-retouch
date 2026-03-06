#!/usr/bin/env python3
"""
图像质量检测工具 - 过滤异常图片
检测灰色/空白/过度曝光/严重损坏的图片
"""
import os
import sys
import json
from pathlib import Path
from PIL import Image, ImageStat
import numpy as np
from datetime import datetime


class ImageQualityDetector:
    """图像质量检测器"""

    def __init__(self):
        self.results = []

    def detect_image_quality(self, image_path: str) -> dict:
        """
        检测单张图片的质量

        Returns:
            dict: {
                "valid": bool,  # 是否有效
                "reason": str,  # 原因
                "metrics": dict  # 检测指标
            }
        """
        try:
            img = Image.open(image_path)
            img_rgb = img.convert('RGB')

            # 获取图片尺寸
            width, height = img.size

            # 计算各种指标
            metrics = self.calculate_metrics(img_rgb)

            # 判断是否有效
            valid, reason = self.is_valid_image(metrics)

            return {
                "valid": valid,
                "reason": reason,
                "metrics": metrics,
                "size": f"{width}x{height}"
            }

        except Exception as e:
            return {
                "valid": False,
                "reason": f"文件损坏或无法读取: {str(e)}",
                "metrics": {},
                "size": "unknown"
            }

    def calculate_metrics(self, img_rgb: Image.Image) -> dict:
        """计算图片质量指标"""
        # 转换为numpy数组
        img_array = np.array(img_rgb)

        # 1. 平均亮度
        avg_brightness = np.mean(img_array)

        # 2. RGB标准差（衡量颜色变化）
        std_r = np.std(img_array[:, :, 0])
        std_g = np.std(img_array[:, :, 1])
        std_b = np.std(img_array[:, :, 2])
        avg_std = (std_r + std_g + std_b) / 3

        # 3. 最大最小亮度差
        min_brightness = np.min(img_array)
        max_brightness = np.max(img_array)
        brightness_range = max_brightness - min_brightness

        # 4. 灰度判断（RGB差异小）
        rg_diff = abs(np.mean(img_array[:, :, 0]) - np.mean(img_array[:, :, 1]))
        rb_diff = abs(np.mean(img_array[:, :, 0]) - np.mean(img_array[:, :, 2]))
        gb_diff = abs(np.mean(img_array[:, :, 1]) - np.mean(img_array[:, :, 2]))
        avg_color_diff = (rg_diff + rb_diff + gb_diff) / 3

        # 5. 亮度分布（计算有多少像素在特定范围内）
        # 灰色图片通常大部分像素亮度在很窄的范围内
        dark_pixels = np.sum(img_array < 50) / img_array.size * 100  # 暗像素百分比
        bright_pixels = np.sum(img_array > 200) / img_array.size * 100  # 亮像素百分比
        mid_pixels = 100 - dark_pixels - bright_pixels  # 中等亮度像素

        return {
            "avg_brightness": float(avg_brightness),
            "std_deviation": float(avg_std),
            "brightness_range": float(brightness_range),
            "avg_color_diff": float(avg_color_diff),
            "dark_percent": float(dark_pixels),
            "bright_percent": float(bright_pixels),
            "mid_percent": float(mid_pixels),
            "min_brightness": float(min_brightness),
            "max_brightness": float(max_brightness)
        }

    def is_valid_image(self, metrics: dict) -> tuple:
        """
        判断图片是否有效

        Returns:
            (bool, str): (是否有效, 原因)
        """
        avg_brightness = metrics["avg_brightness"]
        std_deviation = metrics["std_deviation"]
        brightness_range = metrics["brightness_range"]
        avg_color_diff = metrics["avg_color_diff"]
        dark_percent = metrics["dark_percent"]
        bright_percent = metrics["bright_percent"]

        # 规则1: 极暗图片（可能是黑色/全黑）
        if avg_brightness < 30:
            return False, f"图片过暗 (平均亮度: {avg_brightness:.1f})"

        # 规则2: 极亮图片（可能是白色/过曝）
        if avg_brightness > 240:
            return False, f"图片过曝 (平均亮度: {avg_brightness:.1f})"

        # 规则3: 灰色图片（颜色变化小）
        # 判断标准：RGB均值差异小 AND 标准差小
        if avg_color_diff < 5 and std_deviation < 30:
            return False, f"疑似灰色/空白图片 (颜色差异: {avg_color_diff:.1f}, 标准差: {std_deviation:.1f})"

        # 规则4: 亮度范围太小（内容单一）
        if brightness_range < 50 and std_deviation < 25:
            return False, f"图片内容单一 (亮度范围: {brightness_range:.1f}, 标准差: {std_deviation:.1f})"

        # 规则5: 暗像素过多（可能是黑色背景）
        if dark_percent > 80:
            return False, f"暗像素过多 ({dark_percent:.1f}%)"

        # 规则6: 亮像素过多（可能是白色背景）
        if bright_percent > 80:
            return False, f"亮像素过多 ({bright_percent:.1f}%)"

        # 规则7: 标准差极小（图片缺乏变化）
        if std_deviation < 10:
            return False, f"图片缺乏变化 (标准差: {std_deviation:.1f})"

        # 通过所有检测
        return True, "图片质量正常"

    def batch_detect(self, input_dir: str, output_file: str = None):
        """批量检测目录中的所有图片"""
        input_path = Path(input_dir)

        if not input_path.exists():
            print(f"❌ 错误: 目录不存在 - {input_dir}")
            return

        # 获取所有图片文件
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(list(input_path.glob(ext)))

        if not image_files:
            print(f"❌ 错误: 未找到图片文件")
            return

        image_files.sort()

        total = len(image_files)
        print(f"\n{'='*80}")
        print(f"🔍 图像质量批量检测")
        print(f"{'='*80}")
        print(f"输入目录: {input_dir}")
        print(f"图片数量: {total}")
        print(f"{'='*80}\n")

        # 统计信息
        valid_count = 0
        invalid_count = 0
        invalid_reasons = {}

        # 检测每张图片
        for idx, image_file in enumerate(image_files, 1):
            result = self.detect_image_quality(str(image_file))

            result["filename"] = image_file.name
            result["path"] = str(image_file)
            self.results.append(result)

            if result["valid"]:
                valid_count += 1
                if idx <= 10 or idx % 50 == 0:  # 只显示前10张和每50张
                    print(f"[{idx}/{total}] ✅ {image_file.name}")
            else:
                invalid_count += 1
                reason = result["reason"]
                invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1

                print(f"[{idx}/{total}] ❌ {image_file.name}")
                print(f"    原因: {reason}")

        # 保存结果
        if output_file is None:
            output_file = input_path.parent / f"image_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "input_dir": str(input_dir),
            "total_images": total,
            "valid_images": valid_count,
            "invalid_images": invalid_count,
            "invalid_reasons": invalid_reasons,
            "invalid_rate": f"{invalid_count/total*100:.1f}%",
            "results": self.results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 打印统计信息
        print(f"\n{'='*80}")
        print(f"📊 检测统计")
        print(f"{'='*80}")
        print(f"总数: {total}")
        print(f"✅ 有效: {valid_count} ({valid_count/total*100:.1f}%)")
        print(f"❌ 无效: {invalid_count} ({invalid_count/total*100:.1f}%)")
        print(f"\n无效原因分布:")
        for reason, count in sorted(invalid_reasons.items(), key=lambda x: -x[1]):
            print(f"  - {reason}: {count}")
        print(f"\n✅ 检测报告已保存到: {output_file}")
        print(f"{'='*80}\n")

        return report


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='图像质量检测工具 - 过滤异常图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 检测单张图片
  python tools/filter_invalid_images.py \\
    --image data/all/jewelry_xxx.jpg

  # 批量检测
  python tools/filter_invalid_images.py \\
    --batch data/all

  # 批量检测并保存报告
  python tools/filter_invalid_images.py \\
    --batch data/all \\
    --output quality_report.json
        """
    )

    parser.add_argument('--image', type=str, help='单张图片路径')
    parser.add_argument('--batch', type=str, help='输入目录路径（批量模式）')
    parser.add_argument('--output', type=str, help='输出报告文件路径')

    args = parser.parse_args()

    detector = ImageQualityDetector()

    # 单图检测
    if args.image:
        if not Path(args.image).exists():
            print(f"❌ 错误: 图片不存在 - {args.image}")
            return 1

        print(f"\n检测图片: {args.image}")
        result = detector.detect_image_quality(args.image)

        print(f"\n结果:")
        print(f"  有效: {'✅ 是' if result['valid'] else '❌ 否'}")
        print(f"  原因: {result['reason']}")
        print(f"  尺寸: {result['size']}")
        print(f"  指标:")
        for key, value in result['metrics'].items():
            print(f"    {key}: {value:.2f}")

        return 0

    # 批量检测
    if args.batch:
        detector.batch_detect(args.batch, args.output)
        return 0

    # 未指定模式
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
