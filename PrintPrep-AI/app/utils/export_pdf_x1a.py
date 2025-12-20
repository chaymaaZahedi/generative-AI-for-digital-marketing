import img2pdf
from pikepdf import Pdf, Dictionary, Name, String, Stream
from PIL import Image
from pathlib import Path
import io

Image.MAX_IMAGE_PIXELS = None

def convert_tiff_to_pdfx1a(input_tiff, output_pdf, icc_profile_path):
    input_tiff = Path(input_tiff)
    output_pdf = Path(output_pdf)
    icc_profile_path = Path(icc_profile_path)

    print("▶ Conversion TIFF → PDF/X-1a")

    # 1. Vérification du mode CMYK
    with Image.open(input_tiff) as img:
        if img.mode != "CMYK":
            raise ValueError(f"Le format PDF/X-1a exige du CMYK. Image actuelle : {img.mode}")

    # 2. TIFF → PDF via img2pdf
    pdf_bytes = img2pdf.convert(str(input_tiff))
    
    # 3. Post-traitement avec pikepdf
    with Pdf.open(io.BytesIO(pdf_bytes)) as pdf:
        
        # --- Profil ICC ---
        icc_data = icc_profile_path.read_bytes()
        # On définit les attributs du flux ICC (N=4 pour CMYK)
        icc_stream = Stream(pdf, icc_data)
        icc_stream.N = 4
        icc_stream.Alternate = Name.DeviceCMYK
        
        icc_indirect = pdf.make_indirect(icc_stream)

        # --- OutputIntent PDF/X ---
        oi = pdf.make_indirect(Dictionary(
            Type=Name.OutputIntent,
            S=Name.GTS_PDFX,
            OutputConditionIdentifier=String("FOGRA39"),
            RegistryName=String("http://www.color.org"),
            Info=String("FOGRA39 ISO 12647-2"),
            DestOutputProfile=icc_indirect
        ))
        
        pdf.Root.OutputIntents = [oi]

        # --- Métadonnées Info (Clés obligatoires PDF/X) ---
        # Utilisation de la méthode standard pour modifier le dictionnaire Info
        with pdf.open_metadata() as meta:
            pdf.docinfo["/GTS_PDFXVersion"] = "PDF/X-1:2001"
            pdf.docinfo["/GTS_PDFXConformance"] = "PDF/X-1a:2001"
            pdf.docinfo["/Trapped"] = Name.False_
            pdf.docinfo["/Title"] = "Export Print Haute Qualité"

        # --- SAUVEGARDE FINALE ---
        # C'est ici qu'on force la version 1.3 pour la conformité X-1a
        pdf.save(
            output_pdf, 
            min_version="1.3", 
            fix_metadata_version=True
        )

    print(f"✅ PDF/X-1a généré avec succès : {output_pdf.name}")

# TEST
if __name__ == "__main__":
    try:
        convert_tiff_to_pdfx1a(
            "../temp_uploads/cmyk_lanczos_enhanced_test_upscaled_x6.tiff",
            "../temp_uploads/final_print_PDFX1a.pdf",
            "profiles/UncoatedFOGRA29.icc"
        )
    except Exception as e:
        print(f"❌ Erreur : {e}")