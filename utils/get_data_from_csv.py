import pandas as pd
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from urllib.parse import urlparse
import argparse

def download_image(url, save_path, max_retries=3):
    """
    下载单个图像
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # 从URL获取文件扩展名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            # 如果没有扩展名，尝试从Content-Type推断
            if not filename or '.' not in filename:
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # 默认
                
                # 使用id或时间戳作为文件名
                filename = f"image_{int(time.time()*1000)}_{attempt}{ext}"
            
            # 确保文件名安全
            safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-').rstrip()
            
            # 完整保存路径
            full_path = os.path.join(save_path, safe_filename)
            
            # 保存文件
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ 下载成功: {safe_filename}")
            return True, safe_filename
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 尝试 {attempt+1}/{max_retries} 失败: {url} - {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # 等待后重试
            continue
    
    return False, None

def download_images_from_csv(csv_path, output_dir, max_workers=5):
    """
    从CSV文件中下载所有图像
    """
    # 读取CSV文件
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ 读取CSV文件成功，共 {len(df)} 行")
    except Exception as e:
        print(f"✗ 读取CSV文件失败: {e}")
        return
    
    # 检查url列是否存在
    if 'url' not in df.columns:
        print("✗ CSV文件中没有'url'列")
        print("可用列:", df.columns.tolist())
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备URL列表
    urls = df['url'].dropna().unique().tolist()
    print(f"✓ 找到 {len(urls)} 个唯一URL")
    
    # 使用多线程下载
    successful = 0
    failed = 0
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有下载任务
        future_to_url = {
            executor.submit(download_image, url, output_dir): url 
            for url in urls
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                success, filename = future.result()
                if success:
                    successful += 1
                    results.append({
                        'url': url,
                        'filename': filename,
                        'status': 'success'
                    })
                else:
                    failed += 1
                    results.append({
                        'url': url,
                        'filename': None,
                        'status': 'failed'
                    })
            except Exception as e:
                failed += 1
                results.append({
                    'url': url,
                    'filename': None,
                    'status': 'error',
                    'error': str(e)
                })
                print(f"✗ 下载异常: {url} - {e}")
    
    # 保存下载结果报告
    report_path = os.path.join(output_dir, 'download_report.csv')
    report_df = pd.DataFrame(results)
    report_df.to_csv(report_path, index=False, encoding='utf-8-sig')
    
    print(f"\n{'='*50}")
    print("下载完成!")
    print(f"✓ 成功: {successful}")
    print(f"✗ 失败: {failed}")
    print(f"📁 图像保存在: {os.path.abspath(output_dir)}")
    print(f"📋 报告保存为: {report_path}")
    
    # 显示部分成功下载的图像
    if successful > 0:
        print(f"\n前5个成功下载的文件:")
        success_files = [r['filename'] for r in results if r['status'] == 'success']
        for i, filename in enumerate(success_files[:5]):
            print(f"  {i+1}. {filename}")

def main():
    parser = argparse.ArgumentParser(description='从CSV文件下载所有图像')
    parser.add_argument('csv_file', help='CSV文件路径')
    parser.add_argument('-o', '--output', default='downloaded_images', 
                       help='输出目录 (默认: downloaded_images)')
    parser.add_argument('-w', '--workers', type=int, default=5, 
                       help='并发下载线程数 (默认: 5)')
    parser.add_argument('-c', '--column', default='url', 
                       help='包含URL的列名 (默认: url)')
    
    args = parser.parse_args()
    
    # 验证CSV文件是否存在
    if not os.path.exists(args.csv_file):
        print(f"✗ 错误: CSV文件不存在 - {args.csv_file}")
        return
    
    print(f"开始处理CSV文件: {args.csv_file}")
    print(f"输出目录: {args.output}")
    print(f"并发数: {args.workers}")
    
    # 读取CSV文件并显示基本信息
    try:
        df = pd.read_csv(args.csv_file)
        print(f"\nCSV文件信息:")
        print(f"  总行数: {len(df)}")
        print(f"  列名: {', '.join(df.columns.tolist())}")
        
        # 检查指定列是否存在
        if args.column not in df.columns:
            print(f"✗ 错误: 列 '{args.column}' 不存在于CSV文件中")
            print(f"可用列: {', '.join(df.columns.tolist())}")
            return
        
        url_count = df[args.column].dropna().count()
        print(f"  '{args.column}'列中的URL数量: {url_count}")
        
        # 显示前几个URL示例
        if url_count > 0:
            print(f"\nURL示例:")
            for url in df[args.column].dropna().head(3):
                print(f"  - {url}")
    
    except Exception as e:
        print(f"✗ 读取CSV文件失败: {e}")
        return
    
    # 确认是否继续
    print(f"\n{'='*50}")
    response = input("是否开始下载? (y/n): ")
    if response.lower() != 'y':
        print("取消下载")
        return
    
    # 执行下载
    download_images_from_csv(args.csv_file, args.output, args.workers)

if __name__ == "__main__":
    main()