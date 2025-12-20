import json
import logging
import csv
import os
import uuid
from typing import Any, Dict, List, Optional
import anthropic
from app.config import settings
from app.services.db_service import db_service
from app.models.request_models import AdvancedFilterRequest
from app.services.log_service import LogCollector

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.tools = [
            {
                "name": "filter_profiles_tool",
                "description": "Filter LinkedIn profiles using complex filters.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string"},
                        "location": {"type": "string"},
                        "gender": {"type": "string"},
                        "min_age": {"type": "integer"},
                        "max_age": {"type": "integer"},
                        "education": {"type": "string"},
                        "limit": {"type": "integer"}
                    }
                }
            },
            {
                "name": "export_csv_tool",
                "description": "Export profiles to CSV format. Use this whenever the user asks to save, download, or export data to CSV.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "profiles": {"type": "array"},
                        "filename": {"type": "string"}
                    },
                    "required": ["profiles"]
                }
            },
            {
                "name": "get_profile_by_name_tool",
                "description": "Retrieve a profile by exact name.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        ]
        
        # Ensure exports directory exists
        self.export_dir = "exports"
        os.makedirs(self.export_dir, exist_ok=True)

    def filter_profiles_tool(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply advanced filters and optional limit."""
        LogCollector.add(f"🛠️ Tool Call: filter_profiles_tool with filters: {filters}")
        # Remove keys that are None or not in the model
        valid_keys = AdvancedFilterRequest.model_fields.keys()
        clean_filters = {k: v for k, v in filters.items() if k in valid_keys}
        req = AdvancedFilterRequest(**clean_filters)
        results = db_service.advanced_filter_profiles(req)
        LogCollector.add(f"   ✅ Found {len(results)} profiles.")
        return results

    def export_csv_tool(self, profiles: List[Dict[str, Any]], filename: str = "filtered_profiles.csv") -> Dict[str, Any]:
        """
        Generate a CSV file from profiles.
        """
        LogCollector.add(f"🛠️ Tool Call: export_csv_tool with {len(profiles)} profiles.")
        
        if not filename.endswith('.csv'):
            filename += '.csv'
            
        # Generate unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(self.export_dir, unique_filename)
        
        try:
            fieldnames = ["name", "profile_url", "location", "gender", "age", "education", "position"]
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                for row in profiles:
                    # Flatten education for CSV
                    row_copy = row.copy()
                    if isinstance(row_copy.get("education"), list):
                        row_copy["education"] = "; ".join([f"{e.get('school')} ({e.get('degree')})" for e in row_copy.get("education", [])])
                    writer.writerow(row_copy)
            
            LogCollector.add(f"   💾 CSV saved to {filepath}")
            return {
                "status": "success", 
                "count": len(profiles), 
                "filename": unique_filename,
                "download_url": f"/agent/download/{unique_filename}"
            }
            
        except Exception as e:
            LogCollector.add(f"   ❌ Failed to export CSV: {e}")
            return {"status": "error", "error": str(e)}

    def get_profile_by_name_tool(self, name: str) -> Optional[Dict[str, Any]]:
        LogCollector.add(f"🛠️ Tool Call: get_profile_by_name_tool for '{name}'")
        result = db_service.get_profile_by_name(name)
        if result:
            LogCollector.add(f"   ✅ Profile found.")
        else:
            LogCollector.add(f"   ⚠️ Profile not found.")
        return result

    async def process_prompt(self, prompt: str) -> Dict[str, Any]:
        messages = [{"role": "user", "content": prompt}]
        tool_outputs = []
        
        LogCollector.add("🤔 Agent is thinking...")
        
        try:
            for turn in range(5): # Max 5 turns to prevent infinite loops
                response = self.client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    tools=self.tools,
                    messages=messages
                )
                
                has_tool_use = False
                tool_results_for_claude = []
                
                # Check for tool uses in this response
                for block in response.content:
                    if block.type == "tool_use":
                        has_tool_use = True
                        break
                
                # If no tool use, we are done. Return the text response.
                if not has_tool_use:
                    final_response = ""
                    for block in response.content:
                        if block.type == "text":
                            final_response += block.text
                            LogCollector.add(f"📝 Answer: {block.text}")
                    
                    return {
                        "response": final_response,
                        "tool_outputs": tool_outputs
                    }
                
                # Handle tool uses
                messages.append({"role": "assistant", "content": response.content})
                
                for block in response.content:
                    if block.type == "text":
                        LogCollector.add(f"💭 Reasoning: {block.text}")
                    elif block.type == "tool_use":
                        tool_name = block.name
                        args = block.input
                        tool_id = block.id
                        
                        result = None
                        if tool_name == "filter_profiles_tool":
                            result = self.filter_profiles_tool(args)
                        elif tool_name == "export_csv_tool":
                            result = self.export_csv_tool(args.get("profiles", []), args.get("filename", "filtered_profiles.csv"))
                        elif tool_name == "get_profile_by_name_tool":
                            result = self.get_profile_by_name_tool(args["name"])
                        
                        tool_outputs.append({
                            "tool": tool_name,
                            "result": result
                        })
                        
                        # For Claude, we need to serialize the result
                        # Truncate very long results to save tokens if needed, but for now pass full
                        tool_results_for_claude.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result, ensure_ascii=False, default=str)
                        })
                
                # Append tool results to messages for the next turn
                messages.append({
                    "role": "user",
                    "content": tool_results_for_claude
                })
            
            return {
                "response": "⚠️ Agent reached maximum turn limit.",
                "tool_outputs": tool_outputs
            }

        except Exception as e:
            logger.error(f"Agent error: {e}")
            LogCollector.add(f"❌ Agent Error: {e}")
            return {"error": str(e)}
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
            LogCollector.add(f"❌ Agent Error: {e}")
            return {"error": str(e)}

agent_service = AgentService()

