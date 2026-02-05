import argparse
import os
import sys
import datetime
import pathlib

# Add parent dir to path to import main and config
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from main import generate_jewelry_showcase
from tools.quick_prompt_test import read_prompts

def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="nano-banana-2-2k-vip")
    parser.add_argument("--prompt_file", default="prompts/base_prompt.txt")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--data_dir", default="数据")
    parser.add_argument("--outdir", default=None)
    args = parser.parse_args()

    # Define categories
    categories = ["耳环", "手环", "手链", "项链"]
    
    # Read prompt
    prompts = read_prompts(None, args.prompt_file, file_as_single=True)
    if not prompts:
        print("No prompts found.")
        return
    prompt = prompts[0] # Single mode implies one prompt

    # Output dir
    outdir = args.outdir or f"outputs/batch_test_{ts()}"
    os.makedirs(outdir, exist_ok=True)
    
    print(f"Output directory: {outdir}")
    print(f"Model: {args.model}")
    print(f"Prompt source: {args.prompt_file}")

    tasks = []

    # Scan for files
    base_path = os.path.abspath(args.data_dir)
    for cat in categories:
        cat_dir = os.path.join(base_path, cat)
        if not os.path.exists(cat_dir):
            print(f"Warning: Category directory not found: {cat_dir}")
            continue
            
        for root, _, files in os.walk(cat_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    # Check if it's not a hidden file
                    if not file.startswith('.'):
                        tasks.append((cat, os.path.join(root, file)))

    print(f"Found {len(tasks)} images to process.")

    # Process
    for idx, (cat, img_path) in enumerate(tasks, 1):
        filename = os.path.splitext(os.path.basename(img_path))[0]
        # Construct output filename: category_filename.png
        # Ensure filename is safe
        safe_filename = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename)
        out_name = f"{cat}_{safe_filename}.png"
        out_path = os.path.join(outdir, out_name)
        
        print(f"[{idx}/{len(tasks)}] Processing {cat}/{os.path.basename(img_path)} -> {out_name}")
        
        try:
            generate_jewelry_showcase(
                image_path=img_path,
                prompt=prompt,
                negative_prompt="", # Default
                model_name=args.model,
                output_path=out_path,
                steps=args.steps,
                control_strength=1.0,
                max_size=1024,
                timeout=300
            )
        except Exception as e:
            print(f"Failed to process {img_path}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
