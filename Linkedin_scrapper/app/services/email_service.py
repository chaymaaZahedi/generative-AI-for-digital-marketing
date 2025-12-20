import smtplib
import os
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
EMAIL_SENDER = os.getenv("EMAIL_EXPEDITEUR", "amina.bamo11@gmail.com")
EMAIL_PASSWORD = os.getenv("MOT_DE_PASSE", "cbpwzhophnkeybhs")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

def read_emails_csv(file_path: str) -> Dict:
    """
    Reads email addresses from a CSV file.
    Expected column: 'email_adress'
    """
    try:
        if not os.path.exists(file_path):
            return {"error": f"File {file_path} does not exist"}
        
        emails = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize keys to handle potential whitespace or case issues if needed
                # For now, strictly following the user's provided script which looks for 'email_adress'
                if 'email_adress' in row and row['email_adress']:
                    emails.append({
                        'email': row['email_adress'],
                        'data': row
                    })
        
        return {"count": len(emails), "emails": emails}
    
    except Exception as e:
        return {"error": f"Error reading CSV: {str(e)}"}

def send_email_with_image(
    recipient_email: str,
    subject: str,
    message_template: str,
    image_path: Optional[str] = None,
    personalization_data: Dict = None
) -> str:
    """
    Sends a personalized email with an optional image attachment.
    """
    try:
        # Personalize message
        message = message_template
        if personalization_data:
            for key, value in personalization_data.items():
                placeholder = f"{{{key}}}"
                if placeholder in message:
                    message = message.replace(placeholder, str(value))
        
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Attach image if provided
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as img_file:
                img = MIMEImage(img_file.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                msg.attach(img)
        elif image_path:
             return f"⚠️ Warning: Image {image_path} does not exist"

        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return f"✅ Email sent to {recipient_email}"
    
    except Exception as e:
        return f"❌ Error sending to {recipient_email}: {str(e)}"

def process_email_campaign(
    subject: str,
    message: str,
    csv_file_path: str,
    image_file_path: Optional[str] = None
) -> Dict:
    """
    Processes the email campaign: reads CSV and sends emails.
    """
    read_result = read_emails_csv(csv_file_path)
    
    if "error" in read_result:
        return read_result
    
    emails_data = read_result["emails"]
    total = len(emails_data)
    success_count = 0
    failures = []
    
    for data in emails_data:
        email = data['email']
        result = send_email_with_image(
            recipient_email=email,
            subject=subject,
            message_template=message,
            image_path=image_file_path,
            personalization_data=data['data']
        )
        
        if "✅" in result:
            success_count += 1
        else:
            failures.append(f"{email}: {result}")
            
    return {
        "status": "completed",
        "total": total,
        "success_count": success_count,
        "failure_count": len(failures),
        "failures": failures
    }
