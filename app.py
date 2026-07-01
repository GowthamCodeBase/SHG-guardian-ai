import os
import gradio as gr
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import re

# Import modules
from main_agent import SHGWorkflowManager
from memory.session_memory import SessionMemory
from memory.database import DatabaseManager
from core.observability import ObservabilityManager
from tools.database_tool import DatabaseTool
from tools.calculator_tool import CalculatorTool

# Initialize database schema
DatabaseManager.init_db()
workflow_manager = SHGWorkflowManager()

# Global styling options
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="sky",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Outfit"), "sans-serif"]
)

# Custom CSS for dark/light mode adaptable cards and badges
custom_css = """
:root, body, .dark {
    --body-background-fill: #0f172a !important; /* Deep Dark */
    --background-fill-primary: #0f172a !important;
    --background-fill-secondary: #1e293b !important;
    --block-background-fill: #1e293b !important;
    --body-text-color: #f8fafc !important; /* Crisp White text */
    --body-text-color-subdued: #94a3b8 !important; /* Light slate text */
    --border-color-primary: #334155 !important; /* Dark border */
}
.metric-card {
    border-radius: 12px;
    padding: 16px;
    border: 1px solid var(--border-color-primary);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    background: var(--block-background-fill);
}
.kpi-title {
    font-size: 0.85em;
    color: var(--body-text-color-subdued);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}
.kpi-value {
    font-size: 1.8em;
    font-weight: 700;
    color: var(--body-text-color);
    margin-top: 5px;
}
.kpi-subtitle {
    font-size: 0.8em;
    color: var(--body-text-color-subdued);
    margin-top: 3px;
}
.badge-low {
    background-color: rgba(34, 197, 94, 0.15);
    color: #22c55e;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.8em;
    font-weight: 600;
    display: inline-block;
}
.badge-med {
    background-color: rgba(234, 179, 8, 0.15);
    color: #eab308;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.8em;
    font-weight: 600;
    display: inline-block;
}
.badge-high {
    background-color: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.8em;
    font-weight: 600;
    display: inline-block;
}
.upload-card-header {
    font-size: 1.4em;
    font-weight: 700;
    margin-bottom: 15px;
    color: #f8fafc;
    text-align: center;
}
.upload-card {
    border-radius: 16px !important;
    padding: 24px !important;
    border: 1px solid var(--border-color-primary) !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
    background: var(--block-background-fill) !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.upload-card:hover {
    box-shadow: 0 15px 35px rgba(0,0,0,0.08) !important;
    transform: translateY(-2px);
}
.run-btn {
    background: linear-gradient(135deg, #4285F4 0%, #34A853 100%) !important;
    border: none !important;
    color: white !important;
    font-size: 1.1em !important;
    font-weight: 600 !important;
    transition: opacity 0.2s ease !important;
}
.run-btn:hover {
    opacity: 0.9 !important;
}
"""

def generate_kpis_html(report):
    """Formats HTML cards for main analytics dashboard KPIs adapting to dark mode."""
    if not report or report.get("status") == "FAILED":
        return "<div class='metric-card'><p style='color: var(--body-text-color);'>No data analyzed yet. Please upload a record file.</p></div>"
        
    overall_rate = report.get("overall_recovery_rate", 0.0) * 100
    total_coll = report.get("total_collected", 0.0)
    total_due = report.get("total_due", 0.0)
    dist = report.get("risk_distribution", {"LOW": 0, "MEDIUM": 0, "HIGH": 0})
    anom = report.get("anomalies_flagged", 0)
    esc = report.get("escalations_generated", 0)

    html = f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; width: 100%;">
        <div class="metric-card">
            <div class="kpi-title">Total Members</div>
            <div class="kpi-value">{report.get("total_members", 0)}</div>
        </div>
        <div class="metric-card" style="border-left: 4px solid #37BAE8;">
            <div class="kpi-title">Payment Collection Rate</div>
            <div class="kpi-value" style="color: #37BAE8;">{overall_rate:.1f}%</div>
            <div class="kpi-subtitle">Collected: ₹{total_coll:,.0f} / ₹{total_due:,.0f}</div>
        </div>
        <div class="metric-card" style="border-left: 4px solid #ef4444;">
            <div class="kpi-title">Risky Members</div>
            <div class="kpi-value" style="color: #ef4444;">{dist.get("HIGH", 0)}</div>
            <div class="kpi-subtitle">Medium: {dist.get("MEDIUM", 0)} | Low: {dist.get("LOW", 0)}</div>
        </div>
        <div class="metric-card" style="border-left: 4px solid #f59e0b;">
            <div class="kpi-title">Warnings & Errors</div>
            <div class="kpi-value" style="color: #f59e0b;">{anom}</div>
        </div>
        <div class="metric-card" style="border-left: 4px solid #6366f1;">
            <div class="kpi-title">Escalations Pending</div>
            <div class="kpi-value" style="color: #6366f1;">{esc}</div>
        </div>
    </div>
    """
    return html

def make_plotly_charts():
    """Generates user-friendly analytical charts with neutral colors readable in both light and dark mode."""
    ledger = SessionMemory.get_ledger()
    risk_scores = SessionMemory.get_risk_scores()
    
    if not ledger:
        fig_rec = go.Figure()
        fig_rec.update_layout(title="No data loaded")
        fig_risk = go.Figure()
        fig_risk.update_layout(title="No data loaded")
        return fig_rec, fig_risk

    try:
        # 1. Payment Recovery Comparison Bar Chart (Due vs Paid)
        df = pd.DataFrame(ledger)
        if len(df) > 50:
            df = df.head(50)
        df["member_id"] = df["member_id"].astype(str)
        
        fig_rec = go.Figure()
        
        # Premium styling for Due
        fig_rec.add_trace(go.Bar(
            x=df["member_id"],
            y=df["monthly_due"],
            name="Target Due",
            marker=dict(color="#1e293b", line=dict(color="#334155", width=1.5)),
            hovertemplate="<b>%{x}</b><br>Target Due: ₹%{y:,.0f}<extra></extra>"
        ))
        
        # Premium styling for Paid
        fig_rec.add_trace(go.Bar(
            x=df["member_id"],
            y=df["actual_paid"],
            name="Amount Paid",
            marker=dict(
                color="#37BAE8", 
                line=dict(color="#118AB2", width=1.5),
                pattern_shape=""
            ),
            hovertemplate="<b>%{x}</b><br>Amount Paid: ₹%{y:,.0f}<extra></extra>"
        ))
        
        fig_rec.update_layout(
            title=dict(
                text="Repayment Recovery Analytics" if len(pd.DataFrame(ledger)) > 50 else "Repayment Recovery Analytics",
                font=dict(size=20, color="#f8fafc", family="Outfit")
            ),
            barmode="group",
            bargap=0.2,
            bargroupgap=0.1,
            xaxis=dict(
                title="",
                tickfont=dict(color="#94a3b8"),
                showgrid=False
            ),
            yaxis=dict(
                title="Amount (₹)",
                tickfont=dict(color="#94a3b8"),
                gridcolor="#334155",
                zerolinecolor="#334155"
            ),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#cbd5e1")
            ),
            margin=dict(l=40, r=20, t=80, b=40),
            hovermode="x unified"
        )
    
        # 2. Risk Distribution Donut Chart (Modern)
        risk_cats = [data.get("category", "LOW") for data in risk_scores.values()]
        risk_df = pd.DataFrame(risk_cats, columns=["Risk"])
        risk_counts = risk_df["Risk"].value_counts().reset_index()
        risk_counts.columns = ["Risk Category", "Count"]
        
        # Sort so it's consistently ordered
        sorter = ["HIGH", "MEDIUM", "LOW"]
        risk_counts["Risk Category"] = pd.Categorical(risk_counts["Risk Category"], categories=sorter, ordered=True)
        risk_counts = risk_counts.sort_values("Risk Category")
        
        color_map = {"LOW": "#10b981", "MEDIUM": "#f59e0b", "HIGH": "#ef4444"}
        
        fig_risk = px.pie(
            risk_counts,
            values="Count",
            names="Risk Category",
            color="Risk Category",
            color_discrete_map=color_map,
            hole=0.6, # Make it a premium donut chart
        )
        
        # Add center text
        total_risk = risk_counts["Count"].sum()
        fig_risk.add_annotation(
            text=f"<b>{total_risk}</b><br><span style='font-size:12px;color:#94a3b8'>Members</span>",
            x=0.5, y=0.5, font_size=24, font_color="#f8fafc", showarrow=False
        )

        fig_risk.update_traces(
            textposition='outside', 
            textinfo='percent+label',
            hovertemplate="<b>%{label} Risk</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
            marker=dict(line=dict(color='#0f172a', width=3)),
            pull=[0.05 if cat == "HIGH" else 0 for cat in risk_counts["Risk Category"]] # Pull HIGH risk out slightly
        )
        
        fig_risk.update_layout(
            title=dict(
                text="Portfolio Risk Distribution",
                font=dict(size=20, color="#f8fafc", family="Outfit")
            ),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=20, r=20, t=80, b=40)
        )
        return fig_rec, fig_risk
    except Exception as e:
        print(f"Error generating Plotly charts: {e}")
        fig_err = go.Figure()
        fig_err.update_layout(title=f"Error rendering chart: {e}")
        return fig_err, fig_err

def load_dataframes():
    """Generates detailed table with plain English column headers."""
    ledger = SessionMemory.get_ledger()
    risk_scores = SessionMemory.get_risk_scores()
    recovery_rates = SessionMemory.get_recovery_rates()
    anomalies = SessionMemory.get_anomalies()
    
    if not ledger:
        return pd.DataFrame(), pd.DataFrame()

    rows = []
    for record in ledger:
        member_id = record.get("member_id")
        risk_data = risk_scores.get(member_id, {"score": 0.0, "category": "LOW", "reasons": "N/A"})
        rec_rate = recovery_rates.get(member_id, 1.0)
        
        rows.append({
            "Member ID": member_id,
            "Village Location": record.get("village", "Unknown"),
            "Group ID": record.get("group_id", "Unknown"),
            "Total Savings (₹)": record.get("savings", 0.0),
            "Original Loan (₹)": record.get("loan_amount", 0.0),
            "Remaining Debt (₹)": record.get("outstanding_loan", 0.0),
            "Monthly Due (₹)": record.get("monthly_due", 0.0),
            "Amount Paid (₹)": record.get("actual_paid", 0.0),
            "Collection Rate": f"{rec_rate * 100:.1f}%",
            "Missed Months": record.get("missed_payments", 0),
            "Risk Score (0-100)": f"{risk_data.get('score', 0.0):.0f}",
            "Risk Category": risk_data.get("category", "LOW"),
            "Auditing Reasons": risk_data.get("reasons", "")
        })
        
    df_detail = pd.DataFrame(rows)
    
    # Anomaly dataframe
    if anomalies:
        df_anom = pd.DataFrame(anomalies)
        df_anom = df_anom[["row", "member_id", "type", "severity", "explanation"]]
        df_anom.columns = ["Row Number", "Member ID", "Warning Type", "Severity", "Explanation Summary"]
    else:
        df_anom = pd.DataFrame(columns=["Row Number", "Member ID", "Warning Type", "Severity", "Explanation Summary"])

    return df_detail, df_anom

def process_upload(file, month):
    """Processes uploaded CSV ledger file and triggers multi-agent flow."""
    if not file:
        return "Please upload a valid CSV file.", "", gr.update(value=""), pd.DataFrame(), pd.DataFrame(), go.Figure(), go.Figure()
        
    # Run Orchestrator Pipeline
    report = workflow_manager.run_analysis_pipeline(file.name, month)
    
    if report.get("status") == "FAILED":
        return f"Audit processing failed: {report.get('error')}", "", gr.update(value=""), pd.DataFrame(), pd.DataFrame(), go.Figure(), go.Figure()
    
    # Log representation
    logs = ObservabilityManager.get_logs()
    log_text = "\n".join([f"[{l['timestamp']}] [{l['status']}] [{l['agent']}] {l['message']}" for l in logs])
    
    # Generate widgets
    kpi_html = generate_kpis_html(report)
    df_detail, df_anom = load_dataframes()
    fig_rec, fig_risk = make_plotly_charts()
    
    status_summary = f"### System Audit Complete: **{report.get('status')}**\n" \
                     f"Reviewed **{report.get('total_members')}** member logs. " \
                     f"Identified **{report.get('anomalies_flagged')}** data warnings " \
                     f"and routed **{report.get('escalations_generated')}** entries to the human review list."
                     
    return status_summary, log_text, kpi_html, df_detail, df_anom, fig_rec, fig_risk

# Human Approval Functions
def get_approvals_dataframe():
    """Queries persistent database and forms active approvals DataFrame."""
    queue = DatabaseTool.query_active_approvals()
    if not queue:
        return pd.DataFrame(columns=[
            "Record ID", "Member ID", "Village Location", "Group Name", "Month", 
            "Risk Category", "Reason for Escalation", "Field Officer Check", "Coordinator Decision"
        ])
        
    rows = []
    for item in queue:
        rows.append({
            "Record ID": item.get("id"),
            "Member ID": item.get("member_id"),
            "Village Location": item.get("village"),
            "Group Name": item.get("group_name"),
            "Month": item.get("ledger_month"),
            "Risk Category": item.get("risk_level"),
            "Reason for Escalation": item.get("escalation_reason"),
            "Field Officer Check": item.get("field_officer_status"),
            "Coordinator Decision": item.get("regional_coordinator_status")
        })
    return pd.DataFrame(rows)

def process_approval_action(approval_id, role, decision, comments):
    """Registers human decision and reloads approval queue, supporting both numeric IDs and Member IDs."""
    if not approval_id:
        return "Please specify a valid Record ID or Member ID.", get_approvals_dataframe()
    
    target_id = approval_id.strip()
    app_id = None
    
    # Try direct numeric lookup first
    if target_id.isdigit():
        app_id = int(target_id)
    else:
        # Resolve from member_id in the database
        member_id_upper = target_id.upper()
        conn = sqlite3.connect(DatabaseManager.DB_FILE)
        cursor = conn.cursor()
        try:
            # Get the latest escalation entry for this member
            cursor.execute("SELECT id FROM approvals WHERE UPPER(member_id) = ? ORDER BY id DESC LIMIT 1", (member_id_upper,))
            row = cursor.fetchone()
            if row:
                app_id = row[0]
            else:
                return f"No pending escalations found for Member ID '{target_id}'.", get_approvals_dataframe()
        except Exception as e:
            return f"Error looking up Member ID: {e}", get_approvals_dataframe()
        finally:
            conn.close()
            
    success = DatabaseTool.log_approval_action(app_id, role, decision, comments)
    if success:
        msg = f"Audit log successfully recorded for {target_id} (Record ID: {app_id}) as '{decision}' under role {role}."
    else:
        msg = f"Failed to register action for {target_id}."
        
    return msg, get_approvals_dataframe()


# Local Semantic Chatbot Logic
def local_nlp_assistant(query: str) -> str:
    """Answers database queries using simplified, non-technical words."""
    query_clean = query.lower().strip()
    conn = sqlite3.connect(DatabaseManager.DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Match "Why is member SHG001 flagged?"
        member_match = re.search(r"shg\d{3}", query_clean)
        if member_match:
            member_id = member_match.group(0).upper()
            cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
            memb = cursor.fetchone()
            if not memb:
                return f"Member ID `{member_id}` is not found in the historical records."
                
            cursor.execute("SELECT * FROM ledgers WHERE member_id = ? ORDER BY ledger_month DESC LIMIT 1", (member_id,))
            ledger = cursor.fetchone()
            
            cursor.execute("SELECT * FROM risk_history WHERE member_id = ? ORDER BY analysis_date DESC LIMIT 1", (member_id,))
            risk = cursor.fetchone()
            
            response = f"### Member Information Card: {member_id}\n"
            response += f"* **Location**: Village {memb[1]} | Group: {memb[2]}\n"
            response += f"* **Join Date**: {memb[3]}\n\n"
            
            if ledger:
                response += f"**Financial Details for {ledger[8]}:**\n"
                response += f"* Savings Balance: ₹{ledger[2]:,.2f} | Current Remaining Loan: ₹{ledger[4]:,.2f}\n"
                response += f"* Planned Monthly Due: ₹{ledger[5]:,.2f} | Amount Received: ₹{ledger[6]:,.2f}\n"
                response += f"* Overdue Months: {ledger[7]}\n\n"
                
            if risk:
                response += f"**AI Risk Analysis: Risk Score {risk[2]:.0f}/100 ({risk[3]} Risk Category)**\n"
                response += f"* **Reasons**: {risk[5]}\n\n"
                
            # Check active approvals
            cursor.execute("SELECT * FROM approvals WHERE member_id = ? ORDER BY id DESC LIMIT 1", (member_id,))
            approval = cursor.fetchone()
            if approval:
                response += f"**Review and Approval Status:**\n"
                response += f"* Field Officer Check: `{approval[5]}` (Notes: {approval[6] or 'No notes'})\n"
                response += f"* Regional Coordinator Decision: `{approval[7]}` (Notes: {approval[8] or 'No notes'})\n"
                
            return response

        # Match "Show high risk members" or "high risk"
        if "high risk" in query_clean:
            cursor.execute("""
                SELECT r.member_id, r.risk_score, r.reasons, m.village 
                FROM risk_history r
                JOIN members m ON r.member_id = m.member_id
                WHERE r.risk_category = 'HIGH'
                GROUP BY r.member_id
                HAVING r.id = MAX(r.id)
            """)
            rows = cursor.fetchall()
            if not rows:
                return "There are currently no **HIGH Risk** members in the system."
                
            res = "### High Risk Members Awaiting Verification\n"
            for r in rows:
                res += f"* **{r[0]}** (Risk Score: {r[1]:.0f}/100) - Village: {r[3]}\n  * *Why:* {r[2]}\n"
            return res

        # Match "missed payments" or "missed"
        if "missed" in query_clean:
            cursor.execute("""
                SELECT member_id, missed_payments, ledger_month 
                FROM ledgers 
                WHERE missed_payments > 0
                ORDER BY missed_payments DESC
            """)
            rows = cursor.fetchall()
            if not rows:
                return "No members have missed any loan payments."
            res = "### Missed Payments Log\n"
            for r in rows:
                res += f"* **{r[0]}**: Missed {r[1]} payment period(s) for the month of {r[2]}.\n"
            return res

        # Match "village" or "which village"
        if "village" in query_clean:
            cursor.execute("""
                SELECT m.village, SUM(l.actual_paid), SUM(l.monthly_due)
                FROM ledgers l
                JOIN members m ON l.member_id = m.member_id
                GROUP BY m.village
            """)
            rows = cursor.fetchall()
            if not rows:
                return "No village stats recorded yet."
            res = "### Collection Performance by Village\n"
            for r in rows:
                paid, due = float(r[1] or 0), float(r[2] or 0)
                rate = (paid / due * 100) if due > 0 else 100.0
                res += f"* **Village {r[0]}**: Collection Rate: **{rate:.1f}%** (Collected: ₹{paid:,.2f} / Planned Due: ₹{due:,.2f})\n"
            return res

        # Match "anomalies" or "fraud"
        if "anomalies" in query_clean or "anomaly" in query_clean or "warnings" in query_clean:
            anom = SessionMemory.get_anomalies()
            if not anom:
                return "No warning alerts flagged in the current session."
            res = "### Flagged Session Warnings\n"
            for a in anom:
                res += f"* Row {a['row']} | **{a['member_id']}** ({a['type']} - {a['severity']}): {a['explanation']}\n"
            return res

        # Fallback default help response
        return "### Assistant Help Guide\n" \
               "I can help you audit and search your member records. Try typing:\n" \
               "1. *\"Why is member SHG001 flagged?\"* (shows details about SHG001)\n" \
               "2. *\"Show high risk members\"* (lists members with high risk scores)\n" \
               "3. *\"Who has missed payments?\"* (lists overdue members)\n" \
               "4. *\"Which village has the lowest recovery rate?\"* (shows collection stats by area)\n" \
               "5. *\"Show current warnings\"* (lists data errors from the uploaded file)"
               
    except Exception as e:
        return f"Error executing search assistant: {e}"
    finally:
        conn.close()

def chatbot_interface(message, history):
    response = local_nlp_assistant(message)
    return response


# Build Gradio UI layout
with gr.Blocks(title="SHG Guardian AI Dashboard") as demo:
    gr.HTML("""
    <div style='position: relative; text-align: center; margin-bottom: 20px; padding: 25px; border-radius: 16px; background: linear-gradient(145deg, rgba(66,133,244,0.1) 0%, rgba(52,168,83,0.1) 100%); border: 1px solid var(--border-color-primary); box-shadow: 0 8px 24px rgba(0,0,0,0.2);'>
        <div style='display: flex; justify-content: center; align-items: center; gap: 35px; margin-bottom: 18px;'>
            <img src='https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg' alt='Google' width='120' style='filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.1));'/>
            <span style='font-size: 28px; color: #cbd5e1; font-weight: 300;'>|</span>
            <img src='https://upload.wikimedia.org/wikipedia/commons/7/7c/Kaggle_logo.png' alt='Kaggle' width='120' style='filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.1));'/>
        </div>
        <h1 style='background: linear-gradient(90deg, #4285F4, #34A853, #FBBC05, #EA4335); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; font-size: 2.8em; font-weight: 900; letter-spacing: -0.02em;'>SHG GUARDIAN AI</h1>
        <p style='color: var(--body-text-color-subdued); font-size: 1.15em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.15em;'>
            Capstone Project: Multi-Agent Risk Assessment & Auditing
        </p>
    </div>
    """)
            
    with gr.Tabs():
        
        # TAB 1: Ledger Ingestion / Upload
        with gr.TabItem("Ledger Upload"):
            with gr.Row(equal_height=True):
                with gr.Column(scale=1, min_width=600):
                    gr.HTML("<div class='upload-card-header'>📁 Start Audit Process</div>")
                    with gr.Group(elem_classes="upload-card"):
                        file_input = gr.File(label="Upload Member Ledger (.csv)", file_types=[".csv"])
                        
                        sample_files = [os.path.join("Sample_test_dat", f) for f in sorted(os.listdir("Sample_test_dat")) if f.endswith('.csv')]
                        if sample_files:
                            gr.Examples(examples=sample_files, inputs=file_input, label="⚡ Quick Start: Choose a Capstone Benchmark Dataset", examples_per_page=6)
                            
                        with gr.Row():
                            month_input = gr.Textbox(label="Reporting Month", value="2026-06", placeholder="YYYY-MM", scale=1)
                            run_btn = gr.Button("🚀 Run Multi-Agent Audit", variant="primary", scale=2, elem_classes="run-btn")
            
            with gr.Row():
                status_md = gr.Markdown("### ⏳ Pipeline Status: Ready for upload")
                
            with gr.Accordion("🔍 View Live Agent System Logs", open=False):
                log_output = gr.TextArea(
                    label="Agent Activity Trace (Planner, Workers, Evaluator)", 
                    interactive=False, 
                    lines=10,
                    max_lines=15,
                    autoscroll=True
                )

        # TAB 2: Analytics Dashboard
        with gr.TabItem("Analytics Dashboard"):
            kpis_panel = gr.HTML(generate_kpis_html(None))
            
            with gr.Row():
                with gr.Column():
                    chart_recovery = gr.Plot(label="Payment Collection Rates (Due vs. Paid)")
                with gr.Column():
                    chart_risk_dist = gr.Plot(label="Risk Level Categories")
            
            gr.Markdown("### Detailed Review of All Members")
            detail_table = gr.DataFrame(interactive=False)

        # TAB 3: Warnings
        with gr.TabItem("Anomaly Report"):
            gr.Markdown("### Identified Mistakes & Warnings")
            anomalies_table = gr.DataFrame(interactive=False)

        # TAB 4: Verification Queue
        with gr.TabItem("Verification Queue"):
            gr.Markdown("### High-Risk Accounts Awaiting Action")
            
            with gr.Row():
                with gr.Column(scale=2):
                    approvals_table = gr.DataFrame(
                        value=get_approvals_dataframe(), 
                        interactive=False
                    )
                    refresh_btn = gr.Button("Refresh Escalation List")
                    
                with gr.Column(scale=1):
                    gr.Markdown("#### Action Review Panel")
                    app_id_input = gr.Textbox(label="Record ID or Member ID to Review", placeholder="e.g. 1 or SHG008")
                    role_select = gr.Dropdown(
                        label="Your Role", 
                        choices=["Field Officer", "Regional Coordinator"], 
                        value="Field Officer"
                    )
                    decision_select = gr.Radio(
                        label="Action Taken", 
                        choices=["APPROVED", "REJECTED", "NEEDS FIELD ESCALATION"], 
                        value="APPROVED"
                    )
                    comments_input = gr.Textbox(
                        label="Reviewer Notes", 
                        placeholder="Type justification or notes..."
                    )
                    action_btn = gr.Button("Submit Decision", variant="primary")
                    action_status = gr.Markdown("")

        # TAB 5: Chatbot Assistant
        with gr.TabItem("AI Financial Assistant"):
            gr.Markdown("### Chat with the SHG Assistant")
            gr.ChatInterface(
                fn=chatbot_interface
            )

    # Bind Events
    run_btn.click(
        fn=process_upload,
        inputs=[file_input, month_input],
        outputs=[status_md, log_output, kpis_panel, detail_table, anomalies_table, chart_recovery, chart_risk_dist]
    )
    
    action_btn.click(
        fn=process_approval_action,
        inputs=[app_id_input, role_select, decision_select, comments_input],
        outputs=[action_status, approvals_table]
    )
    
    refresh_btn.click(
        fn=get_approvals_dataframe,
        outputs=[approvals_table]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, theme=theme, css=custom_css)
