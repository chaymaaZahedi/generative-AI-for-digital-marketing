from PIL import Image, ImageCms
import os

Image.MAX_IMAGE_PIXELS = None
# def soft_proof_rgb(image_path, cmyk_profile_path="utils/profiles/USWebCoatedSWOP.icc", output_path="proof_preview.jpg"):
#     """
#     Simule le rendu CMYK d'une image RGB sur écran (soft proof),
#     compatible avec les versions récentes de Pillow.
#     """
#     if not os.path.exists(cmyk_profile_path):
#         raise FileNotFoundError(f"Profil ICC non trouvé : {cmyk_profile_path}")

#     img = Image.open(image_path).convert("RGB")

#     # Profils ICC
#     rgb_profile = ImageCms.createProfile("sRGB")
#     cmyk_profile = ImageCms.getOpenProfile(cmyk_profile_path)

#     # Transformation soft proofing (intent = perceptual)
#     proof_transform = ImageCms.buildProofTransform(
#         rgb_profile,   # source
#         rgb_profile,   # destination pour affichage
#         cmyk_profile,  # profil imprimante
#         "RGB",         # mode sortie
#         "perceptual"   # rendering intent
#     )

#     proof_img = ImageCms.applyTransform(img, proof_transform)

#     proof_img.save(output_path, "JPEG")
#     print(f"Soft proof enregistrée : {output_path}")
#     return proof_img
# ==============================version 2================================
# def soft_proof_rgb(image_path, cmyk_profile_path="utils/profiles/USWebCoatedSWOP.icc", output_path="proof_preview_v2_without_conv.jpg"):
#     """
#     Soft proof simulé en convertissant directement l'image RGB vers CMYK puis retour RGB.
#     Compatible avec toutes les versions Pillow.
#     """
#     img = Image.open(image_path).convert("RGB")
#     rgb_profile = ImageCms.createProfile("sRGB")
#     cmyk_profile = ImageCms.getOpenProfile(cmyk_profile_path)

#     # Conversion RGB -> CMYK
#     transform = ImageCms.buildTransform(rgb_profile, cmyk_profile, "RGB", "CMYK")
#     img_cmyk = ImageCms.applyTransform(img, transform)

#     # Reconversion CMYK -> RGB pour affichage écran
#     back_transform = ImageCms.buildTransform(cmyk_profile, rgb_profile, "CMYK", "RGB")
#     proof_img = ImageCms.applyTransform(img_cmyk, back_transform)

#     proof_img.save(output_path, "JPEG")
#     print(f"Soft proof simulée enregistrée : {output_path}")
#     return proof_img

# ========================================== version3 =============================
from PIL import Image, ImageCms
import os, gc, sys, time

def soft_proof_rgb(
    image_path,
    cmyk_profile_path="app/utils/profiles/USWebCoatedSWOP.icc",
    output_path="soft_proof_preview.jpg",
    max_preview_size=4000
):
    """
    Soft proof allégé : simule le rendu imprimé d'une image RGB en CMYK puis retour RGB.
    Affiche la progression dans le terminal.
    """

    def progress(step, total_steps, message):
        """Affiche une barre de progression textuelle."""
        bar_length = 30
        filled = int(bar_length * step / total_steps)
        bar = "█" * filled + "-" * (bar_length - filled)
        sys.stdout.write(f"\r[{bar}] {int(step/total_steps*100)}% — {message}")
        sys.stdout.flush()

    total_steps = 6
    step = 0

    # --- Étape 1 : Vérification des fichiers
    progress(step, total_steps, "Vérification des fichiers...")
    time.sleep(0.2)
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable : {image_path}")
    if not os.path.exists(cmyk_profile_path):
        raise FileNotFoundError(f"Profil ICC introuvable : {cmyk_profile_path}")
    step += 1

    # --- Étape 2 : Chargement et réduction de l'image
    progress(step, total_steps, "Chargement de l'image...")
    img = Image.open(image_path).convert("RGB")
    step += 1

    if max(img.size) > max_preview_size:
        scale = max_preview_size / max(img.size)
        new_size = (int(img.width * scale), int(img.height * scale))
        progress(step, total_steps, f"Redimensionnement vers {new_size}...")
        img = img.resize(new_size, Image.LANCZOS)
    else:
        progress(step, total_steps, "Taille adaptée, pas de redimensionnement nécessaire.")
    step += 1

    # --- Étape 3 : Préparation des profils
    progress(step, total_steps, "Préparation des profils ICC...")
    rgb_profile = ImageCms.createProfile("sRGB")
    cmyk_profile = ImageCms.getOpenProfile(cmyk_profile_path)
    step += 1

    # --- Étape 4 : Simulation du passage RGB → CMYK → RGB
    progress(step, total_steps, "Conversion RGB → CMYK → RGB...")
    rgb_to_cmyk = ImageCms.buildTransform(rgb_profile, cmyk_profile, "RGB", "CMYK")
    cmyk_to_rgb = ImageCms.buildTransform(cmyk_profile, rgb_profile, "CMYK", "RGB")

    img_cmyk = ImageCms.applyTransform(img, rgb_to_cmyk)
    proof_img = ImageCms.applyTransform(img_cmyk, cmyk_to_rgb)
    step += 1

    # --- Étape 5 : Sauvegarde
    progress(step, total_steps, "Sauvegarde de l'image de prévisualisation...")
    proof_img.save(output_path, "JPEG", quality=95)
    step += 1

    # --- Étape finale : Nettoyage
    del img, img_cmyk
    gc.collect()
    progress(step, total_steps, "Terminé ✔\n")

    print(f"\n✅ Soft proof enregistrée : {output_path}")
    return proof_img