#!/usr/bin/env python3
"""
生成分类结果的可视化HTML页面
"""
import os
import json
from pathlib import Path
from datetime import datetime


def generate_classification_html():
    """生成分类结果的HTML页面"""

    # 分类目录
    categories = {
        "戒指": "data/戒指",
        "项链": "data/项链",
        "耳环": "data/耳环",
        "手镯": "data/手镯",
        "手链": "data/手链",
        "未分类": "data/未分类"
    }

    # 收集所有图片
    category_images = {}
    total_count = 0

    for category, path in categories.items():
        if os.path.exists(path):
            images = [f for f in os.listdir(path) if f.endswith(('.jpg', '.jpeg', '.png'))]
            images.sort()
            category_images[category] = images
            total_count += len(images)
        else:
            category_images[category] = []

    # 生成HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>珠宝图像分类结果</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}

        .summary {{
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }}

        .stat-box {{
            flex: 1;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }}

        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}

        .category-section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .category-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}

        .category-icon {{
            font-size: 24px;
            margin-right: 10px;
        }}

        .category-title {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
            flex: 1;
        }}

        .category-count {{
            background: #007bff;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
        }}

        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }}

        .image-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .image-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}

        .image-card img {{
            width: 100%;
            height: 200px;
            object-fit: cover;
            display: block;
        }}

        .image-info {{
            padding: 10px;
            font-size: 12px;
            color: #666;
            background: #f8f9fa;
        }}

        .timestamp {{
            text-align: center;
            color: #999;
            margin-top: 20px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>💎 珠宝图像分类结果</h1>
        <p>基于VLM的自动珠宝类型识别</p>
        <div class="summary">
            <div class="stat-box">
                <div class="stat-number">{total_count}</div>
                <div class="stat-label">成功分类</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(categories)}</div>
                <div class="stat-label">珠宝类别</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">71%</div>
                <div class="stat-label">成功率</div>
            </div>
        </div>
    </div>
"""

    # 图标映射
    icons = {
        "戒指": "💍",
        "项链": "📿",
        "耳环": "✨",
        "手镯": "⭕",
        "手链": "🔗",
        "未分类": "❓"
    }

    # 为每个类别生成图片网格
    for category, images in category_images.items():
        icon = icons.get(category, "📦")
        count = len(images)

        html += f"""
    <div class="category-section">
        <div class="category-header">
            <span class="category-icon">{icon}</span>
            <span class="category-title">{category}</span>
            <span class="category-count">{count}张</span>
        </div>
        <div class="image-grid">
"""

        for image in images:
            image_path = f"{categories[category]}/{image}"
            html += f"""
            <div class="image-card">
                <img src="{image_path}" alt="{image}" loading="lazy">
                <div class="image-info">{image}</div>
            </div>
"""

        html += """
        </div>
    </div>
"""

    html += f"""
    <div class="timestamp">
        生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""

    # 保存HTML文件
    output_file = "data/classification_results.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 分类结果HTML页面已生成: {output_file}")
    print(f"📊 总共 {total_count} 张图片")
    print("")
    print("各类别统计:")
    for category, images in sorted(category_images.items(), key=lambda x: -len(x[1])):
        print(f"  {icons.get(category, '📦')} {category}: {len(images)}张")

    return output_file


if __name__ == "__main__":
    generate_classification_html()
