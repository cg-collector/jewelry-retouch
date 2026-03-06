#!/usr/bin/env python3
"""
使用VLM批量检测AIGC生成图并自动处理
- 检测AIGC图
- 复制到 aicg 目录
- 文件名添加 aicg_ 前缀
- 保留原图不删除
"""
import os
import sys
import json
import base64
import requests
import shutil
from pathlib import Path
from datetime import datetime
import urllib3
import ssl

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AICGVLMClassifier:
    """使用VLM检测AIGC图"""

    def __init__(self, api_key: str, base_url: str = "https://api.tu-zi.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def encode_image(self, image_path: str) -> str:
        """编码图片为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def build_aicg_prompt(self) -> str:
        """构建AIGC检测提示词"""
        return """请仔细观察这张珠宝图片，判断它是否为AI生成（AIGC）的图片。

**判断标准：**

1. **视觉质量指标**（AI生成图常见特征）：
   - 过度完美/平滑的纹理
   - 不自然的反光和光泽
   - 背景过度纯白/不真实
   - 细节过度一致（缺乏随机性）
   - 边缘过度锐利或模糊
   - 珠宝造型不自然/对称过度

2. **摄影真实感**（真实拍摄图特征）：
   - 自然的光影变化
   - 真实的材质纹理
   - 微小的瑕疵和不完美
   - 合理的景深和焦外
   - 自然的阴影

3. **AI生成的其他迹象**：
   - 水印或logo（如Midjourney、Stable Diffusion等）
   - 图像边缘有不自然的融合痕迹
   - 重复的模式或纹理
   - 闪烁或锯齿状的细节

**输出格式（严格按照JSON）：**
```json
{{
  "is_aicg": true/false,
  "confidence": "高/中/低",
  "reason": "<简短说明判断理由>"
}}
```

请判断这张图片是否为AI生成。"""

    def detect_single_image(self, image_path: str, model: str = "gemini-3-pro-preview", max_retries: int = 2) -> dict:
        """检测单张图片是否为AIGC"""
        # 编码图片
        image_b64 = self.encode_image(image_path)

        # 构建提示词
        prompt = self.build_aicg_prompt()

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
                response = requests.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                    verify=False  # 跳过SSL验证
                )

                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content']

                # 解析JSON
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_match = re.search(r'\{.*?"is_aicg".*?\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        raise ValueError(f"无法从响应中提取JSON")

                classification_result = json.loads(json_str)
                return classification_result

            except Exception as e:
                if attempt < max_retries:
                    continue
                else:
                    return {
                        "is_aicg": None,
                        "confidence": "未知",
                        "reason": f"检测失败: {str(e)}"
                    }

    def batch_detect_and_copy(self, input_dirs: list, output_file: str = None, model: str = "gemini-3-pro-preview",
                              sample_rate: int = 1, auto_copy: bool = True):
        """
        批量检测AIGC图并自动复制

        Args:
            input_dirs: 输入目录列表
            output_file: 输出报告文件路径
            model: VLM模型
            sample_rate: 采样率（1=全部检测，10=检测10%）
            auto_copy: 是否自动复制AICG图到aicg目录
        """
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

        # 采样
        if sample_rate > 1:
            sampled_images = all_images[::sample_rate]
            print(f"⚠️  采样模式: 检测 {len(sampled_images)}/{len(all_images)} 张 ({100//sample_rate}%)")
        else:
            sampled_images = all_images

        total = len(sampled_images)
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

        for idx, image_path in enumerate(sampled_images, 1):
            print(f"[{idx}/{total}] 检测: {image_path.name}...", end=" ")

            result = self.detect_single_image(str(image_path), model)
            result['filename'] = image_path.name
            result['path'] = str(image_path)

            if result['is_aicg'] is None:
                print(f"❌ 失败")
                failed_count += 1
            elif result['is_aicg']:
                print(f"🤖 AIGC ({result['confidence']})")
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
                print(f"✅ 真实 ({result['confidence']}) - {result.get('reason', '')[:30]}")
                real_count += 1

            results.append(result)

        # 保存结果
        if output_file is None:
            output_file = f"data/aicg_vlm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "sample_rate": sample_rate,
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

  # 检测项链类别（采样20%，快速测试）
  python tools/detect_aicg_vlm_auto.py \\
    --dirs data/项链 \\
    --sample 5 \\
    --copy

  # 检测所有分类（采样20%）
  python tools/detect_aicg_vlm_auto.py \\
    --dirs data/戒指 data/项链 data/耳环 data/手镯 data/手链 \\
    --sample 5 \\
    --copy

  # 全部检测（慢但准确）
  python tools/detect_aicg_vlm_auto.py \\
    --dirs data/项链 \\
    --sample 1 \\
    --copy
        """
    )

    parser.add_argument('--dirs', type=str, nargs='+', required=True,
                       help='要检测的目录列表')
    parser.add_argument('--output', type=str, help='输出报告文件路径')
    parser.add_argument('--model', type=str, default='gemini-3-pro-preview',
                       help='VLM模型')
    parser.add_argument('--sample', type=int, default=5,
                       help='采样率（默认5=检测20%%，1=全部检测）')
    parser.add_argument('--copy', action='store_true', help='自动复制AICG图到aicg目录')

    args = parser.parse_args()

    classifier = AICGVLMClassifier(api_key="sk-ttIhb1gjZtc6kn0amyc4zpgSuxW3SBubuppyPXRvkhVqt0gJ")
    classifier.batch_detect_and_copy(args.dirs, args.output, args.model, args.sample, args.copy)
    return 0


if __name__ == "__main__":
    sys.exit(main())
