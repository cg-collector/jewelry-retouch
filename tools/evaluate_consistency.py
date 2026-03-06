#!/usr/bin/env python3
"""
VLM一致性评估工具
使用视觉大模型评估生成图片与原图的一致性
"""
import os
import sys
import json
import base64
from pathlib import Path
from PIL import Image
import io
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from api_client import APIClient


class ConsistencyEvaluator:
    """一致性评估器"""

    def __init__(self):
        self.config = Config()
        self.config.validate()
        self.client = APIClient(self.config.base_url, self.config.api_key)

    def encode_image(self, image_path: str) -> str:
        """编码图片为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def evaluate_single_pair(
        self,
        input_image: str,
        output_image: str,
        model: str = "gemini-3-pro-image-preview-2k-vip"
    ) -> Dict:
        """
        评估单对图片的一致性

        Args:
            input_image: 原始图片路径
            output_image: 生成图片路径
            model: 使用的VLM模型

        Returns:
            评估结果字典
        """

        # 构建评估提示词
        prompt = self._build_evaluation_prompt()

        # 编码图片
        input_b64 = self.encode_image(input_image)
        output_b64 = self.encode_image(output_image)

        # 准备payload (使用多模态模型格式)
        # 注意：这里需要根据实际API调整格式
        # 假设支持vision API

        # 由于当前API主要是image-to-image，我们用文本描述的方式
        # 或者需要使用vision-capable模型

        # 这里先返回一个结构化的评估框架
        # 实际VLM调用需要根据具体API调整

        return {
            "input_image": input_image,
            "output_image": output_image,
            "evaluation_pending": True,
            "note": "VLM API integration needed - requires vision-capable model"
        }

    def _build_evaluation_prompt(self) -> str:
        """构建评估提示词"""
        return """# Jewelry Image Consistency Evaluation Task

## Input
- Original image: [INPUT_IMAGE]
- Generated image: [OUTPUT_IMAGE]

## Evaluation Dimensions (Total 100 points)

### 1. Detail Preservation (40 points)
Compare the pendant in original vs generated:
- Shape outline consistency (10 points)
- Texture/metal finish consistency (10 points)
- Color accuracy (10 points)
- Engravings/patterns preservation (10 points)

Scoring: 1-10 for each sub-dimension

### 2. Anti-Hallucination (40 points)
Check generated image for:
- Chain details not in original (15 points)
- Decorations not in original (15 points)
- Material changes (10 points)

Scoring: Deduct points for each hallucination found

### 3. Angle Transformation (10 points)
- Correct front-facing view? (5 points)
- Pendant facing forward? (5 points)

Scoring: 1-5 for each

### 4. Composition (5 points)
- Pendant occupies 60-70% of frame? (3 points)
- Close-up effect achieved? (2 points)

Scoring: 1-3 and 1-2

### 5. Background Quality (5 points)
- Pure white background? (3 points)
- No input background remnants? (2 points)

Scoring: 1-3 and 1-2

## Output Format (JSON)

Please output in this exact format:

```json
{
  "detail_preservation": {
    "shape": 8,
    "texture": 9,
    "color": 8,
    "engravings": 7,
    "total": 32,
    "notes": "Minor texture differences"
  },
  "anti_hallucination": {
    "chain_hallucination": false,
    "decoration_hallucination": false,
    "material_change": false,
    "total": 40,
    "notes": "No hallucination detected"
  },
  "angle_transformation": {
    "front_facing": 5,
    "pendant_facing": 4,
    "total": 9,
    "notes": "Slightly off-center"
  },
  "composition": {
    "pendant_ratio": 3,
    "close_up_effect": 2,
    "total": 5,
    "notes": "Perfect composition"
  },
  "background": {
    "pure_white": 3,
    "no_remnants": 2,
    "total": 5,
    "notes": "Clean background"
  },
  "total_score": 91,
  "overall_rating": "Excellent",
  "major_issues": []
}
```

## Evaluation Guidelines

- Score 9-10: Perfect match
- Score 7-8: Minor differences, acceptable
- Score 5-6: Noticeable differences, needs improvement
- Score 1-4: Major issues, failed

Please analyze both images carefully and provide detailed scoring.
"""

    def batch_evaluate(
        self,
        test_dir: str,
        input_base_dir: str = "数据/项链",
        model: str = "gemini-3-pro-image-preview-2k-vip"
    ) -> List[Dict]:
        """
        批量评估测试结果

        Args:
            test_dir: 测试输出目录
            input_base_dir: 原始图片基础目录
            model: VLM模型

        Returns:
            评估结果列表
        """
        results = []

        # 扫描测试目录
        test_path = Path(test_dir)
        if not test_path.exists():
            print(f"Test directory not found: {test_dir}")
            return results

        # 查找所有生成图片
        output_images = list(test_path.glob("**/*.png"))
        output_images += list(test_path.glob("**/*.jpg"))

        print(f"Found {len(output_images)} output images")

        for output_img in output_images:
            # 根据文件名找到对应的输入图片
            # 假设文件名包含原始图片信息
            # 这里需要根据实际的命名规则调整

            # 暂时跳过，等待具体命名规则
            pass

        return results


def manual_evaluation_template():
    """
    人工评估模板
    当VLM不可用时使用
    """
    return {
        "image_pair": "image_1",
        "detail_preservation": {
            "shape": None,  # 1-10
            "texture": None,  # 1-10
            "color": None,  # 1-10
            "engravings": None,  # 1-10
            "total": None,
            "notes": ""
        },
        "anti_hallucination": {
            "chain_hallucination": None,  # True/False
            "decoration_hallucination": None,  # True/False
            "material_change": None,  # True/False
            "total": None,
            "notes": ""
        },
        "angle_transformation": {
            "front_facing": None,  # 1-5
            "pendant_facing": None,  # 1-5
            "total": None,
            "notes": ""
        },
        "composition": {
            "pendant_ratio": None,  # 1-3
            "close_up_effect": None,  # 1-2
            "total": None,
            "notes": ""
        },
        "background": {
            "pure_white": None,  # 1-3
            "no_remnants": None,  # 1-2
            "total": None,
            "notes": ""
        },
        "total_score": None,
        "overall_rating": None,  # Excellent/Good/Fair/Poor
        "major_issues": []
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='评估生成图片的一致性')
    parser.add_argument('--input', type=str, required=True, help='原始图片路径')
    parser.add_argument('--output', type=str, required=True, help='生成图片路径')
    parser.add_argument('--model', type=str, default='gemini-3-pro-image-preview-2k-vip',
                       help='VLM模型')
    parser.add_argument('--batch', type=str, help='批量评估目录')

    args = parser.parse_args()

    evaluator = ConsistencyEvaluator()

    if args.batch:
        # 批量评估
        results = evaluator.batch_evaluate(args.batch)
        print(f"\n{'='*70}")
        print(f"Batch Evaluation Results")
        print(f"{'='*70}")
        for result in results:
            print(f"\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        # 单对评估
        result = evaluator.evaluate_single_pair(
            args.input,
            args.output,
            args.model
        )

        print(f"\n{'='*70}")
        print(f"Consistency Evaluation Result")
        print(f"{'='*70}")
        print(f"\nInput:  {args.input}")
        print(f"Output: {args.output}")
        print(f"\n{json.dumps(result, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
