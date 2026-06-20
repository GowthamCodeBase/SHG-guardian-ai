import os
import datetime
from typing import List, Dict, Any

class ObservabilityManager:
    _logs: List[Dict[str, Any]] = []
    
    # Define absolute logs path in workspace
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    LOG_FILE = os.path.join(LOG_DIR, "agent_workflow.log")

    @classmethod
    def log_event(cls, agent_name: str, message: str, status: str = "INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "message": message,
            "status": status
        }
        cls._logs.append(log_entry)
        
        # Ensure log directory exists
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        
        # Write to log file
        log_line = f"{timestamp} [{status}] [{agent_name}]: {message}\n"
        try:
            with open(cls.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"Failed to write log: {e}")
            
        print(f"[{timestamp}] [{status}] [{agent_name}] {message}")

    @classmethod
    def get_logs(cls) -> List[Dict[str, Any]]:
        return cls._logs

    @classmethod
    def clear_logs(cls):
        cls._logs.clear()
