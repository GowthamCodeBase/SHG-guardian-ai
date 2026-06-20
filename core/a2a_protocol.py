import datetime
from typing import Dict, Any

class AgentMessage:
    def __init__(self, sender: str, receiver: str, task_type: str, payload: Dict[str, Any], status: str = "PENDING"):
        self.sender = sender
        self.receiver = receiver
        self.task_type = task_type
        self.payload = payload
        self.status = status
        self.timestamp = datetime.datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "task_type": self.task_type,
            "payload": self.payload,
            "status": self.status,
            "timestamp": self.timestamp
        }

    def update_status(self, status: str):
        self.status = status

    def __repr__(self):
        return f"AgentMessage(from={self.sender}, to={self.receiver}, task={self.task_type}, status={self.status})"
