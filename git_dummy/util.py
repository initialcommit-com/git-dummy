import os
import subprocess

import typer


def is_dir_exist(path):
    return os.path.isdir(path)


def _git_dir_of(path, search_parents):
    args = ["git", "rev-parse", "--git-dir"]
    try:
        proc = subprocess.run(
            args,
            cwd=str(path),
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_CEILING_DIRECTORIES": "" if search_parents else os.path.dirname(str(path))},
        )
    except (FileNotFoundError, NotADirectoryError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def is_git_dir(path):
    """True when ``path`` itself is a repository (its own .git)."""
    if not is_dir_exist(path):
        return False
    if os.path.isdir(os.path.join(str(path), ".git")) or os.path.isfile(os.path.join(str(path), ".git")):
        return True
    # a bare repository
    return os.path.isfile(os.path.join(str(path), "HEAD")) and os.path.isdir(os.path.join(str(path), "objects"))


def is_inside_git_dir(path):
    """True when ``path`` or any parent is inside a repository."""
    path = str(path)
    while path and not is_dir_exist(path):
        parent = os.path.dirname(path)
        if parent == path:
            return False
        path = parent
    return _git_dir_of(path, search_parents=True) is not None


def is_valid_folder_name(name):
    allowed_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    if not name or not all(char in set(allowed_characters) for char in name):
        raise typer.BadParameter(
            f"only the following characters are permitted in the directory name: {allowed_characters}"
        )
    return name
