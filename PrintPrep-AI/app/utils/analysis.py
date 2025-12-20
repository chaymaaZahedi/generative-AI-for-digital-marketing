from PIL import Image
import numpy as np
from skimage import filters
from collections import Counter
import cv2
from skimage import measure
import requests

def analyze_image(image_path,
                  w_color=0.4,
                  w_edge=0.3,
                  w_texture=0.3,
                  k_clusters=16,
                  max_edge_density=0.4,
                  max_entropy=8.0,
                  score_threshold=0.7,
                  analysis_max_dim=500.0):
    """
    Analyse une image pour déterminer si elle est probablement vectorisable.
    
    Args:
        image_path (str): chemin local ou URL de l'image.
        w_color, w_edge, w_texture (float): poids des métriques.
        k_clusters (int): nombre de clusters pour K-Means.
        max_edge_density, max_entropy (float): bornes pour normalisation.
        score_threshold (float): seuil pour la décision finale.
        analysis_max_dim (float): taille max pour redimensionner l'image.
        
    Returns:
        dict: métriques calculées et verdict vectorisation.
    """
    
    def load_image(path):
        """Charge une image depuis un chemin local ou URL."""
        try:
            if path.startswith('http://') or path.startswith('https://'):
                resp = requests.get(path)
                resp.raise_for_status()
                arr = np.frombuffer(resp.content, np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            else:
                img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Impossible de charger l'image.")
            return img
        except Exception as e:
            print(f"Erreur lors du chargement : {e}")
            return None

    def resize_image(img):
        """Redimensionne l'image si nécessaire pour l'analyse."""
        h, w = img.shape[:2]
        if max(h, w) > analysis_max_dim:
            ratio = analysis_max_dim / float(max(h, w))
            new_size = (int(w*ratio), int(h*ratio))
            return cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
        return img

    def normalize(value, min_val, max_val):
        value = max(min_val, min(value, max_val))
        return (value - min_val) / (max_val - min_val)

    def color_complexity(img, k=k_clusters):
        pixels = img.reshape((-1, 3)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, _ = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        return len(np.unique(labels))

    def edge_density(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blur, 50, 150)
        return np.sum(edges > 0) / (img.shape[0] * img.shape[1])

    def texture_entropy(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return measure.shannon_entropy(gray)

    # --- Analyse ---
    img = load_image(image_path)
    if img is None:
        return None

    img_resized = resize_image(img)

    # Calcul métriques brutes
    metric_colors = color_complexity(img_resized)
    metric_edges = edge_density(img_resized)
    metric_texture = texture_entropy(img_resized)

    # Normalisation
    score_color = normalize(metric_colors, 1, k_clusters)
    score_edge = normalize(metric_edges, 0, max_edge_density)
    score_texture = normalize(metric_texture, 0, max_entropy)

    # Simplicité (1 = simple, 0 = complexe)
    simplicity_color = 1 - score_color
    simplicity_edge = 1 - score_edge
    simplicity_texture = 1 - score_texture

    # Score final pondéré
    final_score = (w_color * simplicity_color +
                   w_edge * simplicity_edge +
                   w_texture * simplicity_texture)

    decision = "Vectorisable" if final_score > score_threshold else "Non-Vectorisable"

    # Retour sous forme de dictionnaire
    return {
        "num_colors": metric_colors,
        "edge_density": metric_edges,
        "entropy": metric_texture,
        "simplicity_color": simplicity_color,
        "simplicity_edge": simplicity_edge,
        "simplicity_texture": simplicity_texture,
        "final_score": final_score,
        "decision": decision
    }