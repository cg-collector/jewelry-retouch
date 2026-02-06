import argparse
import json
import os
import requests
import mimetypes
from concurrent.futures import ThreadPoolExecutor

def download_file(url, filepath_base):
    if not url:
        return False, "No URL"
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').split(';')[0].strip()
        ext = mimetypes.guess_extension(content_type)
        if not ext:
            # Fallback based on content type string if mimetypes fails or is unknown
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg' # Ultimate fallback
        
        # Prefer .jpg over .jpe
        if ext == '.jpe':
            ext = '.jpg'
            
        filepath = filepath_base + ext
            
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True, filepath
    except Exception as e:
        return False, f"{url}: {str(e)}"

def process_line(line, output_dir):
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return []

    record_id = data.get('record_id')
    if not record_id:
        return []

    results = []
    
    # Process Generated Image
    gen_url = data.get('generated_image_url')
    if gen_url:
        save_dir = os.path.join(output_dir, 'generated')
        save_path_base = os.path.join(save_dir, str(record_id))
        results.append((gen_url, save_path_base))

    # Process Original Image
    orig_url = data.get('original_image_url')
    if orig_url:
        save_dir = os.path.join(output_dir, 'original')
        save_path_base = os.path.join(save_dir, str(record_id))
        results.append((orig_url, save_path_base))
        
    return results

def main():
    parser = argparse.ArgumentParser(description="Download images from JSONL file")
    parser.add_argument("input_file", help="Path to JSONL file")
    parser.add_argument("--output_dir", help="Output directory", default=None)
    parser.add_argument("--workers", type=int, default=8, help="Number of concurrent downloads")
    
    args = parser.parse_args()
    
    if not args.output_dir:
        # Create a folder named after the input file (without extension) in the same directory as input file
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        input_dir = os.path.dirname(os.path.abspath(args.input_file))
        args.output_dir = os.path.join(input_dir, f"{base_name}_images")
    
    os.makedirs(os.path.join(args.output_dir, 'generated'), exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, 'original'), exist_ok=True)
    
    tasks = []
    
    print(f"Reading {args.input_file}...")
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    tasks.extend(process_line(line, args.output_dir))
    except FileNotFoundError:
        print(f"Error: File {args.input_file} not found.")
        return

    if not tasks:
        print("No images found to download.")
        return
        
    print(f"Found {len(tasks)} images to download. Saving to {args.output_dir}")
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for url, path_base in tasks:
            futures.append(executor.submit(download_file, url, path_base))
            
        completed = 0
        total = len(futures)
        for future in futures:
            success, msg = future.result()
            completed += 1
            if completed % 10 == 0 or completed == total:
                print(f"Progress: {completed}/{total}", end='\r')
                
            if not success:
                print(f"\nFailed: {msg}")

    print(f"\nDone. Check {args.output_dir}")

if __name__ == "__main__":
    main()
