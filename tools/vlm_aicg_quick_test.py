#!/usr/bin/env python3
"""
VLM AIGC快速采样检测 - 只检测前N张图片
"""
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


def encode_image(image_path: str, max_size: int = 768) -> str:
    """编码图片为base64，压缩到指定尺寸"""
    img = Image.open(image_path)
    if img.size[0] > max_size or img.size[1] > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def detect_aicg(image_path: str, api_key: str, model: str = "gemini-3-pro-preview") -> dict:
    """检测单张图片"""
    image_b64 = encode_image(image_path)

    prompt = """请判断这张珠宝图片是否为AI生成（AIGC）。

判断标准：
- AIGC特征：过度完美/平滑、不自然反光、背景过度纯白、细节过度一致
- 真实特征：自然光影、真实纹理、微小瑕疵、合理景深

返回JSON: {"is_aicg": true/false, "confidence": "高/中/低", "reason": "简短理由"}"""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        "max_tokens": 200,
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    endpoint = "https://api.tu-zi.com/v1/chat/completions"

    for attempt in range(2):
        try:
            print(f"    [尝试 {attempt+1}/2]", end=" ", flush=True)
            response = requests.post(endpoint, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']

            # 解析JSON
            import re

            # 查找is_aicg字段
            is_aicg_match = re.search(r'"is_aicg"\s*:\s*(true|false)', content, re.IGNORECASE)
            confidence_match = re.search(r'"confidence"\s*:\s*"([^"]+)"', content, re.IGNORECASE)
            reason_match = re.search(r'"reason"\s*:\s*"([^"]+)"', content, re.IGNORECASE)

            if is_aicg_match:
                detection_result = {
                    "is_aicg": is_aicg_match.group(1).lower() == 'true',
                    "confidence": confidence_match.group(1) if confidence_match else "中",
                    "reason": reason_match.group(1) if reason_match else ""
                }
                status = "🤖 AIGC" if detection_result['is_aicg'] else "✅ 真实"
                print(f"→ {status} ({detection_result['confidence']})")
                return detection_result

            raise ValueError(f"无法解析JSON: {content[:100]}")

        except Exception as e:
            print(f"❌ {str(e)[:50]}")
            if attempt < 1:
                time.sleep(3)

    return {"is_aicg": None, "confidence": "未知", "reason": "检测失败"}


def main():
    # 配置
    api_key = "sk-ttIhb1gjZtc6kn0amyc4zpgSuxW3SBubuppyPXRvkhVqt0gJ"
    input_dir = Path("data/项链")
    aicg_dir = Path("data/aicg")
    aicg_dir.mkdir(exist_ok=True)

    # 只检测前10张图片
    images = sorted(list(input_dir.glob("*.jpg")))[:10]

    print(f"\n{'='*80}")
    print(f"🔍 VLM AIGC快速采样检测（前{len(images)}张）")
    print(f"{'='*80}\n")

    results = []
    aicg_count = 0
    real_count = 0
    failed_count = 0
    copied_count = 0

    for idx, image_path in enumerate(images, 1):
        print(f"[{idx}/{len(images)}] {image_path.name}")

        result = detect_aicg(str(image_path), api_key)
        result['filename'] = image_path.name

        if result['is_aicg'] is None:
            failed_count += 1
        elif result['is_aicg']:
            aicg_count += 1
            # 复制图片
            try:
                new_name = f"aicg_{image_path.name}"
                shutil.copy2(image_path, aicg_dir / new_name)
                copied_count += 1
                print(f"         ✅ 已复制到 aicg/")
            except Exception as e:
                print(f"         ❌ 复制失败: {e}")
        else:
            real_count += 1

        results.append(result)
        time.sleep(1)  # 延迟避免请求过快

    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "sample_size": len(images),
        "aicg_count": aicg_count,
        "real_count": real_count,
        "failed_count": failed_count,
        "copied_count": copied_count,
        "aicg_rate": f"{aicg_count/(len(images)-failed_count)*100:.1f}%" if len(images) > failed_count else "0%",
        "results": results
    }

    report_file = f"data/aicg_quick_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"📊 采样检测结果")
    print(f"{'='*80}")
    print(f"采样数: {len(images)}")
    print(f"🤖 AIGC: {aicg_count} ({report['aicg_rate']})")
    print(f"✅ 真实: {real_count}")
    print(f"❌ 失败: {failed_count}")
    print(f"📁 已复制: {copied_count}")
    print(f"\n报告: {report_file}")
    print(f"{'='*80}\n")

    # 推测全量结果
    total_images = len(list(input_dir.glob("*.jpg")))
    if real_count > 0:
        estimated_aicg = int(total_images * aicg_count / (aicg_count + real_count))
        print(f"📈 推测：项链类别共{total_images}张，预计约{estimated_aicg}张为AIGC")
    print()


if __name__ == "__main__":
    main()
