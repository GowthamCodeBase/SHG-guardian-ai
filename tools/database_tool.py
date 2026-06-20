from memory.database import DatabaseManager
from typing import Dict, Any, List

class DatabaseTool:
    @staticmethod
    def get_member_history(member_id: str) -> Dict[str, Any]:
        """Fetches detailed profile, ledger, risk history, and approvals of a member."""
        return DatabaseManager.get_member_history(member_id)

    @staticmethod
    def query_active_approvals() -> List[Dict[str, Any]]:
        """Retrieves list of all active escalations awaiting approval."""
        return DatabaseManager.get_approval_queue()

    @staticmethod
    def log_approval_action(approval_id: int, role: str, status: str, comments: str) -> bool:
        """Approves, rejects, or updates escalation items based on human reviewer role."""
        try:
            if role.lower() in ["field_officer", "field officer"]:
                DatabaseManager.update_field_officer_approval(approval_id, status, comments)
                return True
            elif role.lower() in ["regional_coordinator", "regional coordinator", "coordinator"]:
                DatabaseManager.update_regional_coordinator_approval(approval_id, status, comments)
                return True
            return False
        except Exception as e:
            print(f"Error logging approval action: {e}")
            return False
