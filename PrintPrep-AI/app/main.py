from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
from app.utils.metadata import read_metadata
from app.utils.upscaling_realesrgan import upscale_image_realesrgan
from app.utils.cleaning import clean_image
from app.utils.dpi_check import check_upscale
from app.utils.upscaling_with_Lanczos import upscale_lanczos
from app.utils.export_pdf_x1a import convert_tiff_to_pdfx1a

app = FastAPI()

# Mount static files to serve uploaded and upscaled images
app.mount("/temp_uploads", StaticFiles(directory="temp_uploads"), name="temp_uploads")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Ensure temp_uploads exists
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_image(request: Request, file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        metadata = read_metadata(file_location)
        
        return templates.TemplateResponse("result.html", {
            "request": request,
            "filename": file.filename,
            "metadata": metadata
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": str(e)
        })

@app.post("/upscale", response_class=HTMLResponse)
async def upscale_image(request: Request, filename: str = Form(...)):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # Upscale the image
        upscaled_path = upscale_image_realesrgan(file_path, UPLOAD_DIR, outscale=6)
        upscaled_filename = os.path.basename(upscaled_path)
        
        # Get metadata for the upscaled image (Result)
        metadata = read_metadata(upscaled_path)

        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": filename,
            "upscaled_filename": upscaled_filename,
            "metadata": metadata,
            "title": "Upscaling Complete",
            "subtitle": "Your image has been successfully upscaled by 600%",
            "icc_profiles": get_icc_profiles()
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Upscaling failed: {str(e)}"
        })

@app.post("/enhance", response_class=HTMLResponse)
async def enhance_image(request: Request, filename: str = Form(...), original_filename: str = Form(...)):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # Clean the image (Enhancement)
        cleaned_filename = f"enhanced_{filename}"
        cleaned_path = os.path.join(UPLOAD_DIR, cleaned_filename)
        clean_image(file_path, cleaned_path)
        
        # Get metadata for the enhanced image (Result)
        metadata = read_metadata(cleaned_path)

        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": filename, # Compare against the input (upscaled) image
            "upscaled_filename": cleaned_filename, # The result is the enhanced image
            "metadata": metadata,
            "title": "Enhancement Complete",
            "subtitle": "Your image has been denoised and sharpened",
            "show_print_options": True,
            "icc_profiles": get_icc_profiles()
        })
    except Exception as e:
        # Fallback to the current page if enhancement fails
        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": original_filename,
            "upscaled_filename": filename,
            "metadata": read_metadata(os.path.join(UPLOAD_DIR, original_filename)),
            "error": f"Enhancement failed: {str(e)}"
        })

@app.post("/check_print")
async def check_print_quality(
    request: Request,
    filename: str = Form(...),
    width_m: float = Form(...),
    height_m: float = Form(...),
    support_type: str = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, filename)
    try:
        # Run the DPI check
        # Note: check_upscale prints to stdout if display=True, but returns a dict
        results = check_upscale(file_path, width_m, height_m, support_type, display=False)
        
        # Map backend results to frontend expectations
        response_data = {
            "current_dpi_x": results["DPI X"],
            "current_dpi_y": results["DPI Y"],
            "scale_factor_needed": results["Upscale factor suggested"],
            "upscale_needed": results["Upscale factor suggested"] > 1.0,
            "recommended_dpi": results["Recommended DPI"]
        }
        
        # Return JSON for the frontend to handle
        return response_data
    except Exception as e:
        return {"error": str(e)}

@app.post("/upscale_lanczos", response_class=HTMLResponse)
async def upscale_lanczos_route(
    request: Request, 
    filename: str = Form(...), 
    scale_factor: float = Form(...),
    original_filename: str = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # Perform Lanczos upscaling
        lanczos_filename = f"lanczos_{filename}"
        lanczos_path = os.path.join(UPLOAD_DIR, lanczos_filename)
        
        upscale_lanczos(file_path, lanczos_path, scale_factor=scale_factor)
        
        # Get metadata for the new image
        metadata = read_metadata(lanczos_path)
        
        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": original_filename, # Keep original for comparison? Or use the input filename?
            # Let's keep the very first original for comparison if possible, or the one passed in.
            # The user flow implies we are refining the result.
            "upscaled_filename": lanczos_filename,
            "metadata": metadata,
            "title": "Lanczos Upscaling Complete",
            "subtitle": f"Your image has been resized by x{scale_factor}",
            "show_print_options": True,
            "icc_profiles": get_icc_profiles()
        })
    except Exception as e:
         return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": original_filename,
            "upscaled_filename": filename,
            "metadata": read_metadata(file_path),
            "error": f"Lanczos upscaling failed: {str(e)}"
        })

# --- Soft Proofing ---
from app.utils.soft_proof import soft_proof_rgb
from app.utils.color_conversion import convert_to_cmyk
import glob

def get_icc_profiles():
    """Returns a list of available ICC profile names."""
    profiles_dir = os.path.join("app", "utils", "profiles")
    if not os.path.exists(profiles_dir):
        return []
    profiles = glob.glob(os.path.join(profiles_dir, "*.icc"))
    return [os.path.basename(p) for p in profiles]

@app.post("/soft_proof", response_class=HTMLResponse)
async def soft_proof_route(
    request: Request,
    filename: str = Form(...),
    original_filename: str = Form(...),
    icc_profile: str = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, filename)
    profile_path = os.path.join("app", "utils", "profiles", icc_profile)
    
    try:
        # Generate soft proof
        # We'll prefix the filename to avoid overwriting if possible, or just overwrite a preview file
        # But for unique sessions/files, let's append _proof
        proof_filename = f"proof_{filename}"
        proof_path = os.path.join(UPLOAD_DIR, proof_filename)
        
        soft_proof_rgb(file_path, cmyk_profile_path=profile_path, output_path=proof_path)
        
        # Get metadata
        metadata = read_metadata(proof_path)
        
        # We return the upscale_result page, but now the "upscaled_filename" is the proof.
        # This effectively replaces the "Upscaled" view with the "Soft Proof" view.
        # The user can still download it.
        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": original_filename,
            "upscaled_filename": proof_filename,
            "source_filename": filename, # Pass the source file for final conversion
            "metadata": metadata,
            "title": "Soft Proofing Preview",
            "subtitle": f"Simulated print result using {icc_profile}",
            "show_print_options": True,
            "icc_profiles": get_icc_profiles(), # Pass profiles again
            "selected_profile": icc_profile
        })
    except Exception as e:
        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": original_filename,
            "upscaled_filename": filename,
            "metadata": read_metadata(file_path),
            "error": f"Soft proofing failed: {str(e)}",
            "show_print_options": True,
            "icc_profiles": get_icc_profiles()
        })

@app.post("/convert_cmyk", response_class=HTMLResponse)
async def convert_cmyk_route(
    request: Request,
    filename: str = Form(...), # This should be the high-res source file
    icc_profile: str = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, filename)
    profile_path = os.path.join("app", "utils", "profiles", icc_profile)
    
    try:
        # Output filename for CMYK
        cmyk_filename = f"cmyk_{filename.rsplit('.', 1)[0]}.tiff"
        output_path = os.path.join(UPLOAD_DIR, cmyk_filename)
        
        convert_to_cmyk(file_path, output_path, cmyk_profile_path=profile_path)
        
        # Get metadata of the new CMYK file
        metadata = read_metadata(output_path)
        
        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": filename, # The source was the input
            "upscaled_filename": cmyk_filename, # Show the CMYK result (browser might not display TIFF well, but we provide download)
            "metadata": metadata,
            "title": "CMYK Conversion Complete",
            "subtitle": f"Converted using {icc_profile}",
            "show_print_options": False, # No need to check quality again? Or maybe yes?
            "cmyk_download": cmyk_filename,
            "icc_profiles": get_icc_profiles()
        })
    except Exception as e:
        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": filename,
            "upscaled_filename": filename,
            "metadata": read_metadata(file_path),
            "error": f"CMYK conversion failed: {str(e)}",
            "show_print_options": True,
            "icc_profiles": get_icc_profiles()
        })

@app.post("/export_pdfx1a", response_class=HTMLResponse)
async def export_pdfx1a_route(
    request: Request,
    filename: str = Form(...), # This is the CMYK TIFF
    icc_profile: str = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, filename)
    profile_path = os.path.join("app", "utils", "profiles", icc_profile)
    
    try:
        # Output filename for PDF
        # filename is likely something like cmyk_input.tiff
        base_name = filename.rsplit('.', 1)[0]
        pdf_filename = f"{base_name}.pdf"
        output_path = os.path.join(UPLOAD_DIR, pdf_filename)
        
        convert_tiff_to_pdfx1a(file_path, output_path, icc_profile_path=profile_path)
        
        # Get metadata
        metadata = read_metadata(file_path) # Metadata of the CMYK file
        
        return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            "original_filename": filename, # Show the CMYK as "original" in context if needed, or just keep flow
            # Actually, standard flow: Compare input vs result?
            # Here we are just downloading. The view doesn't change much.
            "upscaled_filename": filename, 
            "metadata": metadata,
            "title": "PDF/X-1a Export Complete",
            "subtitle": f"Exported using {icc_profile} Output Intent",
            "show_print_options": False,
            "cmyk_download": filename,
            "pdf_download": pdf_filename,
            "icc_profiles": get_icc_profiles()
        })
    except Exception as e:
         return templates.TemplateResponse("upscale_result.html", {
            "request": request,
            # We need to recover the previous state if possible, but we might lose some context
            # assuming filename is the cmyk file
            "upscaled_filename": filename,
            "original_filename": filename, 
            "metadata": read_metadata(file_path),
            "error": f"PDF Export failed: {str(e)}",
            "cmyk_download": filename,
            "icc_profiles": get_icc_profiles()
        })
