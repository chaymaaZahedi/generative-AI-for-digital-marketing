
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "*******")
    
    # LinkedIn Credentials
    LINKEDIN_EMAIL: str = os.getenv("LINKEDIN_EMAIL", "*********@gmail.com")
    LINKEDIN_PASSWORD: str = os.getenv("LINKEDIN_PASSWORD", "*********")
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MCP_SERVER_SCRIPT: str = os.path.join(BASE_DIR, "linkedin_mcp_server.py")
    LOCATION_CSV_PATH: str = os.path.join(BASE_DIR, "location_id.csv")
    
    # Output
    JSON_OUTPUT_FILE: str = os.path.join(BASE_DIR, "linkedin_profiles_age.json")
    DB_FILE: str = os.path.join(BASE_DIR, "linkedin_profiles.db")

settings = Settings()
