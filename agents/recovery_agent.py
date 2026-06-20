from core.observability import ObservabilityManager
from core.a2a_protocol import AgentMessage
from tools.calculator_tool import CalculatorTool
from memory.session_memory import SessionMemory
from typing import Dict, Any, List

class RecoveryAnalysisAgent:
    def __init__(self):
        self.name = "RecoveryAnalysisAgent"

    def execute_task(self, message: AgentMessage) -> Dict[str, Any]:
        """Runs recovery metrics calculations."""
        payload = message.payload
        month = payload.get("ledger_month", "Unknown")
        records = payload.get("records", [])
        
        ObservabilityManager.log_event(self.name, f"Calculating collection performance for {month}.")
        
        total_collected = 0.0
        total_due = 0.0
        total_outstanding = 0.0
        total_savings = 0.0
        
        individual_rates = {}
        
        for record in records:
            member_id = record.get("member_id")
            if not member_id:
                continue
                
            try:
                savings = float(record.get("savings", 0.0))
                outstanding = float(record.get("outstanding_loan", 0.0))
                due = float(record.get("monthly_due", 0.0))
                paid = float(record.get("actual_paid", 0.0))
            except (ValueError, TypeError):
                savings, outstanding, due, paid = 0.0, 0.0, 0.0, 0.0
                
            rate = CalculatorTool.calculate_recovery_rate(paid, due)
            individual_rates[member_id] = rate
            SessionMemory.set_recovery_rate(member_id, rate)
            
            total_collected += paid
            total_due += due
            total_outstanding += outstanding
            total_savings += savings
            
        overall_rate = CalculatorTool.calculate_recovery_rate(total_collected, total_due)
        
        summary = {
            "ledger_month": month,
            "total_collected": total_collected,
            "total_due": total_due,
            "total_outstanding": total_outstanding,
            "total_savings": total_savings,
            "overall_recovery_rate": overall_rate,
            "individual_rates": individual_rates
        }
        
        SessionMemory.set_agent_output(self.name, summary)
        
        ObservabilityManager.log_event(
            self.name, 
            f"Recovery summary generated: Overall Recovery Rate: {overall_rate * 100:.2f}% | Total Collected: {total_collected:.2f} | Total Due: {total_due:.2f}",
            "SUCCESS"
        )
        
        return summary
