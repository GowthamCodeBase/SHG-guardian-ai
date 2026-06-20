from memory.database import DatabaseManager
from tools.calculator_tool import CalculatorTool

class PredictionTool:
    @staticmethod
    def predict_default_probability(record: dict) -> float:
        """
        Estimates the probability (0.0 to 1.0) of a member defaulting in the next 3 months
        based on current financials and historical trends stored in the database.
        """
        try:
            savings = float(record.get("savings", 0.0))
            loan_amount = float(record.get("loan_amount", 0.0))
            outstanding_loan = float(record.get("outstanding_loan", 0.0))
            monthly_due = float(record.get("monthly_due", 0.0))
            actual_paid = float(record.get("actual_paid", 0.0))
            missed_payments = int(record.get("missed_payments", 0))
            member_id = record.get("member_id")

            # If outstanding loan is already 0, risk of default is 0
            if outstanding_loan <= 0:
                return 0.0

            # 1. Base probability
            probability = 0.05

            # 2. Missed payments contribution
            if missed_payments > 0:
                probability += min(0.60, missed_payments * 0.15)
                if missed_payments >= 4:
                    probability += 0.15

            # 3. Recovery rate contribution
            rec_rate = CalculatorTool.calculate_recovery_rate(actual_paid, monthly_due)
            if rec_rate < 0.60:
                probability += 0.20
            if rec_rate == 0.0:
                probability += 0.15

            # 4. Debt to savings ratio contribution
            ratio = CalculatorTool.calculate_outstanding_to_savings_ratio(outstanding_loan, savings)
            if ratio > 5.0:
                probability += 0.15
            elif ratio > 3.0:
                probability += 0.10

            # 5. Historical database trend analysis
            if member_id:
                history = DatabaseManager.get_member_history(member_id)
                risks = history.get("risks", [])
                if len(risks) >= 2:
                    # Check if risk score has been increasing over time
                    # risks is ordered by analysis_date DESC, so risks[0] is latest, risks[1] is previous
                    latest_score = risks[0].get("risk_score", 0.0)
                    prev_score = risks[1].get("risk_score", 0.0)
                    if latest_score > prev_score:
                        probability += 0.10  # Upward risk trend increases default prediction probability

            # Cap between 0% and 100%
            probability = min(1.0, max(0.0, probability))
            return round(probability, 4)

        except Exception as e:
            print(f"Error in prediction tool: {e}")
            return 0.5  # Fallback neutral default probability
