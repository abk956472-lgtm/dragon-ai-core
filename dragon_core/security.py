"""
DRAGON AI CORE
Central Security Controller
"""

SECURITY_POLICY_VERSION = "1.2.0"

ALLOW_EXTERNAL_TOOLS = True

ALLOW_FILE_READ = True
ALLOW_FILE_WRITE = True
ALLOW_FILE_DELETE = True

ALLOW_NETWORK_ACCESS = True
ALLOW_SYSTEM_COMMANDS = True

ALLOW_DEFENSIVE_SECURITY_TASKS = True
ALLOW_OFFENSIVE_SECURITY_TASKS = False

ENABLE_SECURITY_LOG = True
STORE_SENSITIVE_DATA_BY_DEFAULT = False

REQUIRE_CONFIRMATION_FOR_SENSITIVE_ACTIONS = False


class SecurityController:
    def requires_confirmation(self) -> bool:
        return REQUIRE_CONFIRMATION_FOR_SENSITIVE_ACTIONS

    def is_allowed(self, capability: str) -> bool:
        permissions = {
            "external_tools": ALLOW_EXTERNAL_TOOLS,
            "file_read": ALLOW_FILE_READ,
            "file_write": ALLOW_FILE_WRITE,
            "file_delete": ALLOW_FILE_DELETE,
            "network": ALLOW_NETWORK_ACCESS,
            "system_commands": ALLOW_SYSTEM_COMMANDS,
            "defensive_security": ALLOW_DEFENSIVE_SECURITY_TASKS,
            "offensive_security": ALLOW_OFFENSIVE_SECURITY_TASKS,
        }

        return permissions.get(capability, False)


security = SecurityController()
