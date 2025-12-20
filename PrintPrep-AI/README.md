# Image Generation and Upscaling Project

This project provides a web interface for upscaling and enhancing images using various techniques (RealESRGAN, Lanczos) and preparing them for print (CMYK conversion, PDF/X-1a export).

## Features
- Image Upload
- Upscaling (RealESRGAN, Lanczos)
- Image Enhancement (Denoising, Sharpening)
- Print Quality Check (DPI calculation)
- Soft Proofing (ICC Profiles)
- CMYK Conversion
- PDF/X-1a Export

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
uvicorn app.main:app --reload
```

Access the web interface at `http://127.0.0.1:8000`.

## Directory Structure
- `app/`: Main application code.
  - `main.py`: Application entry point.
  - `templates/`: HTML templates.
  - `utils/`: Utility scripts for image processing.
- `temp_uploads/`: Temporary directory for uploaded and processed images.
