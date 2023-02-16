import pathlib
from pydantic import BaseSettings


class Settings(BaseSettings):
    name = "dummy"
    git_dir = pathlib.Path().cwd()
    commits = 5
    branches = 1
    diverge_at = 0
    merge = ""
    no_subdir = False

    class Config:
        env_prefix = "git_dummy_"


settings = Settings()
