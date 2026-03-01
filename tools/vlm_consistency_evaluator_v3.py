#!/usr/bin/env python3
"""
VLM一致性评估工具 v3.0 - 聚焦纹理和装饰
重点评估：纹理质感、装饰花纹的一致性（光影变化可接受）
"""
import os
import sys
import json
import base64
import requests
from pathlib import Path


class GeminiConsistencyEvaluatorV3:
    """使用Gemini进行一致性评估 - 聚焦纹理和装饰"""

    def __init__(self, api_key, base_url="https://api.tu-zi.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/v1/chat/completions"

    def encode_image(self, image_path):
        """编码图片为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def build_evaluation_prompt(self, business_requirement):
        """构建评估提示词 - 聚焦纹理和装饰"""

        prompt = f"""# 珠宝图像一致性评估任务（聚焦纹理和装饰）

你是一个专业的珠宝图像质量评估专家。请仔细对比原始图片和生成图片，**重点评估纹理质感和装饰花纹的一致性**。

## 📋 业务需求
{business_requirement}

## 🎯 评估原则（重要）

**一致性 > 业务需求**，但重点关注：

1. **纹理质感**（最关键）：金属的抛光/拉丝/磨砂等质感必须一致
2. **装饰花纹**：雕刻、镶嵌、花纹图案必须完全一致
3. **形状轮廓**：整体形状必须一致
4. **颜色**：金属和宝石颜色必须准确
5. **光影可变**：⚠️ 光影和反射可以改变（因为要转换为摄影棚布光）

## 📊 评估维度

### 一、纹理质感一致性（40分）⭐⭐⭐⭐⭐

这是**最关键**的评估维度，请仔细观察：

1. **金属表面处理** (20分):
   - 抛光效果：是高光抛光还是哑光？必须一致
   - 拉丝/磨砂：如果有拉丝或磨砂效果，必须保留
   - 纹理方向：金属的纹理方向是否一致

2. **材质特征** (20分):
   - 是否有锤纹、车纹、雕刻等特殊工艺
   - 这些特殊纹理是否保留
   - 材质感是否改变（如从实心变空心）

**扣分标准**:
- 抛光变哑光/拉丝：-15分
- 哑光变抛光：-15分
- 纹理方向错误：-10分
- 特殊工艺丢失：-10分
- 轻微差异（光影导致）：-3分

### 二、装饰花纹一致性（40分）⭐⭐⭐⭐⭐

这是**第二关键**的评估维度：

1. **雕刻/刻字** (20分):
   - 文字/数字内容：是否完全一致
   - 图案内容：是否完全一致
   - 位置和比例：是否保持一致

2. **镶嵌工艺** (10分):
   - 宝石镶嵌位置：是否一致
   - 爪镶/包镶等工艺：是否保留
   - 镶嵌数量：是否一致

3. **装饰细节** (10分):
   - 花纹、珠边、镂空等装饰：是否保留
   - 细节复杂度：是否简化或丢失

**扣分标准**:
- 刻字内容错误：-20分（严重）
- 刻字丢失：-15分
- 图案内容改变：-15分
- 宝石位置改变：-8分
- 镶嵌工艺改变：-5分
- 装饰细节丢失：-5分

### 三、形状与轮廓（10分）

- 整体形状是否一致
- 轮廓线条是否保持
- 比例是否协调

### 四、颜色准确性（5分）

- 金属颜色（金/银/玫瑰金等）
- 宝石颜色（如果有）

### 五、防幻觉检查（5分）一票否决

- 是否添加了原图不存在的装饰
- 是否添加了原图不存在的宝石
- 是否改变了产品类型（如手链变项链）

## ✅ 可接受的变化

以下变化是**允许的**，不扣分：

1. **光影和反射**: 因为要从自然光转换为摄影棚光
   - 高光位置改变 ✅
   - 反射内容改变 ✅
   - 阴影淡化或消除 ✅

2. **链条长度**: 如果只展示部分链条
   - 链条延伸出画面 ✅
   - 扣头不在画面内 ✅

3. **背景**: 背景完全改变
   - 从有背景到纯白 ✅

## ❌ 不可接受的变化（一票否决）

出现以下情况直接判为"不可用"：

1. 纹理质感根本性改变（抛光↔哑光/拉丝）
2. 装饰图案内容改变或丢失
3. 刻字内容错误或丢失
4. 添加原图不存在的装饰/宝石
5. 产品类型改变（手链变项链等）

## 📤 输出格式（JSON）

请按照以下格式输出，**所有评分都是你根据具体情况自主决定的**：

```json
{{
  "evaluation_overview": {{
    "consistency_score": <0-100分>,
    "business_score": <0-100分>,
    "overall_score": <0-100分>,
    "is_usable": true/false,
    "primary_reason": "<一句话总结>"
  }},

  "texture_analysis": {{
    "score": <0-100>,
    "metal_finish": {{
      "original": "<原图: 抛光/哑光/拉丝等>",
      "generated": "<生成图: 抛光/哑光/拉丝等>",
      "consistent": true/false,
      "description": "<描述对比结果>"
    }},
    "surface_texture": {{
      "original": "<原图表面纹理>",
      "generated": "<生成图表面纹理>",
      "consistent": true/false,
      "description": "<描述对比结果>"
    }},
    "texture_issues": [
      "<如果有问题，列出具体问题>"
    ]
  }},

  "decoration_analysis": {{
    "score": <0-100>,
    "engravings": {{
      "content_preserved": true/false,
      "description": "<刻字/文字是否保留>"
    }},
    "patterns": {{
      "content_preserved": true/false,
      "description": "<图案内容是否保留>"
    }},
    "gemstones": {{
      "position_consistent": true/false,
      "description": "<宝石镶嵌位置是否一致>"
    }},
    "decoration_details": {{
      "preserved": true/false,
      "description": "<装饰细节是否保留>"
    }},
    "decoration_issues": [
      "<如果有问题，列出具体问题>"
    ]
  }},

  "shape_analysis": {{
    "score": <0-100>,
    "description": "<形状是否一致>",
    "issues": []
  }},

  "color_analysis": {{
    "score": <0-100>,
    "description": "<颜色是否准确>",
    "issues": []
  }},

  "hallucination_check": {{
    "has_hallucination": true/false,
    "added_decorations": "<是否添加装饰>",
    "added_gemstones": "<是否添加宝石>",
    "product_type_changed": "<产品类型是否改变>",
    "critical_issues": [
      "<严重问题列表>"
    ]
  }},

  "business_analysis": {{
    "angle_achievement": <0-100>,
    "composition_quality": <0-100>,
    "background_quality": <0-100>,
    "description": "<业务需求完成情况>"
  }},

  "conclusion": {{
    "rating": "<PERFECT/EXCELLENT/GOOD/FAIR/POOR>",
    "summary": "<详细总结>",
    "can_use_production": true/false,
    "recommendation": "<具体建议>"
  }}
}}
```

## ⚠️ 评估重点提示

1. **纹理质感是第一位的**：即使光影改变，纹理质感必须一致
2. **装饰花纹不可改变**：刻字、图案必须完全保留
3. **光影变化可接受**：不要因为光影改变而扣分
4. **诚实评估**：纹理或装饰有问题，即使其他方面做得好，也要给出低分

现在请仔细观察两张图片，重点对比**纹理质感和装饰花纹**，进行专业评估。
"""

        return prompt

    def evaluate(self, original_image, generated_image, business_requirement, model="gemini-3-pro-image-preview-2k-vip"):
        """执行评估"""

        # 编码图片
        original_b64 = self.encode_image(original_image)
        generated_b64 = self.encode_image(generated_image)

        # 构建提示词
        prompt = self.build_evaluation_prompt(business_requirement)

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
                            "url": f"data:image/jpeg;base64,{original_b64}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{generated_b64}"
                        }
                    }
                ]
            }
        ]

        # API请求
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 3000,
            "temperature": 0.3
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            print(f"📡 正在调用 {model} 评估（聚焦纹理和装饰）...")
            print(f"   原图: {original_image}")
            print(f"   生成: {generated_image}")

            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=180
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
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError(f"无法从响应中提取JSON")

            evaluation_result = json.loads(json_str)

            return evaluation_result, content

        except requests.exceptions.RequestException as e:
            print(f"❌ API请求失败: {e}")
            return None, None
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"响应内容: {content[:1000]}")
            return None, content
        except Exception as e:
            print(f"❌ 评估失败: {e}")
            return None, None


def print_evaluation_result(result):
    """打印评估结果"""
    if not result:
        return

    print(f"\n{'='*80}")
    print(f"📊 评估结果（聚焦纹理和装饰）")
    print(f"{'='*80}\n")

    # 总览
    overview = result['evaluation_overview']
    print(f"🎯 总览")
    print(f"   一致性得分: {overview['consistency_score']}/100")
    print(f"   业务需求得分: {overview['business_score']}/100")
    print(f"   总体得分: {overview['overall_score']}/100")
    print(f"   {'✅ 可用' if overview['is_usable'] else '❌ 不可用'}")
    print(f"   结论: {overview['primary_reason']}")

    # 纹理分析（重点）
    print(f"\n{'='*80}")
    print(f"🔍 纹理质感分析（重点）")
    print(f"{'='*80}\n")

    ta = result['texture_analysis']
    print(f"纹理质感到分: {ta['score']}/100")

    metal = ta['metal_finish']
    print(f"\n金属表面处理:")
    print(f"   原图: {metal['original']}")
    print(f"   生成: {metal['generated']}")
    print(f"   一致性: {'✅ 是' if metal['consistent'] else '❌ 否'}")
    print(f"   说明: {metal['description']}")

    surface = ta['surface_texture']
    print(f"\n表面纹理:")
    print(f"   原图: {surface['original']}")
    print(f"   生成: {surface['generated']}")
    print(f"   一致性: {'✅ 是' if surface['consistent'] else '❌ 否'}")
    print(f"   说明: {surface['description']}")

    if ta['texture_issues']:
        print(f"\n纹理问题:")
        for issue in ta['texture_issues']:
            print(f"   ⚠️  {issue}")

    # 装饰分析（重点）
    print(f"\n{'='*80}")
    print(f"🔍 装饰花纹分析（重点）")
    print(f"{'='*80}\n")

    da = result['decoration_analysis']
    print(f"装饰花纹得分: {da['score']}/100")

    print(f"\n刻字/文字:")
    print(f"   保留: {'✅ 是' if da['engravings']['content_preserved'] else '❌ 否'}")
    print(f"   说明: {da['engravings']['description']}")

    print(f"\n图案:")
    print(f"   保留: {'✅ 是' if da['patterns']['content_preserved'] else '❌ 否'}")
    print(f"   说明: {da['patterns']['description']}")

    print(f"\n宝石镶嵌:")
    print(f"   位置一致: {'✅ 是' if da['gemstones']['position_consistent'] else '❌ 否'}")
    print(f"   说明: {da['gemstones']['description']}")

    print(f"\n装饰细节:")
    print(f"   保留: {'✅ 是' if da['decoration_details']['preserved'] else '❌ 否'}")
    print(f"   说明: {da['decoration_details']['description']}")

    if da['decoration_issues']:
        print(f"\n装饰问题:")
        for issue in da['decoration_issues']:
            print(f"   ⚠️  {issue}")

    # 幻觉检测
    hc = result['hallucination_check']
    if hc['has_hallucination']:
        print(f"\n{'='*80}")
        print(f"⚠️  幻觉检测")
        print(f"{'='*80}")
        if hc.get('added_decorations'):
            print(f"   添加装饰: {hc['added_decorations']}")
        if hc.get('added_gemstones'):
            print(f"   添加宝石: {hc['added_gemstones']}")
        if hc.get('product_type_changed'):
            print(f"   产品类型改变: {hc['product_type_changed']}")
        if hc['critical_issues']:
            print(f"   严重问题:")
            for issue in hc['critical_issues']:
                print(f"      - {issue}")

    # 结论
    print(f"\n{'='*80}")
    print(f"📝 最终结论")
    print(f"{'='*80}\n")

    conclusion = result['conclusion']
    print(f"评级: {conclusion['rating']}")
    print(f"总结: {conclusion['summary']}")
    print(f"生产可用: {'✅ 是' if conclusion['can_use_production'] else '❌ 否'}")
    print(f"建议: {conclusion['recommendation']}")
    print(f"\n{'='*80}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='VLM一致性评估 v3.0 - 聚焦纹理和装饰')
    parser.add_argument('--original', type=str, required=True, help='原始图片路径')
    parser.add_argument('--generated', type=str, required=True, help='生成图片路径')
    parser.add_argument('--business', type=str,
                       default='保持纹理质感和装饰花纹的一致性',
                       help='业务需求描述')
    parser.add_argument('--output', type=str, help='输出评估结果JSON路径')
    parser.add_argument('--model', type=str, default='gemini-3-pro-image-preview-2k-vip',
                       help='使用的模型')

    args = parser.parse_args()

    # 创建评估器
    api_key = "sk-ttIhb1gjZtc6kn0amyc4zpgSuxW3SBubuppyPXRvkhVqt0gJ"
    evaluator = GeminiConsistencyEvaluatorV3(api_key=api_key)

    # 执行评估
    print(f"\n{'='*80}")
    print(f"🔍 VLM一致性评估 v3.0（聚焦纹理和装饰）")
    print(f"{'='*80}")
    print(f"📋 业务需求: {args.business}")
    print(f"🤖 模型: {args.model}")
    print(f"{'='*80}\n")

    result, raw_content = evaluator.evaluate(
        args.original,
        args.generated,
        args.business,
        args.model
    )

    if result:
        # 打印结果
        print_evaluation_result(result)

        # 保存结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"✅ 评估结果已保存到: {args.output}")

    else:
        print(f"\n❌ 评估失败")
        if raw_content:
            print(f"原始响应:\n{raw_content[:2000]}")


if __name__ == "__main__":
    main()
