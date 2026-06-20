from core.observability import ObservabilityManager
from core.a2a_protocol import AgentMessage
from memory.session_memory import SessionMemory
from memory.database import DatabaseManager
from typing import Dict, Any, List

class ApprovalAgent:
    def __init__(self):
        self.name = "ApprovalAgent"

    def execute_task(self, message: AgentMessage) -> List[Dict[str, Any]]:
        """Processes outputs to compile escalation proposals."""
        payload = message.payload
        month = payload.get("ledger_month", "Unknown")
        records = payload.get("records", [])
        
        ObservabilityManager.log_event(self.name, f"Generating approval recommendations for {month}.")
        
        risk_scores = SessionMemory.get_risk_scores()
        recovery_rates = SessionMemory.get_recovery_rates()
        anomalies = SessionMemory.get_anomalies()
        
        recommendations = []
        
        # Identify members that need escalation
        # Criteria: High Risk Category, Missed Payments >= 4, or critical data anomalies
        for record in records:
            member_id = record.get("member_id")
            if not member_id:
                continue
                
            risk_data = risk_scores.get(member_id, {"score": 0.0, "category": "LOW"})
            score = risk_data.get("risk_score", risk_data.get("score", 0.0))
            category = risk_data.get("risk_category", risk_data.get("category", "LOW"))
            rec_rate = recovery_rates.get(member_id, 1.0)
            
            try:
                missed = int(record.get("missed_payments", 0))
            except (ValueError, TypeError):
                missed = 0

            escalate = False
            reasons = []
            
            if category == "HIGH":
                escalate = True
                reasons.append(f"Risk score is critically high ({score:.0f}/100)")
            
            if missed >= 3:
                escalate = True
                reasons.append(f"Member has missed {missed} consecutive payments")
                
            if rec_rate < 0.60:
                escalate = True
                reasons.append(f"Recovery collection rate dropped to {rec_rate * 100:.1f}%")

            # Check if this member is associated with any critical/high anomalies
            member_anomalies = [a for a in anomalies if a.get("member_id") == member_id and a.get("severity") in ["HIGH", "CRITICAL"]]
            if member_anomalies:
                escalate = True
                reasons.append(f"Critical data anomalies flagged: {member_anomalies[0].get('type')}")

            if escalate:
                reason_str = "; ".join(reasons)
                rec = {
                    "member_id": member_id,
                    "ledger_month": month,
                    "risk_level": category,
                    "escalation_reason": reason_str,
                    "recommended_action": "Field Verification & Financial Advisory Review" if category == "HIGH" else "Follow-up Collection Reminder"
                }
                
                recommendations.append(rec)
                SessionMemory.add_approval_recommendation(rec)
                
                # Push escalation record to SQLite approvals table
                DatabaseManager.create_approval_escalation(
                    member_id=member_id,
                    month=month,
                    risk_level=category,
                    reason=reason_str
                )
                
        ObservabilityManager.log_event(
            self.name, 
            f"Escalation screening complete. Flagged {len(recommendations)} accounts for multi-level human approval.",
            "WARNING" if recommendations else "SUCCESS"
        )
        return recommendations
