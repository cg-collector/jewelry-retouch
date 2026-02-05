import cv2
import numpy as np
from PIL import Image

def get_canny_image(image, low_threshold=100, high_threshold=200):
    """
    Convert a PIL Image to a Canny edge map.
    """
    image = np.array(image)
    
    # Check if image has alpha channel, if so, handle it (e.g., blend with white background)
    if image.shape[-1] == 4:
        # Create a white background
        background = np.ones_like(image[:, :, :3]) * 255
        alpha = image[:, :, 3:] / 255.0
        image = (image[:, :, :3] * alpha + background * (1 - alpha)).astype(np.uint8)
    
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
    canny_image = cv2.Canny(image, low_threshold, high_threshold)
    canny_image =  canny_image[:, :, None]
    canny_image = np.concatenate([canny_image, canny_image, canny_image], axis=2)
    return Image.fromarray(canny_image)

def resize_image_maintain_aspect_ratio(image, max_size=512):
    """
    Resize image maintaining aspect ratio so that the max dimension is max_size.
    """
    width, height = image.size
    if width > height:
        if width > max_size:
            ratio = max_size / width
            new_width = max_size
            new_height = int(height * ratio)
            image = image.resize((new_width, new_height), Image.LANCZOS)
    else:
        if height > max_size:
            ratio = max_size / height
            new_height = max_size
            new_width = int(width * ratio)
            image = image.resize((new_width, new_height), Image.LANCZOS)
    return image
