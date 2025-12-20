import csv
import logging
from typing import List, Set
from enum import Enum
from app.config import settings

logger = logging.getLogger(__name__)

def load_locations() -> List[str]:
    """
    Loads location names from the CSV file defined in settings.
    Returns a list of location names (cities).
    """
    locations = []
    try:
        with open(settings.LOCATION_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'name' in row:
                    locations.append(row['name'].strip())
    except FileNotFoundError:
        logger.error(f"Location CSV file not found at {settings.LOCATION_CSV_PATH}")
    except Exception as e:
        logger.error(f"Error reading location CSV: {e}")
    
    return locations

# Load locations once at module level
AVAILABLE_LOCATIONS = load_locations()

def get_location_enum():
    """
    Creates a dynamic Enum for locations to be used in Pydantic models.
    This helps with Swagger UI documentation.
    """
    if not AVAILABLE_LOCATIONS:
        # Fallback if no locations loaded
        return Enum('LocationEnum', {'UNKNOWN': 'unknown'})
    
    # Create a dict for Enum creation: {'CASABLANCA': 'casablanca', ...}
    # Using the name as both key (upper case) and value
    enum_dict = {loc.upper().replace(' ', '_').replace('-', '_').replace("'", ""): loc for loc in AVAILABLE_LOCATIONS}
    return Enum('LocationEnum', enum_dict, type=str)

LocationEnum = get_location_enum()
