from core.observability import ObservabilityManager
from core.a2a_protocol import AgentMessage
from typing import List, Dict, Any

class PlannerAgent:
    def __init__(self):
        self.name = "PlannerAgent"

    def plan_workflow(self, ledger_month: str, data_records: List[Dict[str, Any]]) -> List[AgentMessage]:
        """
        Receives an analysis request and schedules a sequence of messages
        for the worker agents: Risk, Recovery, Anomaly, and Approval.
        """
        ObservabilityManager.log_event(self.name, f"Planning analysis workflow for month: {ledger_month} with {len(data_records)} records.")

        tasks = []
        
        # 1. Schedule Risk Assessment Task
        tasks.append(AgentMessage(
            sender=self.name,
            receiver="RiskAssessmentAgent",
            task_type="ANALYZE_RISK",
            payload={"ledger_month": ledger_month, "records": data_records}
        ))
        
        # 2. Schedule Recovery Analysis Task
        tasks.append(AgentMessage(
            sender=self.name,
            receiver="RecoveryAnalysisAgent",
            task_type="ANALYZE_RECOVERY",
            payload={"ledger_month": ledger_month, "records": data_records}
        ))

        # 3. Schedule Anomaly Detection Task
        tasks.append(AgentMessage(
            sender=self.name,
            receiver="AnomalyDetectionAgent",
            task_type="DETECT_ANOMALIES",
            payload={"ledger_month": ledger_month, "records": data_records}
        ))

        # 4. Schedule Approval Recommendation Task
        # Will run after workers gather calculations, but planned initially
        tasks.append(AgentMessage(
            sender=self.name,
            receiver="ApprovalAgent",
            task_type="GENERATE_RECOMMENDATIONS",
            payload={"ledger_month": ledger_month, "records": data_records}
        ))

        ObservabilityManager.log_event(self.name, f"Workflow planned successfully. Scheduled {len(tasks)} subtasks.")
        return tasks
