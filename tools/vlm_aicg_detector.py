#!/usr/bin/env python3
"""
使用VLM检测AIGC生成图 - 基于vlm_image_classifier.py的成功实现
"""
import os
import sys
import json
import base64
import requests
import shutil
import time
from pathlib import Path
from datetime import datetime
from PIL import Image
import io


class VLMAICGDetector:
    """使用VLM检测AIGC图"""

    def __init__(self, api_key: str, base_url: str = "https://api.tu-zi.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def encode_image(self, image_path: str, max_size: int = 1024) -> str:
        """编码图片为base64，如果图片过大则压缩"""
        img = Image.open(image_path)

        # 如果图片尺寸超过max_size，则压缩
        if img.size[0] > max_size or img.size[1] > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # 保存到内存并编码为base64
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def build_detection_prompt(self) -> str:
        """构建AICG检测提示词"""
        return """请仔细观察这张珠宝图片，判断它是否为AI生成（AIGC）的图片。

**判断标准：**

1. **AIGC图特征**（如果出现以下特征，很可能是AI生成）：
   - 过度完美/平滑的纹理
   - 不自然的反光和光泽
   - 背景过度纯白或过度虚化
   - 细节过度一致（缺乏随机性）
   - 边缘过度锐利或模糊
   - 珠宝造型不自然/对称过度
   - 材质看起来像塑料或蜡

2. **真实拍摄图特征**（如果出现以下特征，很可能是真实照片）：
   - 自然的光影变化
   - 真实的材质纹理（金属的光泽、宝石的折射）
   - 微小的瑕疵和不完美
   - 合理的景深和焦外
   - 自然的阴影

3. **其他线索**：
   - 如果有水印或logo（如Midjourney、Stable Diffusion等），肯定是AIGC
   - 如果边缘有不自然的融合痕迹，可能是AIGC

**输出格式（严格按照JSON）：**
```json
{
  "is_aicg": true/false,
  "confidence": "高/中/低",
  "reason": "<简短说明判断理由>"
}
```

请判断这张图片是否为AI生成。"""

    def detect_single_image(self, image_path: str, model: str = "gemini-3-pro-preview",
                           max_retries: int = 2) -> dict:
        """检测单张图片是否为AIGC"""
        # 编码图片
        image_b64 = self.encode_image(image_path)

        # 构建提示词
        prompt = self.build_detection_prompt()

        # 准备消息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ]

        # API请求
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.1
        }

        # 重试循环
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  📡 正在调用 {model} 检测... [尝试 {attempt}/{max_retries}]", end="")

                # 超时时间递增
                timeout = 60 + (attempt - 1) * 30

                response = requests.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=timeout
                )

                response.raise_for_status()
                result = response.json()

                # 提取内容
                content = result['choices'][0]['message']['content']

                # 解析JSON
                import re

                # 尝试提取JSON
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 尝试查找包含is_aicg的JSON对象
                    json_match = re.search(r'\{[^{}]*"is_aicg"[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        # 最后尝试：查找任何类似JSON的结构
                        json_match = re.search(r'\{.*?"is_aicg".*?\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                        else:
                            # 尝试查找部分JSON（处理响应被截断的情况）
                            is_aicg_match = re.search(r'"is_aicg"\s*:\s*(true|false)', content)
                            confidence_match = re.search(r'"confidence"\s*:\s*"([^"]+)"', content)
                            reason_match = re.search(r'"reason"\s*:\s*"([^"]+)"', content)

                            if is_aicg_match:
                                detection_result = {
                                    "is_aicg": is_aicg_match.group(1) == 'true',
                                    "confidence": confidence_match.group(1) if confidence_match else "中",
                                    "reason": reason_match.group(1) if reason_match else "从截断响应中提取"
                                }
                                print(f" -> {'AIGC' if detection_result['is_aicg'] else '真实'} ({detection_result['confidence']}) [部分解析]")
                                return detection_result
                            else:
                                raise ValueError(f"无法从响应中提取JSON: {content[:200]}")

                # 尝试修复常见的JSON格式问题
                json_str = json_str.strip()
                if not json_str.endswith('}'):
                    # 尝试找到最后一个完整的括号
                    last_brace = json_str.rfind('}')
                    if last_brace > 0:
                        json_str = json_str[:last_brace + 1]

                detection_result = json.loads(json_str)
                print(f" -> {'AIGC' if detection_result.get('is_aicg') else '真实'} ({detection_result.get('confidence', 'N/A')})")
                return detection_result

            except requests.exceptions.Timeout:
                print(f"\n  ⏱️  请求超时 (>{timeout}s)")
                if attempt < max_retries:
                    wait_time = 3 * attempt
                    print(f"  ⏳ {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    return {
                        "is_aicg": None,
                        "confidence": "未知",
                        "reason": "请求超时"
                    }
            except Exception as e:
                print(f"\n  ❌ 检测失败: {str(e)}")
                if attempt < max_retries:
                    wait_time = 3 * attempt
                    print(f"  ⏳ {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    return {
                        "is_aicg": None,
                        "confidence": "未知",
                        "reason": f"检测失败: {str(e)[:100]}"
                    }

        return {
            "is_aicg": None,
            "confidence": "未知",
            "reason": "未知错误"
        }

    def batch_detect_and_copy(self, input_dirs: list, output_file: str = None,
                             model: str = "gemini-3-pro-preview", auto_copy: bool = True):
        """批量检测AIGC图并自动复制"""
        print(f"\n{'='*80}")
        print(f"🤖 VLM批量检测AIGC图并自动处理")
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
        print(f"检测图片: {total}")
        print(f"自动复制: {'是' if auto_copy else '否'}")
        print(f"模型: {model}")
        print(f"{'='*80}\n")

        # 创建AICG目录
        aicg_dir = Path("data/aicg")
        if auto_copy:
            aicg_dir.mkdir(exist_ok=True)
            print(f"✅ AICG图片将复制到: {aicg_dir}\n")

        # 检测每张图片
        results = []
        aicg_count = 0
        real_count = 0
        failed_count = 0
        copied_count = 0

        for idx, image_path in enumerate(all_images, 1):
            print(f"[{idx}/{total}] 检测: {image_path.name}", end="")

            result = self.detect_single_image(str(image_path), model)
            result['filename'] = image_path.name
            result['path'] = str(image_path)

            if result['is_aicg'] is None:
                failed_count += 1
            elif result['is_aicg']:
                aicg_count += 1

                # 自动复制AICG图
                if auto_copy:
                    try:
                        # 添加aicg_前缀并复制
                        new_filename = f"aicg_{image_path.name}"
                        dst_path = aicg_dir / new_filename
                        shutil.copy2(str(image_path), str(dst_path))
                        copied_count += 1
                        print(f"           → 已复制到 aicg/ 作为 {new_filename}")
                    except Exception as e:
                        print(f"           ❌ 复制失败: {e}")
            else:
                real_count += 1

            results.append(result)

            # 短暂延迟，避免请求过快
            time.sleep(1)

        # 保存结果
        if output_file is None:
            output_file = f"data/aicg_vlm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "total_images": total,
            "aicg_count": aicg_count,
            "real_count": real_count,
            "failed_count": failed_count,
            "copied_count": copied_count,
            "aicg_rate": f"{aicg_count/total*100:.1f}%" if total > 0 else "0%",
            "results": results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 打印统计
        print(f"\n{'='*80}")
        print(f"📊 检测统计")
        print(f"{'='*80}")
        print(f"总数: {total}")
        print(f"🤖 AIGC图: {aicg_count} ({report['aicg_rate']})")
        print(f"✅ 真实图: {real_count} ({real_count/total*100:.1f}%)" if total > 0 else "")
        print(f"❌ 检测失败: {failed_count}")
        if auto_copy:
            print(f"📁 已复制: {copied_count} 张到 {aicg_dir}")
        print(f"\n✅ 报告已保存到: {output_file}")
        print(f"{'='*80}\n")

        return report


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='使用VLM检测AIGC图',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 检测项链类别
  python tools/vlm_aicg_detector.py \\
    --dirs data/项链 \\
    --copy

  # 检测多个类别
  python tools/vlm_aicg_detector.py \\
    --dirs data/戒指 data/项链 data/耳环 \\
    --copy
        """
    )

    parser.add_argument('--dirs', type=str, nargs='+', required=True,
                       help='要检测的目录列表')
    parser.add_argument('--output', type=str, help='输出报告文件路径')
    parser.add_argument('--model', type=str, default='gemini-3-pro-preview',
                       help='VLM模型')
    parser.add_argument('--copy', action='store_true', help='自动复制AICG图到aicg目录')

    args = parser.parse_args()

    # 从环境变量读取API key
    api_key = "sk-ttIhb1gjZtc6kn0amyc4zpgSuxW3SBubuppyPXRvkhVqt0gJ"

    detector = VLMAICGDetector(api_key=api_key)
    detector.batch_detect_and_copy(args.dirs, args.output, args.model, args.copy)
    return 0


if __name__ == "__main__":
    sys.exit(main())
