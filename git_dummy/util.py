import git
import os
import typer


def is_dir_exist(path):
    if os.path.exists(path) and os.path.isdir(path):
        return True
    return False


def is_git_dir(path):
    try:
        git.Repo(path)
        return True
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
        return False


def is_inside_git_dir(path):
    while not is_dir_exist(path):
        try:
            git.Repo(path, search_parent_directories=True)
            return True
        except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
            path = os.path.dirname(path)
    else:
        try:
            git.Repo(path, search_parent_directories=True)
            return True
        except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
            return False


def is_valid_folder_name(name):
    allowed_characters = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    )
    is_valid = all(char in set(allowed_characters) for char in name)
    if not is_valid:
        raise typer.BadParameter(
            f"only the following characters are permitted in the directory name: {allowed_characters}"
        )
    return name
