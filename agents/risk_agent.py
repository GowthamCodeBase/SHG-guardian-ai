from core.observability import ObservabilityManager
from core.a2a_protocol import AgentMessage
from tools.calculator_tool import CalculatorTool
from memory.session_memory import SessionMemory
from memory.database import DatabaseManager
from typing import Dict, Any, List

class RiskAssessmentAgent:
    def __init__(self):
        self.name = "RiskAssessmentAgent"

    def execute_task(self, message: AgentMessage) -> Dict[str, Any]:
        """Runs risk evaluation on the provided dataset."""
        payload = message.payload
        month = payload.get("ledger_month", "Unknown")
        records = payload.get("records", [])
        
        ObservabilityManager.log_event(self.name, f"Evaluating financial risk scores for {len(records)} members for {month}.")
        
        results = {}
        
        for record in records:
            member_id = record.get("member_id")
            if not member_id:
                continue

            try:
                savings = float(record.get("savings", 0.0))
                outstanding = float(record.get("outstanding_loan", 0.0))
                monthly_due = float(record.get("monthly_due", 0.0))
                actual_paid = float(record.get("actual_paid", 0.0))
                missed = int(record.get("missed_payments", 0))
            except (ValueError, TypeError):
                # Anomaly agent will flag formatting, risk agent uses safe default zero values
                savings, outstanding, monthly_due, actual_paid, missed = 0.0, 0.0, 0.0, 0.0, 0
            
            # Risk Scoring Logic (Scale 0-100)
            score = 0.0
            reasons = []

            # 1. Missed Payments Risk (up to 40 points)
            if missed > 0:
                points = min(40, missed * 10)
                score += points
                reasons.append(f"Missed {missed} payments (+{points} pts)")
            
            # 2. Debt-to-Savings Risk (up to 30 points)
            ratio = CalculatorTool.calculate_outstanding_to_savings_ratio(outstanding, savings)
            if ratio > 4.0:
                score += 30
                reasons.append(f"Outstanding loan exceeds savings by {ratio:.1f}x (+30 pts)")
            elif ratio > 2.0:
                score += 15
                reasons.append(f"Outstanding loan exceeds savings by {ratio:.1f}x (+15 pts)")
            
            # 3. Repayment Recovery Risk (up to 30 points)
            recovery_rate = CalculatorTool.calculate_recovery_rate(actual_paid, monthly_due)
            if recovery_rate < 0.50 and monthly_due > 0:
                score += 30
                reasons.append(f"Critical low recovery rate of {recovery_rate * 100:.1f}% (+30 pts)")
            elif recovery_rate < 0.80 and monthly_due > 0:
                score += 15
                reasons.append(f"Under-repayment rate of {recovery_rate * 100:.1f}% (+15 pts)")

            # Check historical database context
            history = DatabaseManager.get_member_history(member_id)
            past_risks = history.get("risks", [])
            if len(past_risks) > 0:
                last_score = past_risks[0].get("risk_score", 0.0)
                if last_score >= 60 and score >= 60:
                    score = min(100.0, score + 10)
                    reasons.append("Persistent high-risk trend over consecutive cycles (+10 pts)")

            score = min(100.0, max(0.0, score))
            
            # Categorize Risk Level
            if score >= 70:
                category = "HIGH"
            elif score >= 40:
                category = "MEDIUM"
            else:
                category = "LOW"
                
            reason_str = "; ".join(reasons) if reasons else "Healthy account profile."
            
            results[member_id] = {
                "risk_score": score,
                "risk_category": category,
                "reasons": reason_str
            }
            
            # Save output to Session Memory
            SessionMemory.set_risk_score(member_id, score, category)
            
            # Persist to Long-Term database memory
            DatabaseManager.save_risk_record(member_id, score, category, reason_str)
            
        ObservabilityManager.log_event(self.name, "Risk analysis finished. Saved profiles to SQLite and Session Memory.", "SUCCESS")
        return results
