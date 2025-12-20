import cv2
import numpy as np
from PIL import Image

def clean_image(image_path, output_path):
    """Supprime le bruit et améliore la netteté."""
    img = cv2.imread(image_path)
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, sharpen_kernel)
    cv2.imwrite(output_path, sharpened)
    return output_path