"""
DRAGON AI CORE
Central Security Policy
"""

SECURITY_POLICY_VERSION = "1.1.0"

# General permissions
REQUIRE_CONFIRMATION_FOR_SENSITIVE_ACTIONS = False

# Core capabilities
ALLOW_EXTERNAL_TOOLS = True

# File operations
ALLOW_FILE_READ = True
ALLOW_FILE_WRITE = True
ALLOW_FILE_DELETE = True

# Network operations
ALLOW_NETWORK_ACCESS = True

# System administration
ALLOW_SYSTEM_COMMANDS = True

# Defensive security
ALLOW_DEFENSIVE_SECURITY_TASKS = True

# Offensive security remains disabled
ALLOW_OFFENSIVE_SECURITY_TASKS = False

# Security logging
ENABLE_SECURITY_LOG = True

# Privacy
STORE_SENSITIVE_DATA_BY_DEFAULT = False
