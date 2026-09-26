"""
DRAGON AI CORE
Security Intelligence Policy
"""

SECURITY_POLICY_VERSION = "1.2.0"

SECURITY_RULES = [
    "Do not execute unauthorized or unverified system commands.",
    "Enforce proper authorization and capability checks before executing file or network operations.",
    "Respect emergency kill switch controls at all times.",
    "Redact sensitive data such as passwords, API keys, and secret tokens in security audit logs.",
    "Do not engage in unauthorized offensive security actions.",
]


def get_security_rules():
    return SECURITY_RULES.copy()


def security_policy_version():
    return SECURITY_POLICY_VERSION


def evaluate_security_risk(action: str, capability: str, metadata: dict = None) -> dict:
    """
    Evaluates security risk level for a given action and capability.
    """
    action = str(action or "").lower().strip()
    capability = str(capability or "").lower().strip()

    high_risk_capabilities = {"file_delete", "system_commands", "offensive_security"}
    medium_risk_capabilities = {"file_write", "network"}

    if capability in high_risk_capabilities:
        return {
            "risk_level": "high",
            "action": action,
            "capability": capability,
            "requires_confirmation": True,
            "reason": f"Capability '{capability}' is classified as high security risk."
        }
    elif capability in medium_risk_capabilities:
        return {
            "risk_level": "medium",
            "action": action,
            "capability": capability,
            "requires_confirmation": False,
            "reason": f"Capability '{capability}' is classified as medium security risk."
        }
    else:
        return {
            "risk_level": "low",
            "action": action,
            "capability": capability,
            "requires_confirmation": False,
            "reason": f"Capability '{capability}' is classified as low security risk."
        }
