# prépare l’image pour qu’elle soit “print ready”
from PIL import Image, ImageCms, TiffImagePlugin
import os, sys, time

Image.MAX_IMAGE_PIXELS = None
# def convert_to_cmyk(image_path, output_path, cmyk_profile_path="utils/profiles/USWebCoatedSWOP.icc"):
#     """Convertit une image RGB en CMYK à l’aide d’un profil ICC externe."""
#     img = Image.open(image_path)
    
#     if img.mode != "RGB":
#         img = img.convert("RGB")

#     # Profil source (sRGB)
#     rgb_profile = ImageCms.createProfile("sRGB")

#     # Profil destination (CMYK) depuis fichier ICC
#     cmyk_profile = ImageCms.getOpenProfile(cmyk_profile_path)

#     transform = ImageCms.buildTransform(rgb_profile, cmyk_profile, "RGB", "CMYK")
#     img_cmyk = ImageCms.applyTransform(img, transform)
    
#     img_cmyk.save(output_path, "TIFF")
#     return output_path

def convert_to_cmyk(
    image_path,
    output_path,
    cmyk_profile_path="app/utils/profiles/USWebCoatedSWOP.icc",
    tile_size=2048
):
    """
    Conversion mémoire-optimisée d'une image RGB en CMJN.
    Traite l'image par blocs (tiles) pour éviter la saturation RAM.
    Affiche une barre de progression dynamique dans le terminal.
    """
    print(f"[INFO] Chargement de l'image source : {image_path}")
    img = Image.open(image_path)

    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    total_tiles = (height // tile_size + 1) * (width // tile_size + 1)
    processed_tiles = 0
    print(f"[INFO] Dimensions : {width}x{height}px")
    print(f"[INFO] Conversion CMJN en cours (par blocs de {tile_size}px)...\n")

    # Prépare les profils ICC
    rgb_profile = ImageCms.createProfile("sRGB")
    cmyk_profile = ImageCms.getOpenProfile(cmyk_profile_path)
    transform = ImageCms.buildTransform(rgb_profile, cmyk_profile, "RGB", "CMYK")

    # Active BigTIFF pour supporter les grands fichiers
    TiffImagePlugin.WRITE_LIBTIFF = True

    # Création d’une image CMJN vide
    output_img = Image.new("CMYK", (width, height))

    def update_progress(progress):
        """Affiche une barre de progression dans le terminal."""
        bar_length = 40
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        sys.stdout.write(f"\r    → Progression : |{bar}| {int(progress * 100)}%")
        sys.stdout.flush()

    # Traitement par blocs
    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            right = min(x + tile_size, width)
            bottom = min(y + tile_size, height)
            box = (x, y, right, bottom)

            region = img.crop(box)
            region_cmyk = ImageCms.applyTransform(region, transform)
            output_img.paste(region_cmyk, box)

            processed_tiles += 1
            update_progress(processed_tiles / total_tiles)

    print("\n[INFO] Conversion terminée, sauvegarde du fichier...")

    # Lecture du profil ICC
    with open(cmyk_profile_path, "rb") as f:
        icc_bytes = f.read()

    # Sauvegarde finale
    output_img.save(output_path, format="TIFF", compression="tiff_deflate", icc_profile=icc_bytes)
    print(f"[✅] Fichier enregistré : {output_path}")

    return output_path