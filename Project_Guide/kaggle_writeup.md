# Kaggle Capstone Submission Writeup

**Project Title**: SHG Guardian AI: Multi-Agent Financial Risk & Recovery Intelligence System  
**Track**: Freestyle (Open Track)  
**Interactive Demo URL**: [Deployable on Hugging Face Spaces via Gradio]  

---

## 1. Problem Statement: Financial Security in Microfinance

Self Help Groups (SHGs) and microfinance organizations provide vital credit and savings services to millions of members, particularly women in underserved rural communities. However, managing financial data in these groups is plagued by operational hurdles:
* **Manual Data Entry Bottlenecks**: Transactions are tracked in manual ledger spreadsheets, making it slow and error-prone.
* **Delayed Risk Spotting**: Managers often realize a member is at risk of defaulting months after the opportunity for early financial intervention has passed.
* **Data Integrity and Fraud**: Excel files are prone to duplicates, missing values, negative balances, and data manipulation.
* **Approval Silos**: Communicating escalations between Field Officers (collecting data in the village) and Regional Coordinators (approving loans) is slow and lacks an audit trail.

**Why this matters**: In microfinance, trust is the primary asset. Early risk detection and strict operational oversight directly prevent default cascades, protecting the collective savings of vulnerable community members.

---

## 2. The Solution: SHG Guardian AI

SHG Guardian AI is a multi-agent financial intelligence platform that automates ledger validation, defaults prediction, and anomaly detection. It presents these analytics through a dashboard and routes high-risk cases through a **Human-in-the-Loop** approval workflow.

### Why Agents?
Traditional software relies on rigid, single-line scripts. If a spreadsheet contains a missing row or zero value, the script crashes. 

An agentic approach is uniquely suited here because:
1. **Separation of Concerns**: Individual specialized agents focus on isolated tasks (e.g. mathematical collection formulas, risk heuristics, formatting checks).
2. **Resilience**: The system does not crash on anomalous data; instead, the Anomaly Agent flags the error, while other agents continue processing healthy rows.
3. **Collaboration**: Agents communicate using a standard protocol, passing tasks and intermediate calculations, mirroring a real-world financial audit team.

---

## 3. Multi-Agent Architecture & Design

The platform uses a **Planner $\rightarrow$ Worker $\rightarrow$ Evaluator** pattern, coordinating independent agents to process a ledger and reach a consensus:

```
                  [User Ledger Upload]
                           │
                           ▼
                     [Planner Agent]
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    [Risk Agent]    [Recovery Agent]   [Anomaly Agent]
         │                 │                 │
         └─────────────────┼─────────────────┘
                           ▼
                    [Approval Agent]
                           │
                           ▼
                   [Evaluator Agent]
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
[SQLite DB Memory]                 [Gradio UI Dashboard]
                                             │
                                             ▼
                                 [Human-in-the-Loop Approval]
```

### Agent Roles:
1. **Planner Agent**: Parses the incoming data request, schedules execution tasks, and coordinates messages for worker agents.
2. **Anomaly Detection Agent (Worker)**: Screens rows for inputs such as duplicate IDs, missing values, negative loan balances, or unrealistic repayment spikes.
3. **Risk Assessment Agent (Worker)**: Evaluates member debt-to-savings ratios and payment histories to assign a numeric risk score (0-100) and risk level (Low, Medium, High).
4. **Recovery Analysis Agent (Worker)**: Computes collection totals and recovery rates for individuals and groups.
5. **Approval Agent (Worker)**: Takes intermediate risk calculations and automatically queues high-risk accounts or severe anomalies for human audits.
6. **Evaluator Agent (Consensus & Audit)**: Serves as the quality controller. It verifies that all agents completed their calculations and generates a final report.

---

## 4. Demonstrating Key Course Concepts

The system directly implements key agentic design patterns covered in the course:

### Concept 1: Multi-Agent System (ADK)
The system leverages independent python classes representing each agent, communicating via a standardized message protocol (`AgentMessage`) tracking sender, receiver, task type, payload, and status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`). This decoupling keeps code clean and modular.

### Concept 2: Agent Skills & Tools
Agents do not hallucinate metrics. They use specialized tools to interact with their environment:
* **Calculator Tool**: Safely performs division operations, preventing zero-division errors when monthly dues are zero.
* **Prediction Tool**: Forecasts default probability using a weighted risk formula combined with historical trends.
* **Database Tool**: Interface for querying and updating records in persistent memory.
* **Local Semantic Query Tool**: Powering the chat assistant to translate natural language inputs (e.g. *"Show high risk members"*) into SQLite queries.

### Concept 3: Database & Session Memory
* **Short-Term Memory (`SessionMemory`)**: An isolated JSON-like memory layer that caches the current session's upload state, intermediate agent outputs, and runtime logs.
* **Long-Term Memory (`DatabaseManager`)**: A persistent SQLite database storing historical ledger inputs, changing risk trends, and human approval logs over successive monthly cycles.

### Concept 4: Security & Input Checks
To ensure safety in microfinance workflows:
* Data sanitization filters out negative balances and duplicate entries.
* The system enforces **Human-in-the-Loop (HITL)** approvals before an escalation status is finalized.
* SQL queries in the NLP chatbot are parameterized to prevent injection risks.
* No API keys or credentials are hardcoded, relying on standard environment variables.

---

## 5. Walkthrough of the User Experience

The application is deployed as an interactive web app with five tabs:
1. **Ledger Upload**: The user uploads a CSV sheet. Clicking *Start Automated Review* displays the live workflow log as agents coordinate.
2. **Analytics Dashboard**: Shows high-level KPIs, a repayment comparison bar chart (Monthly Due vs. Actual Paid), and a portfolio risk pie chart.
3. **Anomaly Report**: Lists data formatting issues or suspicious repayment spikes.
4. **Verification Queue**: An interface for Field Officers and Regional Coordinators to audit, comment on, and approve or reject flagged accounts.
5. **AI Financial Assistant**: A natural language chatbot where users can ask questions about group metrics and individual member risk profiles.

---

## 6. Reflections and Project Value

By building SHG Guardian AI, we moved from basic dashboard scripting to a robust, fault-tolerant agentic system. Using agents allows the platform to be resilient against poor data quality while enforcing strict corporate governance through the human approval queue. This project represents a practical, secure, and production-ready tool that directly improves the financial health and sustainability of local microfinance institutions.
