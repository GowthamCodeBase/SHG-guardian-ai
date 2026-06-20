from core.observability import ObservabilityManager
from core.a2a_protocol import AgentMessage
from memory.session_memory import SessionMemory
from typing import Dict, Any, List

class EvaluatorAgent:
    def __init__(self):
        self.name = "EvaluatorAgent"

    def audit_and_synthesize(self, ledger_month: str) -> Dict[str, Any]:
        """Audits intermediate worker results and creates a final executive summary."""
        ObservabilityManager.log_event(self.name, f"Auditing workflow processing results for {ledger_month}.")

        ledger = SessionMemory.get_ledger()
        risk_scores = SessionMemory.get_risk_scores()
        recovery_rates = SessionMemory.get_recovery_rates()
        anomalies = SessionMemory.get_anomalies()
        recommendations = SessionMemory.get_approval_recommendations()
        recovery_output = SessionMemory.get_agent_outputs().get("RecoveryAnalysisAgent", {})

        # 1. Integrity check: Verify that calculations were completed
        total_members = len(ledger)
        total_risks_evaluated = len(risk_scores)
        total_rates_computed = len(recovery_rates)

        issues = []
        if total_risks_evaluated != total_members:
            issues.append(f"Risk evaluation count discrepancy: {total_risks_evaluated} risks evaluated vs. {total_members} ledger entries.")
        if total_rates_computed != total_members:
            issues.append(f"Recovery computation count discrepancy: {total_rates_computed} rates calculated vs. {total_members} ledger entries.")

        # 2. Risk aggregation
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        
        for mid, data in risk_scores.items():
            cat = data.get("category", "LOW")
            if cat == "HIGH":
                high_risk_count += 1
            elif cat == "MEDIUM":
                medium_risk_count += 1
            else:
                low_risk_count += 1

        # 3. Sort high-risk members for immediate attention
        top_risk_members = []
        for mid, data in risk_scores.items():
            top_risk_members.append({
                "member_id": mid,
                "score": data.get("score", 0.0),
                "category": data.get("category", "LOW")
            })
        top_risk_members.sort(key=lambda x: x["score"], reverse=True)
        top_focus = top_risk_members[:3]

        # 4. Synthesize final report structure
        overall_rate = recovery_output.get("overall_recovery_rate", 0.0)
        total_collected = recovery_output.get("total_collected", 0.0)
        total_due = recovery_output.get("total_due", 0.0)

        status = "COMPLETED"
        if len(anomalies) > 0 or len(issues) > 0:
            status = "COMPLETED_WITH_WARNINGS"
        if high_risk_count > 0:
            status = "CRITICAL_ACTION_REQUIRED"

        report = {
            "status": status,
            "ledger_month": ledger_month,
            "total_members": total_members,
            "overall_recovery_rate": overall_rate,
            "total_collected": total_collected,
            "total_due": total_due,
            "risk_distribution": {
                "HIGH": high_risk_count,
                "MEDIUM": medium_risk_count,
                "LOW": low_risk_count
            },
            "anomalies_flagged": len(anomalies),
            "escalations_generated": len(recommendations),
            "top_focus_members": top_focus,
            "integrity_checks": {
                "passed": len(issues) == 0,
                "discrepancies": issues
            }
        }

        SessionMemory.set_final_report(report)

        ObservabilityManager.log_event(
            self.name, 
            f"Final report generated with status: {status}. Evaluator audit passed.",
            "ERROR" if status == "CRITICAL_ACTION_REQUIRED" else "SUCCESS"
        )
        return report
