import os
import subprocess
from tqdm import tqdm
from PIL import Image, TiffImagePlugin

Image.MAX_IMAGE_PIXELS = None  # Désactive la limite anti "bomb" pour les très grandes images

def prepare_tiff_for_gs(input_tiff, temp_tiff="temp_for_gs.tiff"):
    """
    Réencode un TIFF volumineux en TIFF compressé standard (Deflate) pour Ghostscript.
    """
    print(f"[INFO] Réencodage du TIFF pour compatibilité Ghostscript...")
    with Image.open(input_tiff) as img:
        TiffImagePlugin.WRITE_LIBTIFF = True
        img.save(temp_tiff, compression="tiff_deflate")
    size_mo = os.path.getsize(temp_tiff) / (1024**2)
    print(f"[INFO] Nouveau TIFF créé : {temp_tiff} ({size_mo:.2f} Mo)")
    return temp_tiff

def tiff_to_pdfx(input_tiff, output_pdf, dpi=300):
    """
    Convertit un TIFF CMJN volumineux en PDF/X-1a via Ghostscript.
    """
    # 1️⃣ Réencodage TIFF pour compatibilité
    temp_tiff = prepare_tiff_for_gs(input_tiff)

    # 2️⃣ Commande Ghostscript
    gs_executable = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"
    gs_command = [
        gs_executable,  # Ghostscript doit être dans PATH
        "-dBATCH",
        "-dNOPAUSE",
        "-dSAFER",
        "-sDEVICE=pdfwrite",
        "-dPDFX",
        "-sColorConversionStrategy=CMYK",
        "-dProcessColorModel=/DeviceCMYK",
        f"-r{dpi}",
        f"-sOutputFile={output_pdf}",
        temp_tiff
    ]

    print(f"[INFO] Exécution Ghostscript pour générer PDF/X-1a...")
    
    # Exécution et barre de progression simulée
    process = subprocess.Popen(gs_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in tqdm(process.stdout, desc="Conversion PDF/X", unit="line"):
        pass  # Affiche la sortie Ghostscript si besoin : print(line.strip())

    process.wait()
    if process.returncode == 0:
        size_mo = os.path.getsize(output_pdf) / (1024**2)
        print(f"[✅] PDF/X-1a généré : {output_pdf} ({size_mo:.2f} Mo)")
    else:
        print(f"[❌] Erreur Ghostscript (code {process.returncode})")

    # 3️⃣ Nettoyage
    if os.path.exists(temp_tiff):
        os.remove(temp_tiff)

    return output_pdf

