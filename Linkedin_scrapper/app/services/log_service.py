
from typing import List
import datetime

class LogCollector:
    _logs: List[str] = []

    @classmethod
    def add(cls, message: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        cls._logs.append(log_entry)
        print(log_entry)  # Also print to console

    @classmethod
    def get_logs(cls) -> List[str]:
        return cls._logs

    @classmethod
    def clear(cls):
        cls._logs = []
