import typer
import git
import pathlib
import os
import random

from git_dummy.settings import settings

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.command()
def main(
    name: str = typer.Option(
        settings.name,
        help="Name of the dummy repo",
    ),
    git_dir: pathlib.Path = typer.Option(
        settings.git_dir,
        help="The path in which to create the dummy Git repo",
    ),
    commits: int = typer.Option(
        settings.commits,
        help="The number of commits to generate",
    ),
    branches: int = typer.Option(
        settings.branches,
        help="The number of branches to generate",
    ),
):
    settings.name = name
    settings.git_dir = os.path.join(os.path.expanduser(git_dir), name)
    settings.commits = commits
    settings.branches = branches

    repo = git.Repo.init(settings.git_dir)
    repo.config_writer().set_value("init", "defaultBranch", "main").release()

    for c in range(1, settings.commits + 1):
        open(os.path.join(settings.git_dir, f"main.{c}"), "a").close()
        repo.index.add([f"main.{c}"])
        repo.index.commit(f"Dummy commit #{c} on main")

    while settings.branches - 1 > 0:
        repo.git.checkout("main")
        r = random.choice(range(1, settings.commits))
        repo.git.checkout(f"HEAD~{r}")
        branch_name = f"branch{settings.branches - 1}"
        repo.create_head(branch_name)
        repo.git.checkout(branch_name)
        for d in range(settings.commits - r + 1, settings.commits + 1):
            open(os.path.join(settings.git_dir, f"{branch_name}.{d}"), "a").close()
            repo.index.add([f"{branch_name}.{d}"])
            repo.index.commit(f"Dummy commit #{d} on {branch_name}")

        settings.branches -= 1

    repo.git.checkout("main")


if __name__ == "__main__":
    app()
