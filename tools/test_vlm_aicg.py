#!/usr/bin/env python3
"""
VLM检测AIGC测试版 - 添加延迟和详细输出
"""
import sys
import base64
import json
import requests
import urllib3
import shutil
import time
from pathlib import Path
from datetime import datetime

urllib3.disable_warnings()

# 配置
api_key = "sk-ttIhb1gjZtc6kn0amyc4zpgSuxW3SBubuppyPXRvkhVqt0gJ"
endpoint = "https://api.tu-zi.com/v1/chat/completions"
model = "gemini-3-pro-preview"

def detect_aicg(image_path: str) -> dict:
    """检测单张图片"""

    # 编码图片
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode('utf-8')

    # 构建请求
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """请仔细观察这张珠宝图片，判断它是否为AI生成（AIGC）的图片。

**判断标准：**
1. AIGC特征：过度完美/平滑、不自然反光、背景过度纯白、细节过度一致、边缘过度锐利或模糊、珠宝造型不自然
2. 真实拍摄：自然光影、真实纹理、微小瑕疵、合理景深、自然阴影

**请严格按照以下JSON格式输出：**
{"is_aicg": true/false, "confidence": "高/中/低", "reason": "简短理由"}"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300,
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 重试机制
    for attempt in range(3):
        try:
            print(f"    尝试 {attempt + 1}/3...", end=" ", flush=True)
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60, verify=False)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']

            print(f"✅ 响应成功")
            print(f"    原始响应: {content[:200]}...")

            # 解析JSON
            import re

            # 方式1: ```json ... ```
            match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if match:
                json_str = match.group(1)
                parsed = json.loads(json_str)
                return parsed

            # 方式2: { ... "is_aicg" ... }
            match = re.search(r'\{[^{}]*"is_aicg"[^{}]*\}', content, re.DOTALL)
            if match:
                json_str = match.group(0)
                parsed = json.loads(json_str)
                return parsed

            # 方式3: 查找最后一个完整的JSON对象
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
            if match:
                try:
                    json_str = match.group(0)
                    parsed = json.loads(json_str)
                    if 'is_aicg' in parsed:
                        return parsed
                except:
                    pass

            print(f"    ❌ 无法解析JSON")
            return {
                "is_aicg": None,
                "confidence": "未知",
                "reason": "无法解析响应"
            }

        except Exception as e:
            print(f"❌ 失败: {str(e)[:60]}")
            if attempt < 2:
                print(f"    等待5秒后重试...")
                time.sleep(5)
            else:
                return {
                    "is_aicg": None,
                    "confidence": "未知",
                    "reason": f"API错误: {str(e)[:50]}"
                }

def main():
    input_dir = Path("data/项链")
    aicg_dir = Path("data/aicg")
    aicg_dir.mkdir(exist_ok=True)

    # 获取所有图片
    images = sorted(list(input_dir.glob("*.jpg")))
    print(f"🔍 检测 {len(images)} 张项链图片\n")

    results = []
    aicg_count = 0
    real_count = 0
    failed_count = 0
    copied_count = 0

    for idx, image_path in enumerate(images, 1):
        print(f"[{idx}/{len(images)}] {image_path.name}")

        result = detect_aicg(str(image_path))
        result['filename'] = image_path.name

        if result['is_aicg'] is None:
            print(f"    ❓ 无法判断\n")
            failed_count += 1
        elif result['is_aicg']:
            print(f"    🤖 AIGC ({result.get('confidence', 'N/A')}) - {result.get('reason', '')[:50]}\n")
            aicg_count += 1

            # 复制图片
            try:
                new_name = f"aicg_{image_path.name}"
                shutil.copy2(image_path, aicg_dir / new_name)
                copied_count += 1
                print(f"    ✅ 已复制到 aicg/ 作为 {new_name}\n")
            except Exception as e:
                print(f"    ❌ 复制失败: {e}\n")
        else:
            print(f"    ✅ 真实 ({result.get('confidence', 'N/A')}) - {result.get('reason', '')[:60]}\n")
            real_count += 1

        results.append(result)

        # 延迟，避免请求过快
        time.sleep(2)

    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "total_images": len(images),
        "aicg_count": aicg_count,
        "real_count": real_count,
        "failed_count": failed_count,
        "copied_count": copied_count,
        "aicg_rate": f"{aicg_count/len(images)*100:.1f}%" if len(images) > 0 else "0%",
        "results": results
    }

    report_file = f"data/aicg_vlm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"📊 检测完成")
    print(f"{'='*80}")
    print(f"总数: {len(images)}")
    print(f"🤖 AIGC: {aicg_count} ({report['aicg_rate']})")
    print(f"✅ 真实: {real_count} ({real_count/len(images)*100:.1f}%)")
    print(f"❓ 失败: {failed_count}")
    print(f"📁 已复制: {copied_count} 张到 {aicg_dir}")
    print(f"\n✅ 报告已保存: {report_file}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
