
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import scraper, filter, agent, email_campaign
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="LinkedIn MCP Scraper")

# Include routers
app.include_router(scraper.router)
app.include_router(filter.router)
app.include_router(agent.router)
app.include_router(email_campaign.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
