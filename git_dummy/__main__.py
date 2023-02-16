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
    diverge_at: int = typer.Option(
        settings.diverge_at,
        help="The point branches diverge from main at",
    ),
    merge: str = typer.Option(
        settings.merge,
        help="Comma separated branch ids to merge back into main",
    ),
    no_subdir: bool = typer.Option(
        settings.no_subdir,
        help="Initialize the dummy Git repo in the current directory instead of in a subdirectory",
    ),
):
    settings.name = name
    settings.commits = commits
    settings.branches = branches
    settings.diverge_at = diverge_at
    settings.merge = merge
    settings.no_subdir = no_subdir

    settings.git_dir = os.path.expanduser(git_dir)
    if not settings.no_subdir:
        settings.git_dir = os.path.join(settings.git_dir, settings.name)

    repo = git.Repo.init(settings.git_dir)
    repo.config_writer().set_value("init", "defaultBranch", "main").release()

    for c in range(1, settings.commits + 1):
        open(os.path.join(settings.git_dir, f"main.{c}"), "a").close()
        repo.index.add([f"main.{c}"])
        repo.index.commit(f"Dummy commit #{c} on main")

    while settings.branches - 1 > 0:
        repo.git.checkout("main")
        r = (
            (settings.commits - settings.diverge_at)
            if settings.diverge_at
            else random.choice(range(1, settings.commits))
        )
        repo.git.checkout(f"HEAD~{r}")
        branch_name = f"branch{settings.branches - 1}"
        repo.create_head(branch_name)
        repo.git.checkout(branch_name)
        for d in range(settings.commits - r + 1, settings.commits + 1):
            open(os.path.join(settings.git_dir, f"{branch_name}.{d}"), "a").close()
            repo.index.add([f"{branch_name}.{d}"])
            repo.index.commit(f"Dummy commit #{d} on {branch_name}")
        if settings.merge:
            to_merge = settings.merge.split(",")
            if str(settings.branches - 1) in to_merge:
                repo.git.checkout("main")
                main = repo.branches["main"]
                branch = repo.branches[branch_name]
                base = repo.git.merge_base(main, branch)
                repo.index.merge_tree(branch, base=base)
                repo.index.commit(
                    f"Merge {branch_name} into main",
                    parent_commits=(branch.commit, main.commit),
                )
                main.checkout(force=True)

        settings.branches -= 1

    repo.git.checkout("main")


if __name__ == "__main__":
    app()
