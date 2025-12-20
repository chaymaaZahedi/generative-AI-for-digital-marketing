# from PIL import Image, ImageCms

# def read_metadata(image_path):
#     """Lit les métadonnées de base d'une image : dimensions, mode, profil ICC"""
#     img = Image.open(image_path)
#     info = {
#         "format": img.format,
#         "mode": img.mode,
#         "size": img.size,  # largeur, hauteur
#         "dpi": img.info.get("dpi", "Non spécifié"),
#         "icc_profile": "Oui" if "icc_profile" in img.info else "Non"
#     }
#     return info
# utils/metadata.py
from PIL import Image, ImageCms
import os
import io

def read_metadata(image_path):
    """
    Lit et retourne un dictionnaire de métadonnées pertinentes pour le pipeline.
    Conserve uniquement les données utiles aux images générées par IA.
    
    Returns:
        dict with keys:
          format, mode, size, dpi, icc_profile_present, icc_profile_name,
          bits_per_channel, filesize_bytes
    """
    result = {}
    filesize = os.path.getsize(image_path)
    result["filesize_bytes"] = filesize

    with Image.open(image_path) as img:
        result["format"] = img.format
        result["mode"] = img.mode
        result["size"] = img.size  # (width_px, height_px)

        # DPI (certaines images le stockent différemment)
        dpi = img.info.get("dpi") or img.info.get("resolution") or None
        result["dpi"] = dpi

        # Profondeur de bits par canal
        try:
            if hasattr(img, "tag_v2") and "BitsPerSample" in img.tag_v2:
                bits = img.tag_v2.get("BitsPerSample")
                if isinstance(bits, (list, tuple)):
                    bits = bits[0]
                result["bits_per_channel"] = int(bits)
            else:
                mode_to_bits = {"1": 1, "L": 8, "P": 8, "RGB": 8, "RGBA": 8, "CMYK": 8, "I;16": 16}
                result["bits_per_channel"] = mode_to_bits.get(img.mode, 8)
        except Exception:
            result["bits_per_channel"] = None

        # Profil ICC (utile pour la conversion colorimétrique)
        icc_profile_bytes = img.info.get("icc_profile")
        result["icc_profile_present"] = bool(icc_profile_bytes)
        result["icc_profile_name"] = None
        if icc_profile_bytes:
            try:
                icc = ImageCms.ImageCmsProfile(io.BytesIO(icc_profile_bytes))
                try:
                    result["icc_profile_name"] = ImageCms.getProfileName(icc)
                except Exception:
                    result["icc_profile_name"] = "ICC profile (nom inconnu)"
            except Exception:
                result["icc_profile_name"] = "profil ICC invalide"

    return result


