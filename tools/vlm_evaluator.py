#!/usr/bin/env python3
"""
VLM一致性评估工具 v3.1 - 聚焦纹理和装饰（支持批量评估）
重点评估：纹理质感、装饰花纹的一致性（光影变化可接受）

新增功能：
1. 批量评估整个结果文件夹
2. 自动从 results.json 读取生成时使用的提示词
3. 评估结果保存在生成图像文件夹内的 evaluation/ 目录
4. 默认使用 gemini-3-pro-preview 模型
"""
import os
import sys
import json
import base64
import requests
from pathlib import Path
from datetime import datetime


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

    def load_results_json(self, result_dir):
        """加载结果目录中的 results.json 或 test_results.json"""
        result_dir = Path(result_dir)

        json_files = [
            result_dir / "results.json",
            result_dir / "test_results.json"
        ]

        for json_file in json_files:
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

        print(f"⚠️  未找到结果文件（尝试了 results.json 和 test_results.json）")
        return []

    def find_original_image(self, image_name, result_dir):
        """查找原图文件"""
        search_dirs = [
            Path("数据/项链"),
            Path("数据/耳环"),
            Path("数据/手链"),
            Path("数据/手环"),
            Path("数据/戒指"),
            Path("数据"),
            Path(result_dir).parent.parent.parent / "数据" / "项链",
            Path(result_dir).parent.parent.parent / "数据" / "耳环",
            Path(result_dir).parent.parent.parent / "数据" / "手链",
            Path(result_dir).parent.parent.parent / "数据" / "手环",
            Path(result_dir).parent.parent.parent / "数据" / "戒指",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            full_path = search_dir / image_name
            if full_path.exists():
                return str(full_path)

            try:
                matching = list(search_dir.glob(image_name.split('.')[0] + '.*'))
                if matching:
                    return str(matching[0])
            except:
                continue

        return None

    def load_prompt_used(self, result_dir, results_data=None):
        """
        获取生成图像时使用的提示词
        优先级：results.json中的prompt_content > prompt_used.txt > prompt.txt > current.txt
        """
        result_dir = Path(result_dir)

        # 1. 优先从 results.json 中读取 prompt_content
        if results_data and isinstance(results_data, list) and len(results_data) > 0:
            first_result = results_data[0]
            if "prompt_content" in first_result and first_result["prompt_content"]:
                return first_result["prompt_content"]

        # 2. 尝试读取 prompt_used.txt
        prompt_used_txt = result_dir / "prompt_used.txt"
        if prompt_used_txt.exists():
            with open(prompt_used_txt, 'r', encoding='utf-8') as f:
                return f.read().strip()

        # 3. 尝试从元数据文件读取
        metadata_files = [
            result_dir / "metadata.json",
            result_dir / "generation_info.json",
        ]

        for metadata_file in metadata_files:
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'prompt' in data:
                            return data['prompt']
                except:
                    continue

        # 4. 尝试读取 prompt.txt
        prompt_txt = result_dir / "prompt.txt"
        if prompt_txt.exists():
            with open(prompt_txt, 'r', encoding='utf-8') as f:
                return f.read().strip()

        # 5. 尝试读取 current.txt
        current_prompt = Path("prompts/current.txt")
        if current_prompt.exists():
            with open(current_prompt, 'r', encoding='utf-8') as f:
                return f.read().strip()

        # 6. 使用默认提示词
        return "保持产品的纹理质感和装饰花纹的一致性，转换为专业电商产品摄影风格"

    def batch_evaluate(self, result_dir, model="gemini-3-pro-preview", limit=None):
        """批量评估结果目录中的所有成功生成的图像"""

        result_dir = Path(result_dir)

        # 加载结果JSON
        results = self.load_results_json(result_dir)
        if not results:
            print(f"❌ 未找到可评估的结果")
            return

        # 加载使用的提示词
        prompt_used = self.load_prompt_used(result_dir, results_data=results)
        print(f"📋 使用的提示词:\n{prompt_used[:200]}...\n")

        # 筛选成功的结果
        success_results = [r for r in results if r.get("status") == "success"]

        if limit:
            success_results = success_results[:limit]

        total = len(success_results)
        print(f"📊 找到 {total} 张成功生成的图像")

        # 创建评估结果目录（保存在生成图像文件夹内）
        eval_dir = result_dir / "evaluation"
        eval_dir.mkdir(exist_ok=True)

        # 评估每张图片
        evaluation_summary = []

        for idx, result in enumerate(success_results, 1):
            print(f"\n{'='*80}")
            print(f"[{idx}/{total}] 正在评估...")
            print(f"{'='*80}")

            # 获取图片路径
            generated_image = result.get("output")
            if not generated_image or not os.path.exists(generated_image):
                print(f"⚠️  跳过：生成图不存在 - {generated_image}")
                continue

            # 获取原图 - 优先使用 input 字段（完整路径），其次使用 image 字段（文件名）
            original_image = None
            image_field = result.get("image", "")  # 用于记录

            # 1. 优先使用 input 字段（完整路径）
            input_path = result.get("input")
            if input_path and os.path.exists(input_path):
                original_image = input_path
            # 2. 其次尝试 image 字段（可能是完整路径）
            elif image_field and os.path.exists(image_field):
                original_image = image_field
            # 3. 如果只有文件名，则搜索
            elif image_field:
                original_image = self.find_original_image(image_field, result_dir)

            if not original_image:
                print(f"⚠️  跳过：找不到原图")
                continue

            print(f"原图: {original_image}")
            print(f"生成: {generated_image}")

            # 执行评估
            eval_result, raw_content = self.evaluate(
                original_image,
                generated_image,
                prompt_used,
                model
            )

            if eval_result:
                # 打印简要结果
                overview = eval_result['evaluation_overview']
                print(f"\n✅ 评估完成:")
                print(f"   一致性得分: {overview['consistency_score']}/100")
                print(f"   业务需求得分: {overview['business_score']}/100")
                print(f"   总体得分: {overview['overall_score']}/100")
                print(f"   {'✅ 可用' if overview['is_usable'] else '❌ 不可用'}: {overview['primary_reason']}")

                # 保存单个评估结果到 evaluation 文件夹
                generated_name = Path(generated_image).stem
                eval_json_path = eval_dir / f"{generated_name}_evaluation.json"
                eval_raw_path = eval_dir / f"{generated_name}_raw.txt"

                with open(eval_json_path, 'w', encoding='utf-8') as f:
                    json.dump(eval_result, f, indent=2, ensure_ascii=False)

                if raw_content:
                    with open(eval_raw_path, 'w', encoding='utf-8') as f:
                        f.write(raw_content)

                print(f"   评估结果已保存到: {eval_json_path}")

                # 添加到汇总
                evaluation_summary.append({
                    "image": image_field,
                    "generated": generated_image,
                    "evaluation": eval_result
                })
            else:
                print(f"❌ 评估失败")
                if raw_content:
                    print(f"原始响应: {raw_content[:500]}")

        # 保存汇总报告
        if evaluation_summary:
            summary_path = eval_dir / "evaluation_summary.json"

            # 计算统计数据
            total_evaluated = len(evaluation_summary)
            usable_count = sum(1 for e in evaluation_summary if e['evaluation']['evaluation_overview']['is_usable'])

            avg_consistency = sum(e['evaluation']['evaluation_overview']['consistency_score'] for e in evaluation_summary) / total_evaluated
            avg_business = sum(e['evaluation']['evaluation_overview']['business_score'] for e in evaluation_summary) / total_evaluated
            avg_overall = sum(e['evaluation']['evaluation_overview']['overall_score'] for e in evaluation_summary) / total_evaluated

            summary_report = {
                "generated_at": datetime.now().isoformat(),
                "result_dir": str(result_dir),
                "prompt_used": prompt_used,
                "model": model,
                "statistics": {
                    "total_evaluated": total_evaluated,
                    "usable_count": usable_count,
                    "usable_rate": f"{usable_count/total_evaluated*100:.1f}%",
                    "avg_consistency_score": f"{avg_consistency:.1f}",
                    "avg_business_score": f"{avg_business:.1f}",
                    "avg_overall_score": f"{avg_overall:.1f}"
                },
                "evaluations": evaluation_summary
            }

            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_report, f, indent=2, ensure_ascii=False)

            print(f"\n{'='*80}")
            print(f"📊 批量评估完成！")
            print(f"{'='*80}")
            print(f"评估总数: {total_evaluated}")
            print(f"可用数量: {usable_count} ({usable_count/total_evaluated*100:.1f}%)")
            print(f"平均一致性得分: {avg_consistency:.1f}/100")
            print(f"平均业务需求得分: {avg_business:.1f}/100")
            print(f"平均总体得分: {avg_overall:.1f}/100")
            print(f"\n✅ 汇总报告已保存到: {summary_path}")
            print(f"✅ 所有评估结果已保存在: {eval_dir}")

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

    def evaluate(self, original_image, generated_image, business_requirement, model="gemini-3-pro-image-preview-2k-vip", max_retries=5):
        """执行评估 - 带重试机制"""

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

        # 重试循环
        for attempt in range(1, max_retries + 1):
            try:
                print(f"📡 正在调用 {model} 评估（聚焦纹理和装饰）...", end="")
                if attempt > 1:
                    print(f" [重试 {attempt}/{max_retries}]", end="")
                print()
                print(f"   原图: {original_image}")
                print(f"   生成: {generated_image}")

                # 增加超时时间：每次重试递增
                timeout = 180 + (attempt - 1) * 60  # 180s, 240s, 300s...

                response = requests.post(
                    self.endpoint,
                    headers=headers,
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
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        raise ValueError(f"无法从响应中提取JSON")

                evaluation_result = json.loads(json_str)

                return evaluation_result, content

            except requests.exceptions.Timeout as e:
                wait_time = 5 * attempt  # 指数退避：5s, 10s, 15s...
                print(f"⏱️  请求超时 (>{timeout}s)，{wait_time}秒后重试...")
                if attempt < max_retries:
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"❌ 超时重试{max_retries}次后仍失败")
                    return None, None

            except requests.exceptions.ConnectionError as e:
                wait_time = 5 * attempt
                error_msg = str(e)
                if 'proxy' in error_msg.lower() or 'connection reset' in error_msg.lower():
                    print(f"🔌 代理/连接错误: {error_msg[:100]}")
                elif 'ssl' in error_msg.lower() or 'eof' in error_msg.lower():
                    print(f"🔒 SSL/TLS错误: {error_msg[:100]}")
                else:
                    print(f"🔌 连接错误: {error_msg[:100]}")

                print(f"   {wait_time}秒后重试...")
                if attempt < max_retries:
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"❌ 连接重试{max_retries}次后仍失败")
                    return None, None

            except requests.exceptions.HTTPError as e:
                # HTTP错误不重试（4xx客户端错误，5xx服务器错误）
                print(f"❌ HTTP错误: {e.response.status_code}")
                print(f"   响应: {e.response.text[:200]}")
                return None, None

            except requests.exceptions.RequestException as e:
                wait_time = 5 * attempt
                print(f"❌ 请求异常: {type(e).__name__}: {str(e)[:100]}")
                print(f"   {wait_time}秒后重试...")
                if attempt < max_retries:
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"❌ 重试{max_retries}次后仍失败")
                    return None, None

            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"响应内容: {content[:1000]}")
                # JSON解析错误不重试
                return None, content

            except Exception as e:
                print(f"❌ 评估失败: {e}")
                # 其他异常不重试
                return None, None

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

    parser = argparse.ArgumentParser(
        description='VLM一致性评估 v3.1 - 聚焦纹理和装饰（支持批量评估）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 单图评估
  python tools/vlm_consistency_evaluator_v3.py \\
    --original 数据/项链/image_1.jpeg \\
    --generated check/necklace_frontal_20250302/01.png

  # 批量评估整个结果文件夹
  python tools/vlm_consistency_evaluator_v3.py \\
    --batch check/necklace_frontal_20250302

  # 批量评估（限制数量，用于测试）
  python tools/vlm_consistency_evaluator_v3.py \\
    --batch check/necklace_frontal_20250302 \\
    --limit 3
        """
    )

    # 单图评估参数
    parser.add_argument('--original', type=str, help='原始图片路径（单图模式）')
    parser.add_argument('--generated', type=str, help='生成图片路径（单图模式）')
    parser.add_argument('--business', type=str,
                       default='保持纹理质感和装饰花纹的一致性',
                       help='业务需求描述（单图模式）')
    parser.add_argument('--output', type=str, help='输出评估结果JSON路径（单图模式）')

    # 批量评估参数
    parser.add_argument('--batch', type=str, help='结果目录路径（批量模式）')
    parser.add_argument('--limit', type=int, help='限制评估的图片数量（批量模式，用于测试）')

    # 通用参数
    parser.add_argument('--model', type=str, default='gemini-3-pro-preview',
                       help='使用的VLM模型（默认: gemini-3-pro-preview）')
    parser.add_argument('--api-key', type=str,
                       default="sk-ttIhb1gjZtc6kn0amyc4zpgSuxW3SBubuppyPXRvkhVqt0gJ",
                       help='API密钥')

    args = parser.parse_args()

    # 创建评估器
    evaluator = GeminiConsistencyEvaluatorV3(api_key=args.api_key)

    # 批量评估模式
    if args.batch:
        if not Path(args.batch).exists():
            print(f"❌ 错误: 结果目录不存在 - {args.batch}")
            return 1

        print(f"\n{'='*80}")
        print(f"🔍 VLM批量一致性评估 v3.1（聚焦纹理和装饰）")
        print(f"{'='*80}")
        print(f"结果目录: {args.batch}")
        print(f"模型: {args.model}")
        if args.limit:
            print(f"限制数量: {args.limit}")
        print(f"{'='*80}\n")

        evaluator.batch_evaluate(
            result_dir=args.batch,
            model=args.model,
            limit=args.limit
        )
        return 0

    # 单图评估模式
    if not args.original or not args.generated:
        print("❌ 错误: 请指定 --original 和 --generated（单图模式），或使用 --batch（批量模式）")
        print("使用 --help 查看帮助")
        return 1

    # 执行单图评估
    print(f"\n{'='*80}")
    print(f"🔍 VLM一致性评估 v3.1（聚焦纹理和装饰）")
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
