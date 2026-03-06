import requests
import base64
import os
import json
from PIL import Image
import io

import time

class APIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.headers_multipart = {
            "Authorization": f"Bearer {api_key}"
        }

    def image_to_base64(self, image):
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    
    def image_to_bytes(self, image):
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return buffered.getvalue()

    def generate_image(self, model, prompt, negative_prompt, image, control_strength=1.0, steps=30, timeout=300, endpoint=None):
        """
        Calls the API to generate an image.
        Assumes an OpenAI-compatible or similar structure.
        """
        
        # Prepare image
        start_encode = time.time()

        # Get dimensions
        width, height = image.size

        endpoint = endpoint
        is_edits = "/edits" in endpoint

        # Only encode what we need
        if is_edits:
            # For edits endpoint, we only need bytes for multipart upload
            img_bytes = self.image_to_bytes(image)
            encode_duration = time.time() - start_encode

            # Log payload size
            payload_size_mb = len(img_bytes) / 1024 / 1024
            print(f"Image encoding took {encode_duration:.2f}s. Payload image size approx: {payload_size_mb:.2f} MB")

            if payload_size_mb > 5:
                print("Warning: Image payload is large (>5MB), this might cause network timeouts.")

            data = {
                "model": model,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "steps": steps,
                "cfg_scale": 7.5,
                "n": 1,
                "size": f"{width}x{height}",
                "response_format": "b64_json"
            }
            files = {
                "image": ("image.png", img_bytes, "image/png")
            }
        else:
            # For generations endpoint, we need base64
            img_b64 = self.image_to_base64(image)
            encode_duration = time.time() - start_encode

            # Log payload size
            payload_size_mb = len(img_b64) / 1024 / 1024
            print(f"Image encoding took {encode_duration:.2f}s. Payload image size approx: {payload_size_mb:.2f} MB")

            if payload_size_mb > 5:
                print("Warning: Image payload is large (>5MB), this might cause network timeouts.")

            payload = {
                "model": model,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "init_images": [img_b64],
                "image": img_b64,
                "steps": steps,
                "cfg_scale": 7.5,
                "controlnet_conditioning_scale": control_strength,
                "n": 1,
                "size": f"{width}x{height}",
                "response_format": "b64_json"
            }
        
        # Logging for debugging
        print(f"Sending request to {self.base_url}{endpoint} with model {model}...")
        print(f"Timeout set to {timeout} seconds.")
        
        start_request = time.time()
        try:
            if is_edits:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers_multipart,
                    data=data,
                    files=files,
                    timeout=timeout
                )
            else:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    json=payload,
                    timeout=timeout
                )
            request_duration = time.time() - start_request
            print(f"Request completed in {request_duration:.2f}s")
            
            response.raise_for_status()
            result = response.json()
            
            # Parse result (handle different potential response formats)
            if "data" in result:
                # OpenAI style: data[0].b64_json or url
                item = result["data"][0]
                if "b64_json" in item:
                    return self.base64_to_image(item["b64_json"])
                elif "url" in item:
                    return self.url_to_image(item["url"])
            elif "images" in result:
                # A1111 style: images[0] (base64)
                return self.base64_to_image(result["images"][0])
                
            raise ValueError(f"Unexpected response format: {result.keys()}")

        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            raise

    def base64_to_image(self, b64_str):
        image_data = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(image_data))

    def url_to_image(self, url):
        response = requests.get(url)
        return Image.open(io.BytesIO(response.content))
