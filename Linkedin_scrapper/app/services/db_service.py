
import sqlite3
import json
import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = settings.DB_FILE):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        url TEXT,
                        location TEXT,
                        keyword TEXT,
                        position TEXT,
                        gender TEXT,
                        image_url TEXT,
                        search_rank INTEGER,
                        estimated_age INTEGER,
                        education TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def to_json_string(self, value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return value

    def save_profiles(self, profiles: List[Dict[str, Any]]):
        """Save a list of profiles to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for p in profiles:
                    cursor.execute("""
                        INSERT INTO profiles (
                            name, url, location, keyword, position,
                            gender, image_url, search_rank, estimated_age, education
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p.get("name"),
                        p.get("url"),
                        p.get("location"),
                        p.get("keyword"),
                        p.get("position"),
                        p.get("gender"),
                        p.get("image_url"),
                        p.get("search_rank"),
                        p.get("estimated_age"),
                        self.to_json_string(p.get("education"))
                    ))
                conn.commit()
            logger.info(f"💾 Saved {len(profiles)} profiles to database.")
        except Exception as e:
            logger.error(f"Failed to save profiles to database: {e}")
            raise

    def advanced_filter_profiles(self, filters: Any) -> List[Dict[str, Any]]:
        """Filter profiles with advanced options."""
        try:
            query = "SELECT * FROM profiles WHERE 1=1"
            params = []

            if filters.keyword:
                query += " AND (name LIKE ? OR position LIKE ? OR keyword LIKE ?)"
                kw = f"%{filters.keyword}%"
                params.extend([kw, kw, kw])

            if filters.location and filters.location.lower() != "morocco":
                query += " AND location LIKE ?"
                params.append(f"%{filters.location}%")

            if filters.gender and filters.gender.lower() not in ["any", ""]:
                query += " AND gender = ?"
                params.append(filters.gender.lower().capitalize())

            if filters.min_age is not None:
                query += " AND estimated_age >= ?"
                params.append(filters.min_age)

            if filters.max_age is not None:
                query += " AND estimated_age <= ?"
                params.append(filters.max_age)

            if filters.education:
                query += " AND education LIKE ?"
                params.append(f"%{filters.education}%")

            if hasattr(filters, 'limit') and filters.limit:
                query += f" LIMIT {filters.limit}"

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    results.append({
                        "name": row["name"],
                        "profile_url": row["url"],
                        "location": row["location"],
                        "gender": row["gender"],
                        "age": row["estimated_age"],
                        "education": json.loads(row["education"]) if row["education"] else [],
                        "position": row["position"],
                        "image_url": row["image_url"]
                    })
                
                return results
        except Exception as e:
            logger.error(f"Failed to filter profiles: {e}")
            raise

    def get_profile_by_name(self, name: str) -> Dict[str, Any]:
        """Find profile by exact name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM profiles WHERE name=? LIMIT 1", (name,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "name": row["name"],
                        "profile_url": row["url"],
                        "location": row["location"],
                        "gender": row["gender"],
                        "age": row["estimated_age"],
                        "education": json.loads(row["education"]) if row["education"] else [],
                        "position": row["position"],
                        "image_url": row["image_url"]
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get profile by name: {e}")
            raise

db_service = DatabaseService()
