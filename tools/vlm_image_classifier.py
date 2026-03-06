#!/usr/bin/env python3
"""
VLM珠宝图像分类工具
使用视觉语言模型识别珠宝类型并自动分类到对应目录
"""
import os
import sys
import json
import base64
import requests
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class VLMImageClassifier:
    """使用VLM进行珠宝图像分类"""

    # 珠宝类别定义
    CATEGORIES = {
        "戒指": "戒指",
        "项链": "项链",
        "耳环": "耳环",
        "手镯": "手镯",
        "手链": "手链"
    }

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

    def build_classification_prompt(self) -> str:
        """构建分类提示词"""
        categories_str = "、".join(self.CATEGORIES.keys())

        prompt = f"""你是一个专业的珠宝识别专家。请仔细观察这张珠宝图片，识别它属于哪一类珠宝。

**珠宝类型（必须从中选择一个）：**
- {categories_str}

**识别要点：**
1. **戒指**：戴在手指上的环形饰品，通常尺寸较小
2. **项链**：戴在脖子上的饰品，有链条和吊坠
3. **耳环**：戴在耳朵上的饰品，通常成对出现
4. **手环/手镯**：戴在手腕上的硬质环形饰品，不可弯曲
5. **手链**：戴在手腕上的软质饰品，由链条、珠子等组成，可弯曲

**重要提示：**
- 如果图片中展示的是多件珠宝（如耳环一对），识别主要类型
- 只返回最准确的类别名称
- 如果难以确定，选择最可能的那一个

**输出格式（严格按照JSON格式）：**
```json
{{
  "category": "<类别名称>",
  "confidence": "<高/中/低>",
  "reason": "<简短说明判断理由>"
}}
```

现在请识别这张珠宝图片。"""

        return prompt

    def classify_image(self, image_path: str, model: str = "gemini-3-pro-preview", max_retries: int = 3) -> Optional[Dict]:
        """
        对单张图片进行分类

        Args:
            image_path: 图片路径
            model: 使用的模型
            max_retries: 最大重试次数

        Returns:
            分类结果字典，格式: {"category": str, "confidence": str, "reason": str}
        """
        # 编码图片
        image_b64 = self.encode_image(image_path)

        # 构建提示词
        prompt = self.build_classification_prompt()

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
            "max_tokens": 500,
            "temperature": 0.1  # 低温度确保稳定输出
        }

        # 重试循环
        for attempt in range(1, max_retries + 1):
            try:
                print(f"  📡 正在调用 {model} 分类... [尝试 {attempt}/{max_retries}]", end="")

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
                    # 尝试查找完整的JSON对象（包括换行）
                    json_match = re.search(r'\{[^{}]*"category"[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        # 最后尝试：查找任何类似JSON的结构
                        json_match = re.search(r'\{.*?"category".*?\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                        else:
                            # 直接查找类别名称
                            category_match = re.search(r'["\']?category["\']?\s*[:：]\s*["\']?([^"\'\n,]+)["\']?', content)
                            if category_match:
                                category = category_match.group(1).strip()
                                return {
                                    "category": category,
                                    "confidence": "中",
                                    "reason": "从非结构化响应中提取"
                                }
                            raise ValueError(f"无法从响应中提取JSON: {content[:200]}")

                # 尝试修复常见的JSON格式问题
                json_str = json_str.strip()
                if not json_str.endswith('}'):
                    # 尝试找到最后一个完整的括号
                    last_brace = json_str.rfind('}')
                    if last_brace > 0:
                        json_str = json_str[:last_brace + 1]

                classification_result = json.loads(json_str)

                # 验证类别
                category = classification_result.get("category", "")
                normalized_category = self.normalize_category(category)

                classification_result["category"] = normalized_category
                classification_result["raw_category"] = category

                print(f" -> {normalized_category} ({classification_result.get('confidence', 'N/A')})")
                return classification_result

            except requests.exceptions.Timeout:
                print(f"\n  ⏱️  请求超时 (>{timeout}s)")
                if attempt < max_retries:
                    import time
                    wait_time = 3 * attempt
                    print(f"  ⏳ {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"  ❌ 超时重试{max_retries}次后仍失败")
                    return None

            except requests.exceptions.ConnectionError as e:
                print(f"\n  🔌 连接错误: {str(e)[:100]}")
                if attempt < max_retries:
                    import time
                    time.sleep(3 * attempt)
                else:
                    return None

            except requests.exceptions.HTTPError as e:
                print(f"\n  ❌ HTTP错误: {e.response.status_code}")
                print(f"  响应: {e.response.text[:200]}")
                return None

            except Exception as e:
                print(f"\n  ❌ 分类失败: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(2)
                else:
                    return None

        return None

    def normalize_category(self, category: str) -> str:
        """标准化类别名称"""
        # 去除空格
        category = category.strip()

        # 特殊映射：手镯直接返回
        if "手镯" in category or category == "手镯":
            return "手镯"

        # 直接匹配
        if category in self.CATEGORIES.values():
            return category

        # 通过映射查找
        if category in self.CATEGORIES:
            return self.CATEGORIES[category]

        # 模糊匹配
        for key, value in self.CATEGORIES.items():
            if key in category or category in key:
                return value

        # 无法识别，返回"未分类"
        return "未分类"

    def batch_classify(
        self,
        input_dir: str,
        output_base: str = "data",
        model: str = "gemini-3-pro-preview",
        limit: Optional[int] = None,
        copy_mode: bool = True,
        dry_run: bool = False
    ):
        """
        批量分类目录中的所有图片

        Args:
            input_dir: 输入图片目录
            output_base: 输出基础目录（默认：数据/）
            model: 使用的模型
            limit: 限制处理的图片数量（用于测试）
            copy_mode: True=复制文件，False=移动文件
            dry_run: True=模拟运行，不实际操作文件
        """
        input_path = Path(input_dir)

        if not input_path.exists():
            print(f"❌ 错误: 输入目录不存在 - {input_dir}")
            return

        # 获取所有图片文件
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(list(input_path.glob(ext)))

        if not image_files:
            print(f"❌ 错误: 在 {input_dir} 中未找到图片文件")
            return

        # 排序
        image_files.sort()

        # 限制数量
        if limit:
            image_files = image_files[:limit]

        total = len(image_files)
        print(f"\n{'='*80}")
        print(f"🔍 VLM珠宝图像批量分类")
        print(f"{'='*80}")
        print(f"输入目录: {input_dir}")
        print(f"图片数量: {total}")
        print(f"输出目录: {output_base}")
        print(f"模型: {model}")
        print(f"模式: {'复制' if copy_mode else '移动'}")
        if dry_run:
            print(f"⚠️  模拟运行模式（不会实际操作文件）")
        print(f"{'='*80}\n")

        # 创建输出目录
        output_base_path = Path(output_base)
        category_dirs = {}
        for category in self.CATEGORIES.values():
            category_dir = output_base_path / category
            if not dry_run:
                category_dir.mkdir(parents=True, exist_ok=True)
            category_dirs[category] = category_dir

        # 未分类目录
        uncategorized_dir = output_base_path / "未分类"
        if not dry_run:
            uncategorized_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        stats = {category: 0 for category in self.CATEGORIES.values()}
        stats["未分类"] = 0
        failed = 0

        # 分类日志
        classification_log = []

        # 逐个分类
        for idx, image_file in enumerate(image_files, 1):
            print(f"\n[{idx}/{total}] 处理: {image_file.name}")

            # 调用分类API
            result = self.classify_image(str(image_file), model)

            if result:
                category = result["category"]
                confidence = result.get("confidence", "N/A")
                reason = result.get("reason", "")

                print(f"  识别为: {category}")
                print(f"  置信度: {confidence}")
                print(f"  理由: {reason}")

                # 确定目标目录
                if category in category_dirs:
                    target_dir = category_dirs[category]
                else:
                    target_dir = uncategorized_dir
                    category = "未分类"

                # 目标文件路径
                target_file = target_dir / image_file.name

                # 复制/移动文件
                if not dry_run:
                    try:
                        if copy_mode:
                            shutil.copy2(image_file, target_file)
                        else:
                            shutil.move(str(image_file), target_file)
                        print(f"  ✅ 已{'复制' if copy_mode else '移动'}到: {target_dir}")
                    except Exception as e:
                        print(f"  ❌ 操作失败: {e}")
                        failed += 1
                        continue
                else:
                    print(f"  📋 将{'复制' if copy_mode else '移动'}到: {target_dir}")

                # 更新统计
                stats[category] += 1

                # 记录日志
                classification_log.append({
                    "image": str(image_file),
                    "category": category,
                    "confidence": confidence,
                    "reason": reason,
                    "target": str(target_file)
                })

            else:
                print(f"  ❌ 分类失败")
                failed += 1
                classification_log.append({
                    "image": str(image_file),
                    "category": "失败",
                    "error": "API调用失败"
                })

        # 保存分类日志
        if not dry_run:
            log_file = output_base_path / f"classification_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "model": model,
                    "total_images": total,
                    "successful": total - failed,
                    "failed": failed,
                    "statistics": stats,
                    "classifications": classification_log
                }, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 分类日志已保存到: {log_file}")

        # 打印统计信息
        print(f"\n{'='*80}")
        print(f"📊 分类统计")
        print(f"{'='*80}")
        for category, count in stats.items():
            if count > 0:
                print(f"{category}: {count}")
        print(f"失败: {failed}")
        print(f"总计: {total}")
        print(f"{'='*80}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='VLM珠宝图像分类工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 测试单张图片
  python tools/vlm_image_classifier.py \\
    --image data/all/jewelry_2025-12-26_29855.jpg \\
    --test

  # 批量分类（测试模式，只处理前10张）
  python tools/vlm_image_classifier.py \\
    --batch data/all \\
    --limit 10 \\
    --dry-run

  # 批量分类（正式运行，复制模式）
  python tools/vlm_image_classifier.py \\
    --batch data/all \\
    --copy \\
    --output data

  # 批量分类（移动模式）
  python tools/vlm_image_classifier.py \\
    --batch data/all \\
    --move \\
    --output data
        """
    )

    # 单图测试参数
    parser.add_argument('--image', type=str, help='单张图片路径（测试模式）')
    parser.add_argument('--test', action='store_true', help='测试单张图片')

    # 批量分类参数
    parser.add_argument('--batch', type=str, help='输入目录路径（批量模式）')
    parser.add_argument('--output', type=str, default='data', help='输出基础目录（默认：data/）')
    parser.add_argument('--limit', type=int, help='限制处理的图片数量（用于测试）')
    parser.add_argument('--copy', action='store_true', help='复制模式（默认）')
    parser.add_argument('--move', action='store_true', help='移动模式')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际操作文件')

    # 通用参数
    parser.add_argument('--model', type=str, default='gemini-3-pro-preview',
                       help='使用的VLM模型（默认: gemini-3-pro-preview）')
    parser.add_argument('--api-key', type=str,
                       default="sk-ttIhb1gjZtc6kn0amyc4zpgSuxW3SBubuppyPXRvkhVqt0gJ",
                       help='API密钥')

    args = parser.parse_args()

    # 创建分类器
    classifier = VLMImageClassifier(api_key=args.api_key)

    # 单图测试模式
    if args.image and args.test:
        if not Path(args.image).exists():
            print(f"❌ 错误: 图片不存在 - {args.image}")
            return 1

        print(f"\n{'='*80}")
        print(f"🔍 VLM单图分类测试")
        print(f"{'='*80}")
        print(f"图片: {args.image}")
        print(f"模型: {args.model}")
        print(f"{'='*80}\n")

        result = classifier.classify_image(args.image, args.model)

        if result:
            print(f"\n✅ 分类结果:")
            print(f"   类别: {result['category']}")
            print(f"   置信度: {result.get('confidence', 'N/A')}")
            print(f"   理由: {result.get('reason', 'N/A')}")
            if result.get('raw_category') != result['category']:
                print(f"   原始识别: {result.get('raw_category')}")
        else:
            print(f"\n❌ 分类失败")

        return 0 if result else 1

    # 批量分类模式
    if args.batch:
        copy_mode = not args.move

        classifier.batch_classify(
            input_dir=args.batch,
            output_base=args.output,
            model=args.model,
            limit=args.limit,
            copy_mode=copy_mode,
            dry_run=args.dry_run
        )
        return 0

    # 未指定模式
    parser.print_help()
    print("\n❌ 错误: 请使用 --test --image（单图测试）或 --batch（批量分类）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
