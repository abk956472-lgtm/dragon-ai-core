"""
DRAGON AI CORE
Central Security Controller

Security Layer
- Permission Management
- Capability Checks
- Audit Logging
- Sensitive Action Confirmation
- Defensive / Offensive Security Policy
- Kill Switch
"""

from datetime import datetime
from threading import Lock
from typing import Optional


# ==========================================================
# Security Policy
# ==========================================================

SECURITY_POLICY_VERSION = "1.3.0"


# ==========================================================
# Global Capabilities
# ==========================================================

ALLOW_EXTERNAL_TOOLS = True

ALLOW_FILE_READ = True
ALLOW_FILE_WRITE = True
ALLOW_FILE_DELETE = True

ALLOW_NETWORK_ACCESS = True
ALLOW_SYSTEM_COMMANDS = True

ALLOW_DEFENSIVE_SECURITY_TASKS = True
ALLOW_OFFENSIVE_SECURITY_TASKS = False


# ==========================================================
# Security Logging
# ==========================================================

ENABLE_SECURITY_LOG = True

STORE_SENSITIVE_DATA_BY_DEFAULT = False


# ==========================================================
# Confirmation Policy
# ==========================================================

REQUIRE_CONFIRMATION_FOR_SENSITIVE_ACTIONS = False


# ==========================================================
# Emergency Kill Switch
# ==========================================================

SECURITY_KILL_SWITCH = False


# ==========================================================
# Security Controller
# ==========================================================

class SecurityController:
    """
    Central security controller for DRAGON AI CORE.

    This class controls whether a capability is allowed
    before an external operation is executed.

    Important:

    This controller does not execute tools itself.

    It only controls authorization and security policy.
    """

    def __init__(self):

        self._lock = Lock()

        self._security_log = []

        self._permissions = {
            "external_tools":
                ALLOW_EXTERNAL_TOOLS,

            "file_read":
                ALLOW_FILE_READ,

            "file_write":
                ALLOW_FILE_WRITE,

            "file_delete":
                ALLOW_FILE_DELETE,

            "network":
                ALLOW_NETWORK_ACCESS,

            "system_commands":
                ALLOW_SYSTEM_COMMANDS,

            "defensive_security":
                ALLOW_DEFENSIVE_SECURITY_TASKS,

            "offensive_security":
                ALLOW_OFFENSIVE_SECURITY_TASKS,
        }

    # ======================================================
    # Confirmation
    # ======================================================

    def requires_confirmation(
        self
    ) -> bool:

        return (
            REQUIRE_CONFIRMATION_FOR_SENSITIVE_ACTIONS
        )

    # ======================================================
    # Kill Switch
    # ======================================================

    def is_kill_switch_active(
        self
    ) -> bool:

        return SECURITY_KILL_SWITCH

    # ======================================================
    # Capability Check
    # ======================================================

    def is_allowed(
        self,
        capability: str
    ) -> bool:
        """
        Check whether a capability is allowed.

        Kill switch always overrides permissions.
        """

        capability = str(
            capability or ""
        ).strip().lower()

        # Emergency stop
        if self.is_kill_switch_active():
            self.log_event(
                action="permission_check",
                capability=capability,
                status="blocked",
                reason="security_kill_switch"
            )

            return False

        allowed = self._permissions.get(
            capability,
            False
        )

        self.log_event(
            action="permission_check",
            capability=capability,
            status=(
                "allowed"
                if allowed
                else "blocked"
            ),
            reason=(
                "policy"
                if allowed
                else "capability_not_allowed"
            )
        )

        return allowed

    # ======================================================
    # Permission Alias
    # ======================================================

    def has_permission(
        self,
        capability: str
    ) -> bool:

        return self.is_allowed(
            capability
        )

    # ======================================================
    # Sensitive Action Check
    # ======================================================

    def can_execute(
        self,
        capability: str,
        sensitive: bool = False
    ) -> bool:
        """
        Final permission check before a tool executes.

        Examples:

            security.can_execute(
                "file_read"
            )

            security.can_execute(
                "system_commands",
                sensitive=True
            )
        """

        if not self.is_allowed(
            capability
        ):
            return False

        if (
            sensitive
            and self.requires_confirmation()
        ):

            self.log_event(
                action="sensitive_action",
                capability=capability,
                status="confirmation_required",
                reason="sensitive_action_policy"
            )

            return False

        return True

    # ======================================================
    # Update Permission
    # ======================================================

    def set_permission(
        self,
        capability: str,
        allowed: bool
    ) -> bool:
        """
        Change a runtime permission.

        This does not modify the global constants.
        It only changes the current controller state.
        """

        capability = str(
            capability or ""
        ).strip().lower()

        if capability not in self._permissions:
            return False

        with self._lock:

            self._permissions[
                capability
            ] = bool(allowed)

        self.log_event(
            action="permission_update",
            capability=capability,
            status=(
                "allowed"
                if allowed
                else "blocked"
            ),
            reason="runtime_permission_change"
        )

        return True

    # ======================================================
    # Get Permissions
    # ======================================================

    def get_permissions(
        self
    ) -> dict:

        with self._lock:

            return dict(
                self._permissions
            )

    # ======================================================
    # Audit Log
    # ======================================================

    def log_event(
        self,
        action: str,
        capability: Optional[str] = None,
        status: str = "unknown",
        reason: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Store a security event.

        Sensitive values should not be stored here
        unless explicitly required.
        """

        if not ENABLE_SECURITY_LOG:
            return

        event = {
            "timestamp":
                datetime.utcnow().isoformat(),

            "action":
                str(action),

            "capability":
                capability,

            "status":
                str(status),

            "reason":
                reason,

            "metadata":
                metadata or {}
        }

        with self._lock:

            self._security_log.append(
                event
            )

            # Prevent unlimited memory growth
            if len(
                self._security_log
            ) > 1000:

                self._security_log = (
                    self._security_log[-1000:]
                )

    # ======================================================
    # Get Audit Log
    # ======================================================

    def get_security_log(
        self,
        limit: int = 100
    ) -> list:

        try:
            limit = int(limit)
        except (
            TypeError,
            ValueError
        ):
            limit = 100

        limit = max(
            1,
            min(limit, 1000)
        )

        with self._lock:

            return list(
                self._security_log[-limit:]
            )

    # ======================================================
    # Clear Audit Log
    # ======================================================

    def clear_security_log(
        self
    ):

        with self._lock:
            self._security_log.clear()

    # ======================================================
    # Security Status
    # ======================================================

    def get_status(
        self
    ) -> dict:

        return {
            "policy_version":
                SECURITY_POLICY_VERSION,

            "kill_switch":
                self.is_kill_switch_active(),

            "confirmation_required":
                self.requires_confirmation(),

            "permissions":
                self.get_permissions(),

            "security_log_enabled":
                ENABLE_SECURITY_LOG,

            "sensitive_data_storage":
                STORE_SENSITIVE_DATA_BY_DEFAULT
        }


# ==========================================================
# Global Security Controller
# ==========================================================

security = SecurityController()
