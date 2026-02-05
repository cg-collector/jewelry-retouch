import argparse
import os
import sys
import json
import datetime
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from main import generate_jewelry_showcase
from config import Config

def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p

def read_prompts(prompt, prompt_file, file_as_single=False):
    items = []
    if prompt:
        items.append(prompt.strip())
    if prompt_file and os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            if file_as_single:
                content = f.read().strip()
                if content:
                    items.append(content)
            else:
                for line in f:
                    t = line.strip()
                    if t:
                        items.append(t)
    return items

def sanitize_name(s, max_len=40):
    s = "".join(c if c.isalnum() or c in "-_" else "_" for c in s.lower())
    if len(s) > max_len:
        s = s[:max_len] + "_"
    return s or "prompt"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--model")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt_file", default="prompts/base_prompt.txt")
    parser.add_argument("--negative_prompt", default="")
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--max_size", type=int, default=1024)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--single", action="store_true", help="Treat entire prompt_file content as a single prompt")
    parser.add_argument("--control_strength", type=float, default=1.0, help="Control strength (0.0-1.5, default: 1.0)")
    args = parser.parse_args()

    prompts = read_prompts(args.prompt, args.prompt_file, file_as_single=args.single)
    if not prompts:
        print("No prompts provided.")
        sys.exit(1)

    root = args.outdir or f"outputs/prompt_tests_{ts()}"
    ensure_dir(root)

    models = [args.model] if args.model else Config().models
    if not models:
        print("No models configured in .env")
        sys.exit(1)

    for model in models:
        model_dir = ensure_dir(os.path.join(root, sanitize_name(model)))
        meta_path = os.path.join(model_dir, "prompts.jsonl")
        with open(meta_path, "a", encoding="utf-8") as meta:
            for idx, p in enumerate(prompts, start=1):
                base = sanitize_name(p)
                outfile = os.path.join(model_dir, f"{idx:02d}.png") #输出图像的文件名
                rec = {
                    "index": idx,
                    "prompt": p,
                    "negative_prompt": args.negative_prompt,
                    "model": model,
                    "steps": args.steps,
                    "control_strength": args.control_strength,
                    "max_size": args.max_size,
                    "timeout": args.timeout,
                    "image": args.image,
                    "output": outfile
                }
                meta.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(f"Model {model}: Running {idx}/{len(prompts)} -> {outfile}")
                generate_jewelry_showcase(
                    image_path=args.image,
                    prompt=p,
                    negative_prompt=args.negative_prompt,
                    model_name=model,
                    output_path=outfile,
                    steps=args.steps,
                    control_strength=args.control_strength,
                    max_size=args.max_size,
                    timeout=args.timeout
                )
    print(f"Done. Outputs in {root}")

if __name__ == "__main__":
    main()
