from pathlib import Path

from .security import security


def read_file(path: str) -> str:
    if not security.can_execute("file_read"):
        raise PermissionError("File reading is disabled.")

    return Path(path).read_text(encoding="utf-8")


def write_file(path: str, content: str) -> bool:
    if not security.can_execute("file_write"):
        raise PermissionError("File writing is disabled.")

    Path(path).write_text(content, encoding="utf-8")
    return True


def delete_file(path: str) -> bool:
    if not
