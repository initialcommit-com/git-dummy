"""Defaults for the command line, each overridable through an environment
variable named git_dummy_<option> (git_dummy_commits=10, git_dummy_style=realistic)."""

import pathlib
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="git_dummy_")

    name: str = "dummy"
    git_dir: pathlib.Path = pathlib.Path().cwd()
    commits: int = 5
    branches: int = 1
    diverge_at: int = 0
    merge: str = ""
    no_subdir: bool = False
    constant_sha: bool = False
    allow_nested: bool = False

    style: str = "plain"
    seed: Optional[int] = None
    branch_names: str = ""
    tags: str = ""
    files: int = 0
    remote: bool = False
    ahead: int = 0
    behind: int = 0
    modified: int = 0
    staged: int = 0
    untracked: int = 0
    stashes: int = 0
    reflog: int = 0


settings = Settings()
