#!/usr/bin/env python3
"""
简单VLM评估脚本
使用视觉模型评估生成图片与原图的一致性
"""
import os
import sys
import json
import base64
from pathlib import Path

# 添加项目根目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def encode_image_to_base64(image_path):
    """将图片编码为base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def create_evaluation_prompt(input_image_path, output_image_path):
    """创建评估提示词"""

    prompt = f"""# Jewelry Image Consistency Evaluation

You are an expert jewelry image quality evaluator. Compare the generated image with the original image and evaluate consistency.

## Images
- **Original Image**: Provided as image input
- **Generated Image**: Provided as image input

## Evaluation Dimensions (100 points total)

### 1. Detail Preservation (40 points)
Evaluate how well the generated image preserves original details:
- **Shape/Outline** (10pt): Is the pendant shape identical to original?
- **Texture/Metal** (10pt): Is metal texture/finish preserved?
- **Color** (10pt): Are metal and gemstone colors accurate?
- **Engravings/Patterns** (10pt): Are original engravings/patterns preserved?

### 2. Anti-Hallucination (40 points)
Check for elements NOT in original:
- **Chain Hallucination** (15pt): Were chain details added that weren't visible in original?
- **Decoration Hallucination** (15pt): Were decorations/gemstones added that weren't in original?
- **Material Change** (10pt): Was metal material type changed?

### 3. Angle Transformation (10 points)
- **Front-Facing View** (5pt): Is the pendant correctly facing forward?
- **Orientation** (5pt): Is the transformation natural?

### 4. Composition (5 points)
- **Pendant Ratio** (3pt): Does pendant occupy 60-70% of frame?
- **Close-up Effect** (2pt): Is it a proper close-up shot?

### 5. Background Quality (5 points)
- **Pure White** (3pt): Is background pure white (#FFFFFF)?
- **No Remnants** (2pt): Are there input background remnants?

## Scoring Guide
- **9-10**: Perfect/Excellent
- **7-8**: Good, minor acceptable differences
- **5-6**: Fair, noticeable issues
- **1-4**: Poor, major failures

## Required Output Format

Return ONLY a valid JSON object (no markdown, no explanation):

```json
{{
  "detail_preservation": {{
    "shape": 8,
    "texture": 9,
    "color": 8,
    "engravings": 7,
    "total": 32,
    "notes": "Minor texture difference"
  }},
  "anti_hallucination": {{
    "chain_hallucination": false,
    "decoration_hallucination": false,
    "material_change": false,
    "total": 40,
    "notes": "No hallucination"
  }},
  "angle_transformation": {{
    "front_facing": 5,
    "orientation": 4,
    "total": 9,
    "notes": "Proper front-facing view"
  }},
  "composition": {{
    "pendant_ratio": 3,
    "close_up_effect": 2,
    "total": 5,
    "notes": "Perfect composition"
  }},
  "background": {{
    "pure_white": 3,
    "no_remnants": 2,
    "total": 5,
    "notes": "Clean background"
  }},
  "total_score": 91,
  "overall_rating": "Excellent",
  "major_issues": []
}}
```

IMPORTANT: Return ONLY the JSON, no other text.
"""

    return prompt


def evaluate_with_openai_vision(original_image, generated_image, api_key=None):
    """
    使用OpenAI Vision API评估 (需要api_key)
    """
    try:
        import openai
    except ImportError:
        print("❌ openai package not installed. Install with: pip install openai")
        return None

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return None

    client = openai.OpenAI(api_key=api_key)

    prompt = create_evaluation_prompt(original_image, generated_image)

    try:
        # 读取图片
        with open(original_image, "rb") as f:
            original_base64 = base64.b64encode(f.read()).decode('utf-8')
        with open(generated_image, "rb") as f:
            generated_base64 = base64.b64encode(f.read()).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o",  # or gpt-4-vision-preview
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{original_base64}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{generated_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )

        # 解析JSON响应
        import re
        content = response.choices[0].message.content

        # 提取JSON (可能被markdown代码块包裹)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接找到JSON对象
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content

        return json.loads(json_str)

    except Exception as e:
        print(f"❌ Error calling OpenAI Vision API: {e}")
        return None


def manual_evaluation_guide(original_image, generated_image):
    """
    生成人工评估指南
    """
    guide = f"""
# 人工评估指南

## 图片对
- **原图**: {original_image}
- **生成图**: {generated_image}

## 评估维度 (请打分 1-10)

### 1. 细节保持 (40分)
- [ ] 形状轮廓 (1-10): ____
- [ ] 纹理质感 (1-10): ____
- [ ] 颜色准确性 (1-10): ____
- [ ] 刻字图案 (1-10): ____

小计: ____ / 40

### 2. 防幻觉 (40分)
- [ ] 链条幻觉? (是=-15, 否=15): ____
- [ ] 装饰幻觉? (是=-15, 否=15): ____
- [ ] 材质改变? (是=-10, 否=10): ____

小计: ____ / 40

### 3. 角度转换 (10分)
- [ ] 正面朝向 (1-5): ____
- [ ] 姿态自然 (1-5): ____

小计: ____ / 10

### 4. 构图 (5分)
- [ ] 吊坠占比60-70% (1-3): ____
- [ ] 特写效果 (1-2): ____

小计: ____ / 5

### 5. 背景 (5分)
- [ ] 纯白背景 (1-3): ____
- [ ] 无残留 (1-2): ____

小计: ____ / 5

## 总分
____ / 100

## 评级
- 90-100: ⭐⭐⭐⭐⭐ Excellent
- 80-89:  ⭐⭐⭐⭐ Good
- 70-79:  ⭐⭐⭐ Fair
- <70:     ⭐⭐ Poor

## 备注
(记录发现的问题)


"""

    return guide


def main():
    import argparse

    parser = argparse.ArgumentParser(description='VLM一致性评估')
    parser.add_argument('--original', type=str, help='原始图片路径')
    parser.add_argument('--generated', type=str, help='生成图片路径')
    parser.add_argument('--batch_dir', type=str, help='批量评估目录')
    parser.add_argument('--api_key', type=str, help='OpenAI API Key')
    parser.add_argument('--output', type=str, help='输出评估结果JSON')
    parser.add_argument('--manual', action='store_true', help='生成人工评估指南')

    args = parser.parse_args()

    if args.manual:
        # 生成人工评估指南
        if args.original and args.generated:
            guide = manual_evaluation_guide(args.original, args.generated)
            print(guide)

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(guide)
                print(f"\n✓ 评估指南已保存到: {args.output}")
        else:
            print("❌ 请提供 --original 和 --generated 参数")
    elif args.original and args.generated:
        # 单对评估
        print(f"\n{'='*70}")
        print(f"VLM Consistency Evaluation")
        print(f"{'='*70}")
        print(f"Original:  {args.original}")
        print(f"Generated: {args.generated}")
        print(f"{'='*70}\n")

        result = evaluate_with_openai_vision(
            args.original,
            args.generated,
            args.api_key
        )

        if result:
            print(f"\n✓ 评估完成")
            print(f"\n总分: {result.get('total_score', 'N/A')}/100")
            print(f"评级: {result.get('overall_rating', 'N/A')}")
            print(f"\n详细结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"\n✓ 结果已保存到: {args.output}")
        else:
            print("\n❌ VLM评估失败，请使用 --manual 生成人工评估指南")

    elif args.batch_dir:
        # 批量评估
        print(f"\n批量评估模式: {args.batch_dir}")
        print("⚠️  此功能需要OpenAI API Key")
        print("请使用 --manual 模式进行人工评估\n")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
