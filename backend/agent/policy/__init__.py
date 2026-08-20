"""
Agent Policy Package.
"""

from .engine import PolicyEngine, PolicyEvaluationResult, policy_engine
from .rules import evaluate_risk, verify_all_tools_have_policy, DEFAULT_TOOL_RISK_MAP

# Backwards compatibility alias
evaluate_tool_risk = evaluate_risk

__all__ = [
    "PolicyEngine",
    "PolicyEvaluationResult",
    "policy_engine",
    "evaluate_risk",
    "evaluate_tool_risk",
    "verify_all_tools_have_policy",
    "DEFAULT_TOOL_RISK_MAP",
]
