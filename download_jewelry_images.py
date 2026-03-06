#!/usr/bin/env python3
"""Download jewelry images from the exported JSONL file."""

import os
import json
import urllib.request
from pathlib import Path

def download_image(url, dest_path):
    """Download an image from URL to destination path."""
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"✓ Downloaded: {dest_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {url}: {e}")
        return False

def main():
    # Paths
    jsonl_path = "outputs/jewelry_export/ghost_jewelry_20260302_112237.jsonl"
    output_dir = Path("data/user_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read and download
    downloaded = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            url = record.get("generated_image_url")
            record_id = record.get("record_id", i)

            if url:
                # Determine file extension from URL or default to .jpg
                ext = ".jpg"  # Default
                filename = f"jewelry_{record_id:05d}{ext}"
                dest_path = output_dir / filename

                if download_image(url, dest_path):
                    downloaded += 1

    print(f"\n✓ Downloaded {downloaded} images to {output_dir}")

if __name__ == "__main__":
    main()
