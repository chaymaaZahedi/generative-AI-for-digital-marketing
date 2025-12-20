from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.services.agent_service import agent_service
from app.services.log_service import LogCollector
import os

router = APIRouter()

class AgentRequest(BaseModel):
    prompt: str

@router.post("/agent/process")
async def process_agent_request(request: AgentRequest):
    """
    Process a natural language prompt using the agent.
    """
    try:
        LogCollector.add(f"🤖 Agent received prompt: {request.prompt}")
        
        result = await agent_service.process_prompt(request.prompt)
        
        if "error" in result:
            LogCollector.add(f"❌ Agent error: {result['error']}")
            raise HTTPException(status_code=500, detail=result['error'])
            
        LogCollector.add("✅ Agent processed request successfully")
        
        return result
        
    except Exception as e:
        LogCollector.add(f"❌ Agent error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/download/{filename}")
async def download_file(filename: str):
    """Download an exported file"""
    file_path = os.path.join("exports", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/csv'
    )
