import json
import os
import pathlib
import sys
from typing import Optional

import typer

from git_dummy import scenarios
from git_dummy.builder import BuildError, Builder, clean as clean_repo, script as make_script
from git_dummy.settings import settings
from git_dummy.spec import Spec
from git_dummy.util import is_valid_folder_name

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, add_completion=False)


def _list(value: str):
    return [p.strip() for p in (value or "").split(",") if p.strip()]


@app.command()
def main(
    name: str = typer.Option(settings.name, help="Name of the dummy repo", callback=is_valid_folder_name),
    git_dir: pathlib.Path = typer.Option(settings.git_dir, help="The path in which to create the dummy Git repo"),
    commits: int = typer.Option(settings.commits, help="The number of commits to generate"),
    branches: int = typer.Option(settings.branches, help="The number of branches to generate"),
    diverge_at: int = typer.Option(settings.diverge_at, help="The point branches diverge from main at"),
    merge: str = typer.Option(settings.merge, help="Comma separated branch ids to merge back into main"),
    no_subdir: bool = typer.Option(settings.no_subdir, help="Initialize the dummy Git repo in the current directory instead of in a subdirectory"),
    constant_sha: bool = typer.Option(settings.constant_sha, help="Use constant values for commit author, email, and commit date parameters to yield consistent sha1 values across git-dummy runs"),
    allow_nested: bool = typer.Option(settings.allow_nested, help="Allow dummy repo creation within an existing Git repo, as long as it's not at the level of an existing .git/ folder"),
    # what the history looks like
    style: str = typer.Option(settings.style, help="plain: main.1 files and 'Dummy commit #1' messages; realistic: a small web service with real-looking files, messages and authors"),
    seed: Optional[int] = typer.Option(settings.seed, help="Seed for every random choice (divergence points, content, authors) and for fixed commit dates, so the same seed gives the same repository"),
    branch_names: str = typer.Option(settings.branch_names, help="Comma separated names for the branches other than main (default branch1, branch2, ... or realistic names)"),
    tags: str = typer.Option(settings.tags, help="Comma separated tags to place along main, the last on its tip"),
    files: int = typer.Option(settings.files, help="Extra files added by every commit on main, for large trees"),
    octopus: bool = typer.Option(False, help="Merge the unmerged branches into main in one octopus merge"),
    criss_cross: bool = typer.Option(False, help="Make main and the first branch each merge the other (a criss-cross history)"),
    orphan_branch: Optional[str] = typer.Option(None, help="Add a branch with its own root and a single page, like gh-pages"),
    fast: Optional[bool] = typer.Option(None, "--fast/--no-fast", help="Write the history with git fast-import (default: only when it is large)"),
    # a remote
    remote: bool = typer.Option(settings.remote, help="Create a bare remote beside the repo, push everything to it and track it as origin"),
    ahead: int = typer.Option(settings.ahead, help="Commits on local main that the remote does not have (needs --remote)"),
    behind: int = typer.Option(settings.behind, help="Commits the remote gained since the last fetch (needs --remote)"),
    # the working tree
    modified: int = typer.Option(settings.modified, help="Tracked files with uncommitted edits"),
    staged: int = typer.Option(settings.staged, help="Tracked files with edits staged for the next commit"),
    untracked: int = typer.Option(settings.untracked, help="New files Git does not track yet"),
    conflict: bool = typer.Option(False, help="Leave a merge stopped on a conflict, markers in the file"),
    stashes: int = typer.Option(settings.stashes, help="Entries on the stash"),
    reflog: int = typer.Option(settings.reflog, help="Extra HEAD moves so the reflog has entries"),
    detached: bool = typer.Option(False, help="Leave HEAD detached at the commit before the tip"),
    checkout: Optional[str] = typer.Option(None, help="The branch to leave checked out (default main)"),
    worktree: Optional[str] = typer.Option(None, help="Add a linked worktree beside the repo, checked out on this branch"),
    submodule: bool = typer.Option(False, help="Add a submodule pinned to a small library repo built beside this one"),
    # recipes, scenarios, output
    scenario: Optional[str] = typer.Option(None, help="Start from a named scenario (see --list-scenarios); other options override it"),
    list_scenarios: bool = typer.Option(False, "--list-scenarios", help="List the named scenarios and exit"),
    recipe: Optional[pathlib.Path] = typer.Option(None, "--from", help="Read the options from a JSON or YAML recipe file"),
    json_out: bool = typer.Option(False, "--json", help="Print what was built as JSON (paths, branches, tags, commits, states) instead of a message"),
    print_script: bool = typer.Option(False, "--print-script", help="Print the plain git commands that would build the repo, and build nothing"),
    clean: bool = typer.Option(False, "--clean", help="Remove the dummy repo at the target path (and what git-dummy made beside it), refusing anything git-dummy did not make"),
):
    if list_scenarios:
        width = max(len(n) for n in scenarios.names())
        for n in scenarios.names():
            typer.echo(f"{n:<{width}}  {scenarios.describe(n)}")
        return

    try:
        if recipe is not None:
            spec = Spec.from_recipe(str(recipe))
        else:
            spec = Spec()
        if scenario is not None:
            spec = scenarios.apply_scenario(scenario, spec)

        # Explicit options win over the recipe and the scenario; unchanged
        # defaults are left alone so a scenario's choices survive.
        defaults = Spec()
        given = dict(
            name=name, git_dir=str(git_dir), commits=commits, branches=branches, diverge_at=diverge_at,
            merge=_list(merge), no_subdir=no_subdir, constant_sha=constant_sha, allow_nested=allow_nested,
            style=style, seed=seed, branch_names=_list(branch_names), tags=_list(tags), files=files,
            octopus=octopus, criss_cross=criss_cross, orphan_branch=orphan_branch, fast=fast,
            remote=remote, ahead=ahead, behind=behind, modified=modified, staged=staged, untracked=untracked,
            conflict=conflict, stashes=stashes, reflog=reflog, detached=detached, checkout=checkout,
            worktree=worktree, submodule=submodule,
        )
        cli_defaults = Spec.from_dict(dict(
            name=settings.name, git_dir=str(settings.git_dir), commits=settings.commits, branches=settings.branches,
            diverge_at=settings.diverge_at, merge=_list(settings.merge), no_subdir=settings.no_subdir,
            constant_sha=settings.constant_sha, allow_nested=settings.allow_nested, style=settings.style,
            seed=settings.seed, branch_names=_list(settings.branch_names), tags=_list(settings.tags),
            files=settings.files, remote=settings.remote, ahead=settings.ahead, behind=settings.behind,
            modified=settings.modified, staged=settings.staged, untracked=settings.untracked,
            stashes=settings.stashes, reflog=settings.reflog,
        )).to_dict()
        merged = spec.to_dict()
        for key, value in given.items():
            if value != cli_defaults.get(key, getattr(defaults, key)):
                merged[key] = value
        if recipe is None and scenario is None:
            merged.update(given)  # nothing to preserve: the command line is the whole spec
        merged["git_dir"] = str(pathlib.Path(os.path.expanduser(merged["git_dir"])).resolve())
        spec = Spec.from_dict(merged)

        if (spec.ahead or spec.behind) and not spec.remote:
            spec.remote = True
        if spec.style not in ("plain", "realistic"):
            raise BuildError("--style must be plain or realistic")

        if clean:
            for removed in clean_repo(str(spec.path())):
                typer.echo(f"git-dummy: removed {removed}")
            return

        if print_script:
            sys.stdout.write(make_script(spec))
            return

        if not json_out:
            typer.echo(f"git-dummy: Generating dummy Git repo at {spec.path()} with {Builder(spec)._describe()}.")
        result = Builder(spec).build()
        if json_out:
            sys.stdout.write(json.dumps(result, indent=1) + "\n")
    except (BuildError, ValueError, OSError) as e:
        typer.echo(f"git-dummy error: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
