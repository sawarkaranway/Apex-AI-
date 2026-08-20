"""
Policy Engine for Chaitanya Karya.
The application policy engine is authoritative for what is allowed to happen.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from agent.domain.enums import RiskLevel
from agent.policy.rules import evaluate_risk

class PolicyEvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    tool_name: str
    risk_level: RiskLevel
    requires_approval: bool
    allowed: bool
    impact_summary: str
    denial_reason: Optional[str] = None

class PolicyEngine:
    """
    Authoritative Policy Gate.
    Evaluates tool requests against safety constraints and human approval rules.
    """

    def evaluate(self, tool_name: str, arguments: Dict[str, Any]) -> PolicyEvaluationResult:
        risk_level, requires_approval, impact_summary = evaluate_risk(tool_name, arguments)

        # Immediate denial rule (e.g. attempting to delete system folders)
        if tool_name == "delete_file":
            path = str(arguments.get("file_path", "")).lower()
            if path in ["c:\\", "c:\\windows", "/", "/etc", "/root"]:
                return PolicyEvaluationResult(
                    tool_name=tool_name,
                    risk_level=RiskLevel.CRITICAL,
                    requires_approval=False,
                    allowed=False,
                    impact_summary="Target is a critical root directory.",
                    denial_reason="Operation strictly prohibited by system safety policy."
                )

        return PolicyEvaluationResult(
            tool_name=tool_name,
            risk_level=risk_level,
            requires_approval=requires_approval,
            allowed=True,
            impact_summary=impact_summary,
            denial_reason=None
        )

policy_engine = PolicyEngine()
