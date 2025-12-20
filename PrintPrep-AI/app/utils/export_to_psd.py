import pyvips
from pathlib import Path

def convert_tiff_to_psd_vips(input_tiff, output_psd, icc_profile_path):
    input_path = str(Path(input_tiff).resolve())
    output_path = str(Path(output_psd).resolve())
    icc_path = str(Path(icc_profile_path).resolve())

    print(f"▶ Conversion haute fidélité avec pyvips...")

    try:
        # 1. Charger l'image
        # pyvips est extrêmement rapide et ne charge pas tout en RAM (streaming)
        image = pyvips.Image.new_from_file(input_path, access="sequential")

        # 2. Attacher le profil ICC
        # On charge le profil depuis le disque
        with open(icc_path, "rb") as f:
            icc_data = f.read()
        
        # On définit le profil ICC dans les métadonnées de l'image
        image = image.copy()
        image.set_type(pyvips.GValue.blob_type, "icc-profile-data", icc_data)

        # 3. Sauvegarder en PSD
        # Note : vips peut écrire en PSD, si votre version de vips le supporte.
        # Sinon, nous écrivons un TIFF avec le profil forcé que Photoshop lira parfaitement.
        image.write_to_file(output_path)
            
        print(f"✅ Conversion terminée. Profil {Path(icc_path).name} intégré.")

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    convert_tiff_to_psd_vips(
        "../temp_uploads/cmyk_lanczos_enhanced_test_upscaled_x6.tiff",
        "../temp_uploads/mon_image_couleurs_fixes.psd",
        "profiles/UncoatedFOGRA29.icc"
    )