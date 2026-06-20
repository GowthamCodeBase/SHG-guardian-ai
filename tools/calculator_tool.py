class CalculatorTool:
    @staticmethod
    def calculate_recovery_rate(actual_paid: float, monthly_due: float) -> float:
        """Calculates recovery rate safely. Monthly due can be 0 (cleared loan)."""
        try:
            actual_paid = float(actual_paid)
            monthly_due = float(monthly_due)
            if monthly_due <= 0:
                # If nothing is due and they paid something or nothing, rate is 1.0 (fully recovered / safe)
                return 1.0 if actual_paid >= 0 else 0.0
            
            rate = actual_paid / monthly_due
            # Cap recovery rate logically or keep it as is (prepayments are possible)
            return round(rate, 4)
        except Exception:
            return 0.0

    @staticmethod
    def calculate_outstanding_to_savings_ratio(outstanding_loan: float, savings: float) -> float:
        """Calculates ratio of outstanding loan to total savings."""
        try:
            outstanding_loan = float(outstanding_loan)
            savings = float(savings)
            if savings <= 0:
                # Negative savings is anomalous, handled by anomaly agent.
                # If savings is 0 and they have outstanding loan, it's 100% (high ratio)
                return float('inf') if outstanding_loan > 0 else 0.0
            return round(outstanding_loan / savings, 4)
        except Exception:
            return 0.0

    @staticmethod
    def calculate_repayment_shortfall(monthly_due: float, actual_paid: float) -> float:
        """Calculates the absolute unpaid amount for the month."""
        try:
            due = float(monthly_due)
            paid = float(actual_paid)
            return max(0.0, due - paid)
        except Exception:
            return 0.0
