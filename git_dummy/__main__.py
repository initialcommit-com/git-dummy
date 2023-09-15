import typer
import git
import pathlib
import os
import random
import sys

from git_dummy.settings import settings
from git_dummy.util import (
    is_dir_exist,
    is_git_dir,
    is_inside_git_dir,
    is_valid_folder_name,
)


app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.command()
def main(
    name: str = typer.Option(
        settings.name,
        help="Name of the dummy repo",
        callback=is_valid_folder_name,
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
    constant_sha: bool = typer.Option(
        settings.constant_sha,
        help="Use constant values for commit author, email, and commit date parameters to yield consistent sha1 values across git-dummy runs",
    ),
    allow_nested: bool = typer.Option(
        settings.allow_nested,
        help="Allow dummy repo creation within an existing Git repo, as long as it's not at the level of an existing .git/ folder",
    ),
):
    settings.name = name
    settings.commits = commits
    settings.branches = branches
    settings.diverge_at = diverge_at
    settings.merge = merge
    settings.no_subdir = no_subdir
    settings.constant_sha = constant_sha
    settings.allow_nested = allow_nested

    settings.git_dir = os.path.expanduser(git_dir)
    if not settings.no_subdir:
        settings.git_dir = os.path.join(settings.git_dir, settings.name)

    if is_git_dir(settings.git_dir):
        print(f"git-dummy error: Git repository already exists at {settings.git_dir}")
        sys.exit(1)

    if not settings.allow_nested and is_inside_git_dir(settings.git_dir):
        print(
            f"git-dummy error: Git repository already exists at {settings.git_dir} or parent: use --allow-nested flag to override"
        )
        sys.exit(1)

    print(
        f"git-dummy: Generating dummy Git repo at {settings.git_dir} with {settings.branches} branch(es) and {settings.commits} commit(s)."
    )

    repo = git.Repo.init(settings.git_dir, initial_branch="main")

    config_writer = repo.config_writer()
    config_writer.set_value("init", "defaultBranch", "main")
    if settings.constant_sha:
        config_writer.set_value("user", "name", "Git Dummy")
        config_writer.set_value("user", "email", "dumdum@git.dummy")
    config_writer.release()

    if settings.constant_sha:
        os.environ["GIT_AUTHOR_DATE"] = "2023-01-01T00:00:00"
        os.environ["GIT_COMMITTER_DATE"] = "2023-01-01T00:00:00"

    try:
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

    except Exception as e:
        raise e

    finally:
        # If needed, delete the environment variables set by git-dummy
        if settings.constant_sha:
            del os.environ["GIT_AUTHOR_DATE"]
            del os.environ["GIT_COMMITTER_DATE"]


if __name__ == "__main__":
    app()
