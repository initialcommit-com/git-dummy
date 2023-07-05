import pathlib
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    name: str = "dummy"
    git_dir: pathlib.Path = pathlib.Path().cwd()
    commits: int = 5
    branches: int = 1
    diverge_at: int = 0
    merge: str = ""
    no_subdir: bool = False
    constant_sha: bool = False

    class Config:
        env_prefix = "git_dummy_"


settings = Settings()
