"""
Scientific Calculator Tool for Agent Architecture.
Wraps the deterministic math engine into an agent-callable tool contract.
"""

from typing import Dict, Any
from ..math_engine import parse_and_calculate


def scientific_calculator(query: str, expression: str = "") -> str:
    """
    Deterministically computes mathematical calculations, algebra, calculus, 
    statistics, linear algebra, unit conversions, and financial math.
    Returns exact symbolic answer, approximate decimal value, step-by-step breakdown, and formula.
    """
    res = parse_and_calculate(query=query, explicit_expression=expression)
    if res.get("status") == "error":
        msg = res.get("message", "Calculation error.")
        sug = res.get("suggestion", "")
        err_type = res.get("error_type", "error")
        return f"❌ Mathematical Error [{err_type}]: {msg}" + (f"\n💡 Suggestion: {sug}" if sug else "")

    exact = res.get("exact_answer", "")
    approx = res.get("approximate_answer", "")
    formula = res.get("formula_used", "")
    steps = res.get("steps", [])
    verif = res.get("verification", {})

    output_lines = [
        f"🔢 **Result**: `{exact}`" + (f" (≈ `{approx}`)" if approx and approx != exact else ""),
    ]
    if formula:
        output_lines.append(f"📐 **Formula Used**: {formula}")

    if steps:
        output_lines.append("\n📝 **Step-by-Step Solution**:")
        for step in steps:
            output_lines.append(f"• {step}")

    if verif and verif.get("performed"):
        v_passed = "✅ Passed" if verif.get("passed") else "⚠️ Warning"
        output_lines.append(f"\n🔍 **Verification**: {v_passed} — {verif.get('details', '')}")

    return "\n".join(output_lines)
