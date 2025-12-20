# import os
# import shutil
# import requests
# from gradio_client import Client, handle_file

# def upscale_image_realesrgan(image_path: str, output_dir: str, outscale: int = 2):
#     """
#     Upscale une image via l'API RealESRGAN Gradio et sauvegarde le résultat dans output_dir.
#     Retourne le chemin complet de l'image upscalée.
#     """
#     os.makedirs(output_dir, exist_ok=True)
#     client = Client("tuan2308/Upscaler")  # API fonctionne bien avec ton test isolé

#     # Appel de l'API
#     result = client.predict(
#         img=handle_file(image_path),
#         model_name="realesr-general-x4v3",
#         denoise_strength=0.5,
#         face_enhance=False,
#         outscale=outscale,
#         api_name="/realesrgan"
#     )

#     # Préparer le chemin de sortie
#     output_path = os.path.join(output_dir, f"upscaled_x{outscale}.png")

#     # Télécharger ou copier selon le type de result
#     if isinstance(result, str):
#         if result.startswith("http"):
#             r = requests.get(result, stream=True)
#             if r.status_code == 200:
#                 with open(output_path, "wb") as f:
#                     f.write(r.content)
#             else:
#                 raise RuntimeError(f"Erreur HTTP : {r.status_code}")
#         elif os.path.exists(result):
#             shutil.copy(result, output_path)
#         else:
#             raise FileNotFoundError(f"Le chemin retourné par l'API n'existe pas : {result}")
#     else:
#         raise TypeError(f"Le résultat de l'API n’est pas une chaîne : {type(result)}")

#     return output_path

# --------------------------------------
import os
import shutil
from gradio_client import Client, handle_file

def upscale_image_realesrgan(image_path: str, output_dir: str, outscale: int = 2):
    """
    Upscale une image via l'API RealESRGAN Gradio et sauvegarde le résultat dans output_dir.
    Retourne le chemin complet de l'image upscalée.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        client = Client("tuan2308/Upscaler")
        
        # Appel de l'API
        result = client.predict(
            img=handle_file(image_path),
            model_name="realesr-general-x4v3",
            denoise_strength=0.5,
            face_enhance=False,
            outscale=outscale,
            api_name="/realesrgan"
        )
        
        # Le résultat est un chemin vers un fichier temporaire (ou un tuple/liste selon l'API)
        # Vérifions le type de résultat
        if isinstance(result, (list, tuple)):
            result = result[0]
            
        if not result or not os.path.exists(result):
            raise RuntimeError(f"L'API n'a pas retourné un fichier valide: {result}")

        # Préparer le chemin de sortie
        # On essaie de garder l'extension d'origine ou png
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_upscaled_x{outscale}{ext}"
        output_path = os.path.join(output_dir, output_filename)

        # Copier le fichier résultat vers la destination
        shutil.copy(result, output_path)
        
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'upscaling avec gradio_client: {str(e)}")
