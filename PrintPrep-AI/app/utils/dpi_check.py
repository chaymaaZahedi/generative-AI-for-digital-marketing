from PIL import Image

from PIL import Image
Image.MAX_IMAGE_PIXELS = None
# def check_upscale(image_path, print_width_cm, print_height_cm, target_dpi=300):
#     """
#     Vérifie si l'image a assez de pixels pour l'impression et calcule le facteur d'upscale nécessaire.

#     Args:
#         image_path (str): chemin vers l'image.
#         print_width_cm (float): largeur d'impression en cm.
#         print_height_cm (float): hauteur d'impression en cm.
#         target_dpi (int): DPI souhaité pour l'impression (ex: 300).

#     Returns:
#         dict: informations avec DPI actuel, pixels requis, et facteur d'upscale.
#     """
#     # Ouvrir l'image
#     img = Image.open(image_path)
#     width_px, height_px = img.size

#     # Convertir taille d'impression en pouces
#     print_width_in = print_width_cm / 2.54
#     print_height_in = print_height_cm / 2.54

#     # DPI actuel
#     dpi_x = width_px / print_width_in
#     dpi_y = height_px / print_height_in

#     # Pixels requis pour atteindre le DPI cible
#     required_width_px = int(print_width_in * target_dpi)
#     required_height_px = int(print_height_in * target_dpi)

#     # Facteur d'upscale nécessaire
#     scale_factor_x = required_width_px / width_px
#     scale_factor_y = required_height_px / height_px
#     scale_factor = max(scale_factor_x, scale_factor_y)

#     info = {
#         "current_dpi_x": round(dpi_x, 2),
#         "current_dpi_y": round(dpi_y, 2),
#         "required_width_px": required_width_px,
#         "required_height_px": required_height_px,
#         "scale_factor_needed": round(scale_factor, 2),
#         "upscale_needed": scale_factor > 1.01
#     }

#     return info

# ------------------------------------------ v2:affiche si dpi est petit ou plus grand que celui souhaite --------------------------
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def check_upscale(image_path, banner_width_m, banner_height_m, support_type="poster", display=True):
    """
    Analyse la résolution d'une image par rapport à la taille d’un support et au type de support
    (flyer, poster, billboard) pour déterminer la distance de vision recommandée et le DPI minimal.

    Paramètres :
        image_path (str): chemin de l'image.
        banner_width_m (float): largeur du support en mètres.
        banner_height_m (float): hauteur du support en mètres.
        support_type (str): type de support ("flyer", "poster", "billboard").
        display (bool): si True, affiche les résultats formatés.

    Retourne :
        dict : toutes les valeurs calculées.
    """

    # Distances moyennes selon le type de support
    support_distances = {
        "flyer": 0.6,     # 0.6 m
        "poster": 1.5,    # 1.5 m
        "billboard": 50   # 50 m
    }

    # Tableau de correspondance distance -> DPI minimum
    dpi_reference = {
        0.6: 300,
        1: 180,
        1.5: 120,
        2: 90,
        3: 60,
        5: 35,
        10: 18,
        15: 12,
        50: 4,
        60: 3,
        200: 1
    }

    # Vérifier que le type de support existe
    if support_type not in support_distances:
        raise ValueError(f"Support inconnu '{support_type}'. Choisir entre 'flyer', 'poster', 'billboard'.")

    # Distance de vision basée sur le type de support
    view_distance_m = support_distances[support_type]

    # Trouver le DPI recommandé le plus proche
    sorted_distances = sorted(dpi_reference.keys())
    closest_distance = min(sorted_distances, key=lambda d: abs(d - view_distance_m))
    recommended_dpi = dpi_reference[closest_distance]

    # Ouvrir l’image et récupérer ses dimensions
    img = Image.open(image_path)
    width_px, height_px = img.size

    # Conversion mètres → pouces
    width_inch = banner_width_m * 39.3701
    height_inch = banner_height_m * 39.3701

    # Calcul des DPI réels
    dpi_x = width_px / width_inch
    dpi_y = height_px / height_inch
    avg_dpi = (dpi_x + dpi_y) / 2

    # Déterminer la qualité par rapport à la référence
    if avg_dpi >= recommended_dpi:
        quality = "adéquate ou supérieure"
        upscale_factor = 1.0
        message = f"Résolution suffisante ({avg_dpi:.2f} DPI ≥ {recommended_dpi} DPI recommandé)."
    else:
        upscale_factor = recommended_dpi / avg_dpi
        quality = "insuffisante"
        message = f"Résolution insuffisante ({avg_dpi:.2f} DPI < {recommended_dpi} DPI requis). " \
                  f"Upscaling x{upscale_factor:.2f} conseillé."

    results = {
        "Support type": support_type,
        "Image width (px)": width_px,
        "Image height (px)": height_px,
        "Banner width (m)": banner_width_m,
        "Banner height (m)": banner_height_m,
        "Viewing distance (m)": view_distance_m,
        "Closest reference distance (m)": closest_distance,
        "Recommended DPI": recommended_dpi,
        "DPI X": round(dpi_x, 2),
        "DPI Y": round(dpi_y, 2),
        "Average DPI": round(avg_dpi, 2),
        "Quality": quality,
        "Upscale factor suggested": round(upscale_factor, 2),
        "Decision": message
    }

    if display:
        print("\n--- Analyse de la résolution de l’image ---")
        for key, value in results.items():
            print(f"{key:<35}: {value}")
        print("-------------------------------------------\n")

    return results