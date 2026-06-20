from typing import List, Dict, Any

class SessionMemory:
    _current_ledger: List[Dict[str, Any]] = []
    _current_month: str = "2026-06"
    _agent_outputs: Dict[str, Any] = {}
    _anomalies: List[Dict[str, Any]] = []
    _risk_scores: Dict[str, Any] = {}
    _recovery_rates: Dict[str, Any] = {}
    _approval_recommendations: List[Dict[str, Any]] = []
    _final_report: Dict[str, Any] = {}

    @classmethod
    def reset(cls, ledger_month: str = "2026-06"):
        cls._current_ledger = []
        cls._current_month = ledger_month
        cls._agent_outputs = {}
        cls._anomalies = []
        cls._risk_scores = {}
        cls._recovery_rates = {}
        cls._approval_recommendations = []
        cls._final_report = {}

    @classmethod
    def set_ledger(cls, ledger: List[Dict[str, Any]]):
        cls._current_ledger = ledger

    @classmethod
    def get_ledger(cls) -> List[Dict[str, Any]]:
        return cls._current_ledger

    @classmethod
    def get_month(cls) -> str:
        return cls._current_month

    @classmethod
    def set_agent_output(cls, agent_name: str, data: Any):
        cls._agent_outputs[agent_name] = data

    @classmethod
    def get_agent_outputs(cls) -> Dict[str, Any]:
        return cls._agent_outputs

    @classmethod
    def add_anomaly(cls, anomaly: Dict[str, Any]):
        cls._anomalies.append(anomaly)

    @classmethod
    def get_anomalies(cls) -> List[Dict[str, Any]]:
        return cls._anomalies

    @classmethod
    def set_risk_score(cls, member_id: str, score: float, category: str):
        cls._risk_scores[member_id] = {"score": score, "category": category}

    @classmethod
    def get_risk_scores(cls) -> Dict[str, Any]:
        return cls._risk_scores

    @classmethod
    def set_recovery_rate(cls, member_id: str, rate: float):
        cls._recovery_rates[member_id] = rate

    @classmethod
    def get_recovery_rates(cls) -> Dict[str, Any]:
        return cls._recovery_rates

    @classmethod
    def add_approval_recommendation(cls, rec: Dict[str, Any]):
        cls._approval_recommendations.append(rec)

    @classmethod
    def get_approval_recommendations(cls) -> List[Dict[str, Any]]:
        return cls._approval_recommendations

    @classmethod
    def set_final_report(cls, report: Dict[str, Any]):
        cls._final_report = report

    @classmethod
    def get_final_report(cls) -> Dict[str, Any]:
        return cls._final_report
