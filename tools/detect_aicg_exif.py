#!/usr/bin/env python3
"""
基于EXIF信息快速检测AIGC图
不使用API，速度快但准确性较低
"""
import os
import sys
import json
from pathlib import Path
from PIL import Image
from datetime import datetime


class AICGEXIFDetector:
    """基于EXIF检测AIGC图"""

    def __init__(self):
        self.results = {
            'aicg_images': [],
            'real_images': [],
            'unknown_images': []
        }

    def check_exif(self, image_path: str) -> dict:
        """
        检查图片EXIF信息

        Returns:
            dict: {
                'is_aicg': bool,
                'confidence': str,
                'reason': str,
                'exif_data': dict
            }
        """
        try:
            img = Image.open(image_path)
            exif_data = {}

            # 获取EXIF信息
            if hasattr(img, '_getexif'):
                exif_raw = img._getexif()
                if exif_raw:
                    import PIL.ExifTags
                    for tag, value in exif_raw.items():
                        decoded = PIL.ExifTags.TAGS.get(tag, tag)
                        exif_data[decoded] = value

            # 检查是否缺少相机信息
            has_camera_info = (
                'Make' in exif_data or
                'CameraModelName' in exif_data or
                'LensModel' in exif_data
            )

            # 检查是否有软件信息
            has_software = 'Software' in exif_data

            # 检查图片尺寸（AIGC图常有特定尺寸）
            width, height = img.size
            is_common_aicg_size = (
                (width == 1024 and height == 1024) or
                (width == 512 and height == 512) or
                (width == 768 and height == 768) or
                (width == 1536 and height == 1536)
            )

            # 判断逻辑
            if not has_camera_info:
                if is_common_aicg_size:
                    return {
                        'is_aicg': True,
                        'confidence': '中',
                        'reason': '缺少相机EXIF信息且为常见AIGC尺寸',
                        'exif_data': exif_data
                    }
                else:
                    return {
                        'is_aicg': True,
                        'confidence': '低',
                        'reason': '缺少相机EXIF信息',
                        'exif_data': exif_data
                    }
            else:
                return {
                    'is_aicg': False,
                    'confidence': '高',
                    'reason': f'有相机信息 ({exif_data.get("Make", "Unknown")})',
                    'exif_data': exif_data
                }

        except Exception as e:
            return {
                'is_aicg': None,
                'confidence': '未知',
                'reason': f'EXIF检测失败: {str(e)}',
                'exif_data': {}
            }

    def batch_detect(self, input_dirs: list, output_file: str = None, move_aicg: bool = False, aicg_dir: str = "data/aicg"):
        """批量检测"""
        print(f"\n{'='*80}")
        print(f"🔍 基于EXIF快速检测AIGC图")
        print(f"{'='*80}\n")

        # 收集所有图片
        all_images = []
        for input_dir in input_dirs:
            input_path = Path(input_dir)
            if not input_path.exists():
                continue

            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                all_images.extend(list(input_path.glob(ext)))

        if not all_images:
            print("❌ 未找到图片文件")
            return

        all_images.sort()
        total = len(all_images)

        print(f"输入目录: {', '.join(input_dirs)}")
        print(f"图片总数: {total}")
        if move_aicg:
            print(f"📦 将移动AIGC图片到: {aicg_dir}")
        print(f"{'='*80}\n")

        # 创建AIGC目录
        if move_aicg:
            aicg_path = Path(aicg_dir)
            aicg_path.mkdir(parents=True, exist_ok=True)

        aicg_count = 0
        real_count = 0
        unknown_count = 0
        moved_count = 0

        for idx, image_path in enumerate(all_images, 1):
            print(f"[{idx}/{total}] {image_path.name}... ", end="")

            result = self.check_exif(str(image_path))
            result['filename'] = image_path.name
            result['path'] = str(image_path)

            if result['is_aicg'] is None:
                print(f"❓ {result['reason']}")
                unknown_count += 1
                self.results['unknown_images'].append(result)
            elif result['is_aicg']:
                print(f"🤖 {result['confidence']} - {result['reason']}")
                aicg_count += 1
                self.results['aicg_images'].append(result)

                # 移动AIGC图片
                if move_aicg:
                    try:
                        dest_path = aicg_path / image_path.name
                        import shutil
                        shutil.move(str(image_path), str(dest_path))
                        print(f" → 已移动到 {aicg_dir}")
                        moved_count += 1
                        result['moved'] = True
                        result['destination'] = str(dest_path)
                    except Exception as e:
                        print(f" → 移动失败: {e}")
                        result['moved'] = False
                        result['move_error'] = str(e)
            else:
                print(f"✅ {result['confidence']} - {result['reason']}")
                real_count += 1
                self.results['real_images'].append(result)

        # 保存结果
        if output_file is None:
            output_file = f"data/aicg_exif_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 清理EXIF数据以避免序列化错误
        clean_results = {
            'aicg_images': [],
            'real_images': [],
            'unknown_images': []
        }

        for key in ['aicg_images', 'real_images', 'unknown_images']:
            for item in self.results[key]:
                clean_item = {
                    'filename': item['filename'],
                    'path': item['path'],
                    'is_aicg': item['is_aicg'],
                    'confidence': item['confidence'],
                    'reason': item['reason']
                }
                clean_results[key].append(clean_item)

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_images": total,
            "aicg_count": aicg_count,
            "real_count": real_count,
            "unknown_count": unknown_count,
            "moved_count": moved_count if move_aicg else None,
            "aicg_rate": f"{aicg_count/total*100:.1f}%" if total > 0 else "0%",
            "results": clean_results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 打印统计
        print(f"\n{'='*80}")
        print(f"📊 检测统计")
        print(f"{'='*80}")
        print(f"总数: {total}")
        print(f"🤖 疑似AICG: {aicg_count} ({report['aicg_rate']})")
        if move_aicg:
            print(f"📦 已移动: {moved_count}")
        print(f"✅ 疑似真实: {real_count} ({real_count/total*100:.1f}%)")
        print(f"❓ 未知: {unknown_count}")
        print(f"\n✅ 报告已保存到: {output_file}")
        print(f"{'='*80}\n")

        return report


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='基于EXIF快速检测AIGC图',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 检测项链类别
  python tools/detect_aicg_exif.py \\
    --dirs data/项链
        """
    )

    parser.add_argument('--dirs', type=str, nargs='+', required=True,
                       help='要检测的目录列表')
    parser.add_argument('--output', type=str, help='输出报告文件路径')
    parser.add_argument('--move-aicg', action='store_true',
                       help='将检测到的AIGC图片移动到aicg目录')
    parser.add_argument('--aicg-dir', type=str, default='data/aicg',
                       help='AIGC图片目标目录 (默认: data/aicg)')

    args = parser.parse_args()

    detector = AICGEXIFDetector()
    detector.batch_detect(args.dirs, args.output, args.move_aicg, args.aicg_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
