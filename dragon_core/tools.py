"""
DRAGON AI CORE
Tool Engine - File Operations
"""

from pathlib import Path

from .security import security


def read_file(path: str) -> str:
    """
    Read a UTF-8 text file after security validation.
    """

    if not security.is_allowed("file_read"):
        raise PermissionError(
            "File reading is disabled."
        )

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if not file_path.is_file():
        raise IsADirectoryError(
            f"Path is not a file: {path}"
        )

    return file_path.read_text(
        encoding="utf-8"
    )


def write_file(
    path: str,
    content: str
) -> bool:
    """
    Write UTF-8 text to a file after
    security validation.
    """

    if not security.is_allowed("file_write"):
        raise PermissionError(
            "File writing is disabled."
        )

    file_path = Path(path)

    file_path.write_text(
        str(content),
        encoding="utf-8"
    )

    return True


def delete_file(
    path: str
) -> bool:
    """
    Delete a file after security validation.
    """

    if not security.is_allowed("file_delete"):
        raise PermissionError(
            "File deletion is disabled."
        )

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if not file_path.is_file():
        raise IsADirectoryError(
            f"Path is not a file: {path}"
        )

    file_path.unlink()

    return True
