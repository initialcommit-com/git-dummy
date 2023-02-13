import typer
import git
import pathlib
import os

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
):
    settings.name = name
    settings.git_dir = os.path.join(git_dir, name)
    settings.commits = commits

    repo = git.Repo.init(settings.git_dir)

    for i in range(1, settings.commits + 1):
        open(os.path.join(settings.git_dir, str(i)), "a").close()
        repo.index.add([str(i)])
        repo.index.commit(f"Dummy commit #{i}")


if __name__ == "__main__":
    app()
