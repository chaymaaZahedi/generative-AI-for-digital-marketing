
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.models.request_models import AdvancedFilterRequest
from app.services.db_service import db_service
from app.services.log_service import LogCollector
import logging
import csv
import os
import tempfile

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/filter/profiles")
async def filter_profiles(request: AdvancedFilterRequest):
    """
    Filter existing profiles from the database using advanced filters.
    """
    try:
        # Log the filter request
        log_msg = f"Applying advanced filters..."
        LogCollector.add(log_msg)
        if request.keyword: LogCollector.add(f"keyword: {request.keyword}")
        if request.location: LogCollector.add(f"location: {request.location}")
        if request.gender: LogCollector.add(f"gender: {request.gender}")
        if request.min_age or request.max_age: LogCollector.add(f"min_age: {request.min_age}, max_age: {request.max_age}")
        if request.education: LogCollector.add(f"education: {request.education}")
        
        results = db_service.advanced_filter_profiles(request)
        
        count = len(results)
        LogCollector.add("SQL query executed successfully")
        LogCollector.add(f"{count} profiles matched filters")
        
        return {
            "status": "success",
            "count": count,
            "profiles": results,
            "logs": LogCollector.get_logs()[-7:] # Return recent logs
        }
        
    except Exception as e:
        LogCollector.add(f"❌ Filter error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filter/export_csv")
async def export_csv(
    keyword: str = Query(None),
    location: str = Query(None),
    gender: str = Query(None),
    min_age: int = Query(None),
    max_age: int = Query(None),
    education: str = Query(None)
):
    """Export filtered profiles to CSV"""
    try:
        request = AdvancedFilterRequest(
            keyword=keyword,
            location=location,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
            education=education
        )
        
        results = db_service.advanced_filter_profiles(request)
        
        # Generate CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8') as tmp:
            fieldnames = ["name", "profile_url", "location", "gender", "age", "education", "position"]
            writer = csv.DictWriter(tmp, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for row in results:
                # Flatten education for CSV
                row_copy = row.copy()
                if isinstance(row_copy.get("education"), list):
                    row_copy["education"] = "; ".join([f"{e.get('school')} ({e.get('degree')})" for e in row_copy["education"]])
                writer.writerow(row_copy)
                
            tmp_path = tmp.name
            
        LogCollector.add(f"CSV file generated: filtered_profiles.csv")
        
        return FileResponse(
            tmp_path,
            media_type="text/csv",
            filename="filtered_profiles.csv"
        )
        
    except Exception as e:
        LogCollector.add(f"❌ Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
