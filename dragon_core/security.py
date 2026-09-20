from policies.security_policy import (
    REQUIRE_CONFIRMATION_FOR_SENSITIVE_ACTIONS,
    ALLOW_UNAUTHORIZED_ACTIONS,
    ALLOW_DEFENSIVE_SECURITY_TASKS,
    ALLOW_OFFENSIVE_SECURITY_TASKS,
    ALLOW_EXTERNAL_TOOLS,
    ALLOW_FILE_READ,
    ALLOW_FILE_WRITE,
    ALLOW_FILE_DELETE,
    ALLOW_NETWORK_ACCESS,
    ALLOW_SYSTEM_COMMANDS,
)


class SecurityManager:
    def can_execute(self, action: str) -> bool:
        if not ALLOW_UNAUTHORIZED_ACTIONS:
            return False

        if action == "defensive_security":
            return ALLOW_DEFENSIVE_SECURITY_TASKS

        if action == "offensive_security":
            return ALLOW_OFFENSIVE_SECURITY_TASKS

        if action == "external_tool":
            return ALLOW_EXTERNAL_TOOLS

        if action == "file_read":
            return ALLOW_FILE_READ

        if action == "file_write":
            return ALLOW_FILE_WRITE

        if action == "file_delete":
            return ALLOW_FILE_DELETE

        if action == "network":
            return ALLOW_NETWORK_ACCESS

        if action == "system_command":
            return ALLOW_SYSTEM_COMMANDS

        return False

    def requires_confirmation(self) -> bool:
        return REQUIRE_CONFIRMATION_FOR_SENSITIVE_ACTIONS


security = SecurityManager()
