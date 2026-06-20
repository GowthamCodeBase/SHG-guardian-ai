from core.observability import ObservabilityManager
from core.a2a_protocol import AgentMessage
from memory.session_memory import SessionMemory
from typing import Dict, Any, List

class AnomalyDetectionAgent:
    def __init__(self):
        self.name = "AnomalyDetectionAgent"

    def execute_task(self, message: AgentMessage) -> List[Dict[str, Any]]:
        """Processes records to detect data anomalies."""
        payload = message.payload
        month = payload.get("ledger_month", "Unknown")
        records = payload.get("records", [])
        
        ObservabilityManager.log_event(self.name, f"Running anomaly screening on {len(records)} records.")
        
        anomalies = []
        seen_members = set()
        
        for index, record in enumerate(records):
            member_id = record.get("member_id")
            
            # 1. Missing Member ID Check
            if not member_id:
                anomaly = {
                    "row": index + 1,
                    "member_id": "MISSING",
                    "type": "Missing Values",
                    "severity": "CRITICAL",
                    "explanation": "Record is missing the member_id identifier."
                }
                anomalies.append(anomaly)
                SessionMemory.add_anomaly(anomaly)
                continue
                
            # 2. Duplicate Member ID Check
            if member_id in seen_members:
                anomaly = {
                    "row": index + 1,
                    "member_id": member_id,
                    "type": "Duplicate Member ID",
                    "severity": "HIGH",
                    "explanation": f"Member ID '{member_id}' occurs multiple times in the upload."
                }
                anomalies.append(anomaly)
                SessionMemory.add_anomaly(anomaly)
            seen_members.add(member_id)

            # 3. Missing Fields Check
            required_fields = ["savings", "loan_amount", "outstanding_loan", "monthly_due", "actual_paid", "missed_payments"]
            missing_fields = []
            for field in required_fields:
                val = record.get(field)
                if val is None or str(val).strip() == "":
                    missing_fields.append(field)
            
            if missing_fields:
                anomaly = {
                    "row": index + 1,
                    "member_id": member_id,
                    "type": "Missing Values",
                    "severity": "HIGH",
                    "explanation": f"Missing values in columns: {', '.join(missing_fields)}"
                }
                anomalies.append(anomaly)
                SessionMemory.add_anomaly(anomaly)
                continue

            try:
                savings = float(record.get("savings", 0.0))
                loan_amount = float(record.get("loan_amount", 0.0))
                outstanding = float(record.get("outstanding_loan", 0.0))
                due = float(record.get("monthly_due", 0.0))
                paid = float(record.get("actual_paid", 0.0))
                missed = int(record.get("missed_payments", 0))
            except ValueError as e:
                anomaly = {
                    "row": index + 1,
                    "member_id": member_id,
                    "type": "Invalid Format",
                    "severity": "HIGH",
                    "explanation": f"Failed to parse numerical columns: {e}"
                }
                anomalies.append(anomaly)
                SessionMemory.add_anomaly(anomaly)
                continue

            # 4. Negative Savings Check
            if savings < 0:
                anomaly = {
                    "row": index + 1,
                    "member_id": member_id,
                    "type": "Negative Savings",
                    "severity": "HIGH",
                    "explanation": f"Savings balance is negative (₹{savings:,.2f})."
                }
                anomalies.append(anomaly)
                SessionMemory.add_anomaly(anomaly)

            # 5. Negative Loan Check
            if loan_amount < 0:
                anomaly = {
                    "row": index + 1,
                    "member_id": member_id,
                    "type": "Negative Loan",
                    "severity": "HIGH",
                    "explanation": f"Loan amount is negative (₹{loan_amount:,.2f})."
                }
                anomalies.append(anomaly)
                SessionMemory.add_anomaly(anomaly)

            # 6. Extreme Loan-to-Savings Ratio Check
            if savings > 0 and loan_amount > 0:
                ratio = loan_amount / savings
                if ratio > 10.0:
                    anomaly = {
                        "row": index + 1,
                        "member_id": member_id,
                        "type": "Abnormal Loan Ratio",
                        "severity": "MEDIUM",
                        "explanation": f"Loan amount is disproportionately high relative to savings (₹{loan_amount:,.2f} vs. ₹{savings:,.2f}, ratio {ratio:.1f}x)."
                    }
                    anomalies.append(anomaly)
                    SessionMemory.add_anomaly(anomaly)

            # 7. Unusually High Repayment Spike Check
            if due > 0 and paid > due * 3:
                anomaly = {
                    "row": index + 1,
                    "member_id": member_id,
                    "type": "Repayment Spike",
                    "severity": "MEDIUM",
                    "explanation": f"Repayment paid is exceptionally high compared to monthly due (₹{paid:,.2f} paid vs. ₹{due:,.2f} due)."
                }
                anomalies.append(anomaly)
                SessionMemory.add_anomaly(anomaly)

        ObservabilityManager.log_event(
            self.name, 
            f"Screening complete. Identified {len(anomalies)} data anomalies.",
            "WARNING" if anomalies else "SUCCESS"
        )
        return anomalies
