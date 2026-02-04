import os
from pathlib import Path


def normalize_path(path: str | os.PathLike[str]) -> Path:
    """
    Normalize a path by expanding user home directory and resolving to absolute path.

    :param path: Path string or PathLike that may contain ~ or relative components
    :return: Normalized absolute Path object
    :raises ValueError: If path is empty
    """
    if not path:
        raise ValueError("Path cannot be empty")
    return Path(path).expanduser().resolve()
