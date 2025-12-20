
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.templating import Jinja2Templates
from app.models.request_models import ScrapeRequest
from app.services.linkedin_service import run_linkedin_workflow
from app.config import settings
from app.utils.locations import AVAILABLE_LOCATIONS
import os

from app.services.log_service import LogCollector

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(settings.BASE_DIR, "app", "templates"))

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "locations": AVAILABLE_LOCATIONS})

@router.get("/logs")
async def get_logs():
    """Get current logs"""
    return {"logs": LogCollector.get_logs()}

@router.post("/scrape/linkedin")
async def scrape_linkedin(request: ScrapeRequest):
    """
    Trigger the LinkedIn scraping workflow.
    Note: This is a long-running process.
    """
    LogCollector.clear()
    LogCollector.add(f"🚀 Starting scrape for '{request.keyword}' in '{request.location}'")
    
    try:
        results = await run_linkedin_workflow(request.keyword, request.location, request.limit)
        
        return {
            "status": "completed",
            "message": "Scraping finished successfully",
            "profiles": results.get("all_profiles", [])
        }
    except Exception as e:
        LogCollector.add(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
