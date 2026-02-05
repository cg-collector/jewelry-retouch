import argparse
import os
import sys
import datetime
from PIL import Image
from config import Config
from api_client import APIClient
from utils import resize_image_maintain_aspect_ratio

class Logger(object):
    def __init__(self, filename="default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        self.terminal.flush()
        self.log.flush()

def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"run_{timestamp}.log")
    
    sys.stdout = Logger(log_file)
    sys.stderr = sys.stdout
    print(f"Logging to {log_file}")

def generate_jewelry_showcase(
    image_path, 
    prompt, 
    negative_prompt, 
    model_name=None,
    output_path="output.png", 
    steps=30, 
    control_strength=1.0,
    max_size=1024,
    timeout=300
):
    # Load configuration
    print("Loading configuration from .env...")
    config = Config()
    
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return

    # Initialize API Client
    if config.api_key:
        masked_key = config.api_key[:4] + "*" * (len(config.api_key) - 8) + config.api_key[-4:] if len(config.api_key) > 8 else "****"
        print(f"Using API Key: {masked_key}")
    else:
        print("Warning: No API Key found!")

    client = APIClient(config.base_url, config.api_key)

    # Determine model
    if model_name is None:
        if config.models:
            model_name = config.models[0]
            print(f"No model selected, using default: {model_name}")
        else:
            print("No models found in configuration.")
            return
    elif model_name not in config.models:
        print(f"Warning: Model '{model_name}' is not in the configured list: {config.models}")

    # Load and preprocess input image
    print(f"Loading input image from {image_path}...")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")
        
    original_image = Image.open(image_path).convert("RGB")
    
    # Resize to avoid sending huge images to API
    processed_image = resize_image_maintain_aspect_ratio(original_image, max_size=max_size)
    
    print(f"Calling API with model: {model_name}...")
    try:
        endpoint = config.get_endpoint_for_model(model_name)
        print(f"Resolved endpoint for {model_name}: {endpoint}")
        output_image = client.generate_image(
            model=model_name,
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=processed_image,
            control_strength=control_strength,
            steps=steps,
            timeout=timeout,
            endpoint=endpoint
        )
        
        # Save output
        output_image.save(output_path)
        print(f"Success! Image saved to {output_path}")
        
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate jewelry showcase image using API.")
    parser.add_argument("--image", type=str, required=True, help="Path to the input jewelry image.")
    parser.add_argument("--prompt", type=str, default="professional jewelry photography, close up, soft lighting, luxury background, high quality, 8k, photorealistic", help="Prompt for generation.")
    parser.add_argument("--negative_prompt", type=str, default="low quality, bad quality, blurry, distorted, ugly, watermark, text", help="Negative prompt.")
    parser.add_argument("--output", type=str, default="output.png", help="Path to save the output image.")
    parser.add_argument("--model", type=str, help="Specific model to use (optional).")
    parser.add_argument("--steps", type=int, default=30, help="Number of inference steps.")
    parser.add_argument("--control_scale", type=float, default=1.0, help="Control strength (if supported by API).")
    parser.add_argument("--max_size", type=int, default=1024, help="Max image dimension.")
    parser.add_argument("--timeout", type=int, default=300, help="API request timeout in seconds.")

    args = parser.parse_args()

    setup_logging()

    generate_jewelry_showcase(
        image_path=args.image,
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        model_name=args.model,
        output_path=args.output,
        steps=args.steps,
        control_strength=args.control_scale,
        max_size=args.max_size,
        timeout=args.timeout
    )
