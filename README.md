# SHG Guardian AI: Multi-Agent Financial Risk & Recovery Intelligence System

SHG Guardian AI is an agentic microfinance analytics and risk intelligence platform. It analyzes member ledgers, flags data anomalies, evaluates delinquency risks, and processes approvals through a multi-level human workflow.

The system is designed with a **Planner → Worker → Evaluator** multi-agent architecture.

---

## Architecture Flow

```mermaid
graph TD
    User([User Ingests CSV]) --> PlannerAgent
    PlannerAgent --> RiskAgent[Worker 1: Risk Assessment]
    PlannerAgent --> RecoveryAgent[Worker 2: Recovery Metrics]
    PlannerAgent --> AnomalyAgent[Worker 3: Anomaly Detection]
    
    RiskAgent --> ApprovalAgent[Worker 4: Approval Recommendation]
    RecoveryAgent --> ApprovalAgent
    AnomalyAgent --> ApprovalAgent
    
    ApprovalAgent --> EvaluatorAgent
    EvaluatorAgent --> SQLite[(Persistent SQLite Long-Term Memory)]
    EvaluatorAgent --> Dashboard[Interactive Gradio Frontend]
    Dashboard --> HumanApproval[Human-in-the-Loop Approval Layer]
```

---

## File Structure

```
.
├── app.py                      # Gradio Web Interface Dashboard
├── main_agent.py               # Orchestrator & CLI Runner
├── requirements.txt            # Package dependencies
├── README.md                   # Instructions and docs
├── agents/                     # Specialized agent modules
│   ├── planner.py
│   ├── risk_agent.py
│   ├── recovery_agent.py
│   ├── anomaly_agent.py
│   ├── approval_agent.py
│   └── evaluator.py
├── tools/                      # Shared helper tools
│   ├── calculator_tool.py
│   ├── prediction_tool.py
│   └── database_tool.py
├── memory/                     # Session and database persistence
│   ├── database.py
│   └── session_memory.py
└── core/                       # Protocols & logging
    ├── a2a_protocol.py
    └── observability.py
```

---

## Installation & Setup

1. **Install Python Dependencies**:
   Ensure you have Python 3.8+ installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Installation with Benchmark Datasets**:
   Run the batch testing verification CLI to analyze all 12 test scenario CSV files:
   ```bash
   python main_agent.py --test-all
   ```

3. **Launch the Web Dashboard**:
   Start the interactive Gradio local server:
   ```bash
   python app.py
   ```
   Once launched, open your web browser and navigate to: [http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## Verification Scenarios (The 12 Test Cases)

The application validates the ledger data against the following edge cases in the workspace:
1. **High Risk Member**: High outstanding relative to savings, multiple missed payments.
2. **Low Risk Member**: High savings, zero missed payments.
3. **Medium Risk Member**: Minor missed payments.
4. **Zero Payment**: Tests zero collection rates.
5. **Loan Already Cleared**: Safe state check for members with zero outstanding loans.
6. **Anomaly: Payment > Due**: Large overpayment anomaly indicator.
7. **Anomaly: Negative Loan**: Flags data input validation failure.
8. **Anomaly: Negative Savings**: Flags data input validation failure.
9. **Division by Zero**: Safeguards computations when monthly due is 0.
10. **Duplicate Member IDs**: Identifies repeated key records.
11. **Missing Values**: Identifies blank columns.
12. **Mixed Dataset (Competition Grade)**: Master validation set combining all elements.
