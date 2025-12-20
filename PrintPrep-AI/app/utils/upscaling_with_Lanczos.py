from PIL import Image
Image.MAX_IMAGE_PIXELS = None
def upscale_lanczos(image_path, output_path, scale_factor=None, target_size=None):
    """
    Redimensionne une image avec interpolation Lanczos (haute qualité).
    Tu peux soit fournir un facteur d'agrandissement, soit une taille cible.

    Args:
        image_path (str): chemin de l'image d'entrée
        output_path (str): chemin de sortie
        scale_factor (float): facteur d'agrandissement (ex: 2.0 = x2)
        target_size (tuple): (largeur_px, hauteur_px)
    """
    img = Image.open(image_path)

    if scale_factor:
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
    elif target_size:
        new_width, new_height = target_size
    else:
        raise ValueError("Tu dois fournir scale_factor ou target_size")

    upscaled = img.resize((new_width, new_height), Image.LANCZOS)
    upscaled.save(output_path, quality=100)
    print(f"Image redimensionnée en {new_width}x{new_height} avec Lanczos ✓")




