"""
DRAGON AI CORE
Tool Engine - File Operations
"""

from pathlib import Path

from .security import security


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _check_permission(capability: str) -> None:
    """
    Check whether the requested file capability
    is allowed by DRAGON SecurityController.
    """

    if not security.is_allowed(capability):
        raise PermissionError(
            f"Operation disabled by security policy: {capability}"
        )


def _get_file(path: str) -> Path:
    """
    Convert a path to a normalized Path object
    and validate the basic input.
    """

    if not isinstance(path, str):
        raise TypeError(
            "File path must be a string."
        )

    path = path.strip()

    if not path:
        raise ValueError(
            "File path cannot be empty."
        )

    return Path(path).expanduser()


# =========================================================
# FILE READ
# =========================================================

def read_file(path: str) -> str:
    """
    Read a UTF-8 text file after security validation.
    """

    _check_permission("file_read")

    file_path = _get_file(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if not file_path.is_file():
        raise IsADirectoryError(
            f"Path is not a file: {file_path}"
        )

    try:
        return file_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError as exc:
        raise UnicodeError(
            f"File is not valid UTF-8 text: {file_path}"
        ) from exc


# =========================================================
# FILE WRITE
# =========================================================

def write_file(
    path: str,
    content: str
) -> bool:
    """
    Write UTF-8 text to a file after
    security validation.

    Existing files are overwritten.
    Parent directories are created when necessary.
    """

    _check_permission("file_write")

    file_path = _get_file(path)

    if file_path.exists() and not file_path.is_file():
        raise IsADirectoryError(
            f"Path is not a file: {file_path}"
        )

    if not isinstance(content, str):
        content = str(content)

    parent = file_path.parent

    if (
        str(parent)
        not in ("", ".")
    ):
        parent.mkdir(
            parents=True,
            exist_ok=True
        )

    file_path.write_text(
        content,
        encoding="utf-8"
    )

    return True


# =========================================================
# FILE DELETE
# =========================================================

def delete_file(
    path: str
) -> bool:
    """
    Delete a file after security validation.
    """

    _check_permission("file_delete")

    file_path = _get_file(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if not file_path.is_file():
        raise IsADirectoryError(
            f"Path is not a file: {file_path}"
        )

    file_path.unlink()

    return True


# =========================================================
# TOOL STATUS
# =========================================================

def get_file_tool_status() -> dict:
    """
    Return the current file-operation permissions.

    This does not perform any file operation.
    """

    return {
        "file_read": security.is_allowed(
            "file_read"
        ),
        "file_write": security.is_allowed(
            "file_write"
        ),
        "file_delete": security.is_allowed(
            "file_delete"
        ),
    }
