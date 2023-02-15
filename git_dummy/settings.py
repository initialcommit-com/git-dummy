import pathlib
from pydantic import BaseSettings


class Settings(BaseSettings):
    name = "dummy"
    git_dir = pathlib.Path().cwd()
    commits = 5
    branches = 1

    class Config:
        env_prefix = "git_dummy_"


settings = Settings()
