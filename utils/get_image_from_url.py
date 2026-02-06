#!/usr/bin/env python3
"""
download_ghost_images.py

从导出的JSONL文件中下载 generated_image_url 和 original_image_url 到不同的文件夹。
"""

import os
import json
import argparse
import requests
import time
import sys
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
    return path

def download_image(url, save_path, retry=3, timeout=30):
    """
    下载单个图片
    """
    if not url or not url.startswith('http'):
        print(f"  ⚠️  无效URL: {url}")
        return False, "无效URL"
    
    for attempt in range(retry):
        try:
            response = requests.get(
                url, 
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            response.raise_for_status()
            
            # 保存图片
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(save_path) / 1024  # KB
            return True, f"下载成功 ({file_size:.1f} KB)"
            
        except requests.exceptions.RequestException as e:
            if attempt < retry - 1:
                time.sleep(1)  # 等待后重试
                continue
            return False, f"请求失败: {str(e)}"
        except Exception as e:
            return False, f"保存失败: {str(e)}"
    
    return False, "未知错误"

def get_filename_from_url(url, record_id, image_type):
    """
    从URL生成文件名
    """
    # 从URL提取原始文件名
    parsed = urlparse(url)
    path = parsed.path
    
    # 获取文件扩展名
    if '.' in path:
        ext = path.split('.')[-1].split('?')[0]  # 处理可能的查询参数
        ext = ext[:10]  # 限制扩展名长度
    else:
        ext = "jpg"
    
    # 清理扩展名，只保留字母数字
    ext = ''.join(c for c in ext if c.isalnum()).lower()
    if not ext:
        ext = "jpg"
    
    # 生成文件名: record_id_类型.扩展名
    filename = f"{record_id}_{image_type}.{ext}"
    return filename

def process_jsonl_file(jsonl_path, generated_dir, original_dir, max_workers=5, limit=None):
    """
    处理JSONL文件，下载所有图片
    """
    if not os.path.exists(jsonl_path):
        print(f"❌ 文件不存在: {jsonl_path}")
        return
    
    # 读取JSONL文件
    print(f"📖 读取文件: {jsonl_path}")
    items = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"  ⚠️  JSON解析错误: {e}")
    
    print(f"📊 找到 {len(items)} 条记录")
    
    if limit and limit > 0:
        items = items[:limit]
        print(f"🔧 限制处理前 {limit} 条记录")
    
    # 准备下载任务
    tasks = []
    for i, item in enumerate(items):
        record_id = item.get('record_id', f'unknown_{i}')
        
        # Generated image URL
        gen_url = item.get('generated_image_url')
        if gen_url:
            filename = get_filename_from_url(gen_url, record_id, 'generated')
            save_path = os.path.join(generated_dir, filename)
            tasks.append({
                'url': gen_url,
                'save_path': save_path,
                'record_id': record_id,
                'type': 'generated',
                'index': i
            })
        
        # Original image URL
        orig_url = item.get('original_image_url')
        if orig_url:
            filename = get_filename_from_url(orig_url, record_id, 'original')
            save_path = os.path.join(original_dir, filename)
            tasks.append({
                'url': orig_url,
                'save_path': save_path,
                'record_id': record_id,
                'type': 'original',
                'index': i
            })
    
    print(f"🚀 准备下载 {len(tasks)} 个图片")
    
    # 使用线程池并行下载
    downloaded = 0
    failed = 0
    skipped = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(
                download_image, 
                task['url'], 
                task['save_path']
            ): task for task in tasks
        }
        
        # 处理结果
        for i, future in enumerate(as_completed(future_to_task), 1):
            task = future_to_task[future]
            success, message = future.result()
            
            if success:
                downloaded += 1
                status = "✅"
            else:
                failed += 1
                status = "❌"
            
            print(f"  [{i}/{len(tasks)}] {status} {task['type']} - {task['record_id']}: {message}")
    
    # 统计结果
    skipped = len(tasks) - downloaded - failed
    
    print("\n" + "="*50)
    print("📊 下载完成统计:")
    print(f"  成功: {downloaded}")
    print(f"  失败: {failed}")
    print(f"  跳过: {skipped}")
    print(f"  生成图片目录: {generated_dir}")
    print(f"  原始图片目录: {original_dir}")
    print("="*50)
    
    # 生成下载报告
    report_path = os.path.join(os.path.dirname(jsonl_path), f"download_report_{int(time.time())}.json")
    report = {
        'jsonl_file': jsonl_path,
        'generated_dir': generated_dir,
        'original_dir': original_dir,
        'total_records': len(items),
        'total_tasks': len(tasks),
        'downloaded': downloaded,
        'failed': failed,
        'skipped': skipped,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📝 报告已保存: {report_path}")
    
    return downloaded, failed, skipped

def main():
    parser = argparse.ArgumentParser(
        description='下载JSONL文件中的图片到不同的文件夹'
    )
    
    parser.add_argument(
        '--jsonl',
        required=True,
        help='JSONL文件路径（从export_ghost_jewelry.py导出的文件）'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./downloaded_images',
        help='输出根目录（默认: ./downloaded_images）'
    )
    
    parser.add_argument(
        '--generated-dir',
        default=None,
        help='生成图片目录名（默认: {output-dir}/generated）'
    )
    
    parser.add_argument(
        '--original-dir',
        default=None,
        help='原始图片目录名（默认: {output-dir}/original）'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=5,
        help='并发下载线程数（默认: 5）'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制处理前N条记录（默认: 处理全部）'
    )
    
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='不生成下载报告'
    )
    
    args = parser.parse_args()
    
    # 设置目录路径
    output_root = args.output_dir
    generated_dir = args.generated_dir or os.path.join(output_root, 'generated')
    original_dir = args.original_dir or os.path.join(output_root, 'original')
    
    # 确保目录存在
    ensure_dir(generated_dir)
    ensure_dir(original_dir)
    
    print("="*50)
    print("🖼️  图片下载工具")
    print("="*50)
    print(f"JSONL文件: {args.jsonl}")
    print(f"生成图片目录: {generated_dir}")
    print(f"原始图片目录: {original_dir}")
    print(f"并发线程: {args.max_workers}")
    print(f"记录限制: {args.limit or '无限制'}")
    print("="*50)
    
    # 开始下载
    try:
        process_jsonl_file(
            jsonl_path=args.jsonl,
            generated_dir=generated_dir,
            original_dir=original_dir,
            max_workers=args.max_workers,
            limit=args.limit
        )
    except KeyboardInterrupt:
        print("\n⚠️  用户中断下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 下载过程中出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()