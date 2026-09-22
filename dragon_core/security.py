"""
DRAGON AI CORE
Central Security Controller

Security Layer
- Permission Management
- Capability Checks
- Audit Logging
- Sensitive Action Confirmation
- Defensive / Offensive Security Policy
- Emergency Kill Switch
"""

from datetime import datetime, timezone
from threading import Lock
from typing import Optional, Dict, Any


# ==========================================================
# Security Policy
# ==========================================================

SECURITY_POLICY_VERSION = "1.4.0"


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

    This class is responsible for authorization,
    capability checks, security logging and
    emergency control.

    It does not execute tools itself.
    """

    def __init__(self):

        self._lock = Lock()

        self._security_log = []

        self._permissions = {
            "external_tools": ALLOW_EXTERNAL_TOOLS,

            "file_read": ALLOW_FILE_READ,
            "file_write": ALLOW_FILE_WRITE,
            "file_delete": ALLOW_FILE_DELETE,

            "network": ALLOW_NETWORK_ACCESS,
            "system_commands": ALLOW_SYSTEM_COMMANDS,

            "defensive_security":
                ALLOW_DEFENSIVE_SECURITY_TASKS,

            "offensive_security":
                ALLOW_OFFENSIVE_SECURITY_TASKS,
        }

        self._kill_switch = bool(
            SECURITY_KILL_SWITCH
        )

        self._confirmation_required = bool(
            REQUIRE_CONFIRMATION_FOR_SENSITIVE_ACTIONS
        )

    # ======================================================
    # Internal Helpers
    # ======================================================

    @staticmethod
    def _normalize_capability(
        capability: str
    ) -> str:

        return str(
            capability or ""
        ).strip().lower()

    # ======================================================
    # Confirmation
    # ======================================================

    def requires_confirmation(
        self
    ) -> bool:

        with self._lock:

            return self._confirmation_required

    # ======================================================
    # Update Confirmation Policy
    # ======================================================

    def set_confirmation_required(
        self,
        required: bool
    ) -> bool:

        required = bool(required)

        with self._lock:

            self._confirmation_required = required

        self.log_event(
            action="confirmation_policy_update",
            status=(
                "enabled"
                if required
                else "disabled"
            ),
            reason="runtime_policy_change"
        )

        return True

    # ======================================================
    # Kill Switch
    # ======================================================

    def is_kill_switch_active(
        self
    ) -> bool:

        with self._lock:

            return self._kill_switch

    # ======================================================
    # Activate / Deactivate Kill Switch
    # ======================================================

    def set_kill_switch(
        self,
        active: bool
    ) -> bool:

        active = bool(active)

        with self._lock:

            self._kill_switch = active

        self.log_event(
            action="kill_switch_update",
            status=(
                "active"
                if active
                else "inactive"
            ),
            reason="runtime_security_control"
        )

        return True

    # ======================================================
    # Capability Check
    # ======================================================

    def is_allowed(
        self,
        capability: str
    ) -> bool:
        """
        Check whether a capability is allowed.

        The emergency kill switch always
        overrides normal permissions.
        """

        capability = self._normalize_capability(
            capability
        )

        if self.is_kill_switch_active():

            self.log_event(
                action="permission_check",
                capability=capability,
                status="blocked",
                reason="security_kill_switch"
            )

            return False

        with self._lock:

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
    # Capability Exists
    # ======================================================

    def is_capability_known(
        self,
        capability: str
    ) -> bool:

        capability = self._normalize_capability(
            capability
        )

        with self._lock:

            return capability in self._permissions

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
        Final authorization check before
        a tool or external operation executes.
        """

        capability = self._normalize_capability(
            capability
        )

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

        self.log_event(
            action="tool_authorization",
            capability=capability,
            status="authorized",
            reason="security_policy"
        )

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

        This changes only the current controller
        state and does not modify global constants.
        """

        capability = self._normalize_capability(
            capability
        )

        with self._lock:

            if capability not in self._permissions:
                return False

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
    # Reset Permissions
    # ======================================================

    def reset_permissions(
        self
    ) -> bool:
        """
        Restore permissions to the original
        global policy values.
        """

        defaults = {
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

        with self._lock:

            self._permissions = dict(
                defaults
            )

        self.log_event(
            action="permission_reset",
            status="completed",
            reason="restore_default_policy"
        )

        return True

    # ======================================================
    # Get Permissions
    # ======================================================

    def get_permissions(
        self
    ) -> Dict[str, bool]:

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
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store a security event.

        Security logs should not contain secrets,
        API keys, passwords or sensitive payloads.
        """

        if not ENABLE_SECURITY_LOG:
            return

        safe_metadata = {}

        if isinstance(
            metadata,
            dict
        ):

            for key, value in metadata.items():

                key_string = str(
                    key
                ).lower()

                blocked_keys = {
                    "password",
                    "passwd",
                    "api_key",
                    "apikey",
                    "token",
                    "access_token",
                    "refresh_token",
                    "secret",
                    "authorization",
                    "cookie"
                }

                if key_string in blocked_keys:
                    safe_metadata[key] = "[REDACTED]"
                else:
                    safe_metadata[key] = value

        event = {
            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "action":
                str(action),

            "capability":
                capability,

            "status":
                str(status),

            "reason":
                reason,

            "metadata":
                safe_metadata
        }

        with self._lock:

            self._security_log.append(
                event
            )

            # Prevent unlimited memory growth.
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

            limit = int(
                limit
            )

        except (
            TypeError,
            ValueError
        ):

            limit = 100

        limit = max(
            1,
            min(
                limit,
                1000
            )
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
    ) -> bool:

        with self._lock:

            self._security_log.clear()

        return True

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
                STORE_SENSITIVE_DATA_BY_DEFAULT,

            "capabilities":
                list(
                    self.get_permissions().keys()
                )
        }


# ==========================================================
# Global Security Controller
# ==========================================================

security = SecurityController()
