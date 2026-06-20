import os
import sqlite3
import datetime
from typing import List, Dict, Any, Tuple

class DatabaseManager:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_FILE = os.path.join(BASE_DIR, "shg_guardian.db")

    @classmethod
    def get_connection(cls):
        conn = sqlite3.connect(cls.DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initializes the SQLite schema if it doesn't already exist."""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        # 1. Members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                member_id TEXT PRIMARY KEY,
                village TEXT,
                group_name TEXT,
                join_date TEXT
            )
        """)
        
        # 2. Ledgers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ledgers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id TEXT,
                savings REAL,
                loan_amount REAL,
                outstanding_loan REAL,
                monthly_due REAL,
                actual_paid REAL,
                missed_payments INTEGER,
                ledger_month TEXT,
                FOREIGN KEY (member_id) REFERENCES members (member_id)
            )
        """)
        
        # 3. Risk history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id TEXT,
                risk_score REAL,
                risk_category TEXT,
                analysis_date TEXT,
                reasons TEXT,
                FOREIGN KEY (member_id) REFERENCES members (member_id)
            )
        """)
        
        # 4. Approvals table (Human-in-the-loop audit trail)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id TEXT,
                ledger_month TEXT,
                risk_level TEXT,
                escalation_reason TEXT,
                field_officer_status TEXT DEFAULT 'PENDING',
                field_officer_comments TEXT,
                regional_coordinator_status TEXT DEFAULT 'PENDING',
                regional_coordinator_comments TEXT,
                updated_at TEXT,
                FOREIGN KEY (member_id) REFERENCES members (member_id)
            )
        """)
        
        conn.commit()
        conn.close()

    @classmethod
    def insert_member_if_not_exists(cls, member_id: str, village: str = "Unknown", group_name: str = "SHG-General"):
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM members WHERE member_id = ?", (member_id,))
        if not cursor.fetchone():
            join_date = datetime.datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO members (member_id, village, group_name, join_date)
                VALUES (?, ?, ?, ?)
            """, (member_id, village, group_name, join_date))
            conn.commit()
        conn.close()

    @classmethod
    def save_ledger_record(cls, record: Dict[str, Any], month: str):
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        member_id = record.get("member_id")
        village = record.get("village", "Unknown")
        group_name = record.get("group_id", "SHG-General")
        
        cls.insert_member_if_not_exists(member_id, village, group_name)
        
        # Check if record already exists for this member and month to avoid duplication
        cursor.execute("""
            SELECT 1 FROM ledgers WHERE member_id = ? AND ledger_month = ?
        """, (member_id, month))
        
        if cursor.fetchone():
            # Update existing ledger
            cursor.execute("""
                UPDATE ledgers
                SET savings = ?, loan_amount = ?, outstanding_loan = ?, 
                    monthly_due = ?, actual_paid = ?, missed_payments = ?
                WHERE member_id = ? AND ledger_month = ?
            """, (
                float(record.get("savings", 0.0)),
                float(record.get("loan_amount", 0.0)),
                float(record.get("outstanding_loan", 0.0)),
                float(record.get("monthly_due", 0.0)),
                float(record.get("actual_paid", 0.0)),
                int(record.get("missed_payments", 0)),
                member_id,
                month
            ))
        else:
            # Insert new ledger
            cursor.execute("""
                INSERT INTO ledgers (
                    member_id, savings, loan_amount, outstanding_loan, 
                    monthly_due, actual_paid, missed_payments, ledger_month
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                member_id,
                float(record.get("savings", 0.0)),
                float(record.get("loan_amount", 0.0)),
                float(record.get("outstanding_loan", 0.0)),
                float(record.get("monthly_due", 0.0)),
                float(record.get("actual_paid", 0.0)),
                int(record.get("missed_payments", 0)),
                month
            ))
        
        conn.commit()
        conn.close()

    @classmethod
    def save_risk_record(cls, member_id: str, score: float, category: str, reasons: str, date_str: str = None):
        conn = cls.get_connection()
        cursor = conn.cursor()
        if not date_str:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO risk_history (member_id, risk_score, risk_category, analysis_date, reasons)
            VALUES (?, ?, ?, ?, ?)
        """, (member_id, score, category, date_str, reasons))
        conn.commit()
        conn.close()

    @classmethod
    def create_approval_escalation(cls, member_id: str, month: str, risk_level: str, reason: str):
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        # Check if approval item already exists for this month and member
        cursor.execute("""
            SELECT 1 FROM approvals WHERE member_id = ? AND ledger_month = ?
        """, (member_id, month))
        
        if not cursor.fetchone():
            updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO approvals (
                    member_id, ledger_month, risk_level, escalation_reason, 
                    field_officer_status, regional_coordinator_status, updated_at
                ) VALUES (?, ?, ?, ?, 'PENDING', 'PENDING', ?)
            """, (member_id, month, risk_level, reason, updated_at))
            conn.commit()
        conn.close()

    @classmethod
    def get_approval_queue(cls) -> List[Dict[str, Any]]:
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.member_id, a.ledger_month, a.risk_level, a.escalation_reason, 
                   a.field_officer_status, a.field_officer_comments,
                   a.regional_coordinator_status, a.regional_coordinator_comments,
                   a.updated_at, m.village, m.group_name
            FROM approvals a
            JOIN members m ON a.member_id = m.member_id
            ORDER BY a.id DESC
        """)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        return result

    @classmethod
    def update_field_officer_approval(cls, approval_id: int, status: str, comments: str):
        conn = cls.get_connection()
        cursor = conn.cursor()
        updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE approvals
            SET field_officer_status = ?, field_officer_comments = ?, updated_at = ?
            WHERE id = ?
        """, (status, comments, updated_at, approval_id))
        conn.commit()
        conn.close()

    @classmethod
    def update_regional_coordinator_approval(cls, approval_id: int, status: str, comments: str):
        conn = cls.get_connection()
        cursor = conn.cursor()
        updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE approvals
            SET regional_coordinator_status = ?, regional_coordinator_comments = ?, updated_at = ?
            WHERE id = ?
        """, (status, comments, updated_at, approval_id))
        conn.commit()
        conn.close()

    @classmethod
    def get_member_history(cls, member_id: str) -> Dict[str, Any]:
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        # Get member info
        cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
        member_row = cursor.fetchone()
        if not member_row:
            conn.close()
            return {}
            
        member_info = dict(member_row)
        
        # Get ledgers
        cursor.execute("SELECT * FROM ledgers WHERE member_id = ? ORDER BY ledger_month ASC", (member_id,))
        ledgers = [dict(r) for r in cursor.fetchall()]
        
        # Get risk history
        cursor.execute("SELECT * FROM risk_history WHERE member_id = ? ORDER BY analysis_date DESC", (member_id,))
        risks = [dict(r) for r in cursor.fetchall()]
        
        # Get approvals
        cursor.execute("SELECT * FROM approvals WHERE member_id = ? ORDER BY id DESC", (member_id,))
        approvals = [dict(r) for r in cursor.fetchall()]
        
        conn.close()
        return {
            "info": member_info,
            "ledgers": ledgers,
            "risks": risks,
            "approvals": approvals
        }
