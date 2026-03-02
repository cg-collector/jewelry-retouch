import os
import time
import datetime
from config import Config
from main import generate_jewelry_showcase, setup_logging

def run_batch_tests():
    # Load config to get models
    config = Config()
    if not config.models:
        print("No models found in config!")
        return

    # Create timestamped directory for results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = f"outputs/{timestamp}"
    os.makedirs(result_dir, exist_ok=True)
    
    print(f"Starting batch test. Results will be saved to {result_dir}")
    print(f"Models to test: {config.models}")
    
    # Ensure log directory exists (setup_logging handles it but good to be sure)
    setup_logging()
    
    test_image = "test_jewel.png"
    if not os.path.exists(test_image):
        print(f"Error: Test image {test_image} not found. Please create it first.")
        return

    for model in config.models:
        print(f"\n=== Testing Model: {model} ===")
        
        for i in range(1, 4): # Run 3 times
            print(f"  Run {i}/3...")
            output_filename = f"{model}_run{i}.png"
            output_path = os.path.join(result_dir, output_filename)
            
            start_time = time.time()
            try:
                generate_jewelry_showcase(
                    image_path=test_image,
                    prompt="luxury diamond ring, professional photography, studio lighting",
                    negative_prompt="low quality, blurry, bad anatomy",
                    model_name=model,
                    output_path=output_path,
                    steps=30,
                    max_size=1024,
                    timeout=300
                )
                duration = time.time() - start_time
                print(f"  Run {i} completed in {duration:.2f}s. Saved to {output_path}")
            except Exception as e:
                print(f"  Run {i} failed: {e}")
                
    print(f"\nBatch test completed. All results in {result_dir}")

if __name__ == "__main__":
    run_batch_tests()
