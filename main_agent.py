import os
import csv
import argparse
import pandas as pd
from typing import Dict, Any, List

# Core and Database
from memory.database import DatabaseManager
from memory.session_memory import SessionMemory
from core.observability import ObservabilityManager

# Agents
from agents.planner import PlannerAgent
from agents.risk_agent import RiskAssessmentAgent
from agents.recovery_agent import RecoveryAnalysisAgent
from agents.anomaly_agent import AnomalyDetectionAgent
from agents.approval_agent import ApprovalAgent
from agents.evaluator import EvaluatorAgent

class SHGWorkflowManager:
    def __init__(self):
        # Initialize SQLite tables
        DatabaseManager.init_db()
        
        # Instantiate agents
        self.planner = PlannerAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.recovery_agent = RecoveryAnalysisAgent()
        self.anomaly_agent = AnomalyDetectionAgent()
        self.approval_agent = ApprovalAgent()
        self.evaluator = EvaluatorAgent()

    def run_analysis_pipeline(self, file_path: str, month: str = "2026-06") -> Dict[str, Any]:
        """
        Runs the complete multi-agent pipeline for a given CSV ledger file.
        """
        if not os.path.exists(file_path):
            error_msg = f"Target ledger file not found: {file_path}"
            ObservabilityManager.log_event("WorkflowManager", error_msg, "ERROR")
            return {"status": "FAILED", "error": error_msg}

        # Clear short-term session memory for a clean run
        SessionMemory.reset(month)
        ObservabilityManager.clear_logs()
        
        ObservabilityManager.log_event("WorkflowManager", f"Loading ledger from: {file_path}")

        # Ingest CSV contents
        records = []
        try:
            # We read with pandas or csv module.
            # Using pandas to load and convert to dictionary records safely.
            df = pd.read_csv(file_path)
            # Standardize columns to lowercase, strip whitespaces
            df.columns = [col.lower().strip() for col in df.columns]
            
            # Fill NaN values with empty string or logical defaults
            # Let's preserve NaNs as None so agents can handle missing fields
            df_cleaned = df.where(pd.notnull(df), None)
            records = df_cleaned.to_dict(orient="records")
        except Exception as e:
            error_msg = f"Failed to parse CSV ledger: {e}"
            ObservabilityManager.log_event("WorkflowManager", error_msg, "ERROR")
            return {"status": "FAILED", "error": error_msg}

        # Set ledger into active session memory
        SessionMemory.set_ledger(records)
        
        # Save ledger records to persistent database storage
        for rec in records:
            if rec.get("member_id"):
                DatabaseManager.save_ledger_record(rec, month)

        # 1. Planner schedule task pipeline
        tasks = self.planner.plan_workflow(month, records)

        # 2. Iterate and dispatch task messages to worker agents
        for msg in tasks:
            msg.update_status("RUNNING")
            ObservabilityManager.log_event("WorkflowManager", f"Dispatching message from {msg.sender} to {msg.receiver} ({msg.task_type}).")
            
            try:
                if msg.receiver == "RiskAssessmentAgent":
                    self.risk_agent.execute_task(msg)
                elif msg.receiver == "RecoveryAnalysisAgent":
                    self.recovery_agent.execute_task(msg)
                elif msg.receiver == "AnomalyDetectionAgent":
                    self.anomaly_agent.execute_task(msg)
                elif msg.receiver == "ApprovalAgent":
                    # Approval recommendation relies on computations gathered by previous agents
                    self.approval_agent.execute_task(msg)
                
                msg.update_status("COMPLETED")
            except Exception as ex:
                msg.update_status("FAILED")
                ObservabilityManager.log_event(
                    msg.receiver, 
                    f"Agent execution failed for task {msg.task_type}: {ex}", 
                    "ERROR"
                )

        # 3. Quality control audit and final report compile
        final_report = self.evaluator.audit_and_synthesize(month)
        
        ObservabilityManager.log_event("WorkflowManager", "Pipeline orchestration complete.", "SUCCESS")
        return final_report

def run_tests():
    """Bulk tests all 12 provided dataset scenarios."""
    print("\n" + "="*50)
    print("RUNNING SHG GUARDIAN MULTI-AGENT VERIFICATION")
    print("="*50 + "\n")
    
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(workspace_dir, "Sample_test_dat")
    if not os.path.exists(test_dir):
        test_dir = workspace_dir
    
    # Locate files starting with digits
    csv_files = [f for f in os.listdir(test_dir) if f.endswith(".csv") and f[0].isdigit()]
    csv_files.sort(key=lambda x: int(x.split()[0])) # Sort numerically
    
    manager = SHGWorkflowManager()
    
    results = []
    
    for csv_file in csv_files:
        path = os.path.join(test_dir, csv_file)
        month_label = f"2026-06-{csv_file.split()[0]}"
        print(f"\n[TESTING] Processing dataset scenario: {csv_file}")
        
        report = manager.run_analysis_pipeline(path, month_label)
        
        # Display key summary fields
        print(f" -> Status: {report.get('status')}")
        print(f" -> Members Count: {report.get('total_members')}")
        print(f" -> Overall Recovery Rate: {report.get('overall_recovery_rate', 0)*100:.1f}%")
        print(f" -> Risk Distribution: {report.get('risk_distribution')}")
        print(f" -> Anomalies Detected: {report.get('anomalies_flagged')}")
        print(f" -> Escalations Queued: {report.get('escalations_generated')}")
        
        results.append({
            "dataset": csv_file,
            "status": report.get("status"),
            "members": report.get("total_members"),
            "anomalies": report.get("anomalies_flagged"),
            "escalations": report.get("escalations_generated")
        })
        
    print("\n" + "="*50)
    print("VERIFICATION COMPLETED SUMMARY")
    print("="*50)
    for res in results:
        print(f"{res['dataset']:<45} | Status: {res['status']:<25} | Anomalies: {res['anomalies']:<3} | Escalations: {res['escalations']}")
    print("="*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SHG Guardian AI Workflow CLI Orchestrator")
    parser.add_argument("--file", type=str, help="Path to single ledger CSV file to analyze")
    parser.add_argument("--month", type=str, default="2026-06", help="Month of ledger file (e.g. 2026-06)")
    parser.add_argument("--test-all", action="store_true", help="Runs pipeline checks on all 12 benchmark test CSVs")
    
    args = parser.parse_args()
    
    if args.test_all:
        run_tests()
    elif args.file:
        manager = SHGWorkflowManager()
        report = manager.run_analysis_pipeline(args.file, args.month)
        print("\nPipeline Execution Final Report Summary:")
        import json
        print(json.dumps(report, indent=2))
    else:
        parser.print_help()
