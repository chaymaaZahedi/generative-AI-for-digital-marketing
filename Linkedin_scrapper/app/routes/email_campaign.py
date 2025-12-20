from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services import email_service
import shutil
import os
import tempfile

router = APIRouter(prefix="/email", tags=["Email Campaign"])

@router.post("/send")
async def send_campaign(
    subject: str = Form(...),
    message: str = Form(...),
    csv_file: UploadFile = File(...),
    image_file: UploadFile = File(None)
):
    # Create a temporary directory to store uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save CSV file
        csv_path = os.path.join(temp_dir, csv_file.filename)
        with open(csv_path, "wb") as buffer:
            shutil.copyfileobj(csv_file.file, buffer)
            
        # Save Image file if provided
        image_path = None
        if image_file:
            image_path = os.path.join(temp_dir, image_file.filename)
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image_file.file, buffer)
        
        # Process campaign
        result = email_service.process_email_campaign(
            subject=subject,
            message=message,
            csv_file_path=csv_path,
            image_file_path=image_path
        )
        
        return result
