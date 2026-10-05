# git-dummy
[![GitHub license](https://img.shields.io/github/license/initialcommit-com/git-dummy)](https://github.com/initialcommit-com/git-dummy/blob/main/LICENSE)
[![GitHub tag](https://img.shields.io/github/v/release/initialcommit-com/git-dummy)](https://img.shields.io/github/v/release/initialcommit-com/git-dummy)
[![Downloads](https://static.pepy.tech/badge/git-dummy)](https://pepy.tech/project/git-dummy)
[![Contributors](https://img.shields.io/github/contributors/initialcommit-com/git-dummy)](https://github.com/initialcommit-com/git-dummy/graphs/contributors)
[![Share](https://img.shields.io/twitter/url?label=Share&url=https%3A%2F%2Ftwitter.com%2Finitcommit)](https://twitter.com/intent/tweet?text=Check%20out%20git%2Ddummy%20%2D%20a%20tool%20to%20generate%20dummy%20Git%20repos%20populated%20with%20the%20desired%20number%20of%20commits,%20branches,%20and%20structure,%20by%20%40initcommit!%20https%3A%2F%2Fgithub%2Ecom%2Finitialcommit%2Dcom%2Fgit%2Ddummy)

Generate Git repositories with the history, remote and working-tree state you ask for: commits, branches, merges, tags, a stopped merge conflict, stashes, a remote that is ahead or behind, a detached HEAD, worktrees, submodules, and named scenarios for the situations tutorials and test suites keep needing.

Example: `$ git-dummy --commits=10 --branches=4 --merge=1`

This initializes a new Git repo in the current directory with 4 branches, each containing 10 commits, 1 of which is merged back into `main`.

```console
$ git-dummy --scenario diverged-remote      # local and remote both moved on: push is rejected, pull merges
$ git-dummy --scenario merge-conflict       # a merge stopped on a conflict, markers in the file
$ git-dummy --style realistic --commits 8 --branches 3 --remote --behind 2 --staged 1 --untracked 1
```

Note: All generated dummy repos have at minimum 1 branch called `main`. Branches are named `branch1, branch2, ..., branchN` (or given with `--branch-names`, or realistic names with `--style realistic`). Each branch diverges from `main` at `--diverge-at` if supplied, or else a randomly chosen commit. The length of each branch is capped at `--commits`. Use `--merge=x,y,...,n` to select which branches get merged back into `main`.

## Use cases
- Programmatically generate Git repos for functional testing of Git tools, with the exact shape a test needs: `git_dummy.build(...)` returns the paths, ids and states it made
- Reproduce the situations people actually get into: a conflicted merge, a diverged remote, a detached HEAD, a dirty working tree, with one `--scenario`
- Decide how many commits and branches are generated, and which branches get merged back into `main`
- Mimic scenarios in real Git repos to practice on without touching real data
- Generate Git demo repos to teach or learn from, with real-looking files, messages and authors
- Generate large histories fast (`git fast-import`) to test tools at scale
- Write the equivalent plain `git` commands out as a shell script (`--print-script`) for machines without Python, or for a tutorial's appendix

## Features
- One-liner in the terminal, a Python API, a recipe file (`--from repo.json` or `.yaml`), and named scenarios (`--list-scenarios`)
- Customize the repo name, path, number of commits, branches, merges, and structure
- `--style realistic`: a small web service with README, source and test files, commit messages that read like a real log, and a few authors; `--seed` makes every choice reproducible
- A remote beside the repo (`--remote`), with local commits not yet pushed (`--ahead`) and commits on the remote not yet fetched (`--behind`)
- Working-tree states: `--modified`, `--staged`, `--untracked`, `--stashes`, `--conflict`; `--detached`, `--checkout`, `--reflog`
- Structure: `--tags`, `--octopus`, `--criss-cross`, `--orphan-branch`, `--worktree`, `--submodule`, `--files` for wide trees
- `--json` describes what was built; `--print-script` prints the commands instead of running them; `--clean` removes a repo git-dummy made and nothing else
- Large histories go through `git fast-import` (automatically above a few hundred commits, or with `--fast`)

## Quickstart

1) Install `git-dummy`:

```console
$ pip install git-dummy
```

2) Browse to the directory you want to create your dummy Git repo in:

```console
$ cd path/to/dummy/parent
```

3) Run the program:

```console
$ git-dummy [options]
```

4) A new Git repo called `dummy` will be initialized and populated based on the supplied parameters.

5) See global help for list of global options/flags and subcommands:

```console
$ git-dummy -h
```

## Requirements
* Python 3.8 or greater
* Pip (Package manager for Python)
* Git 2.28 or greater on PATH (git-dummy runs your own `git`; nothing else is needed)

## Scenarios
`git-dummy --scenario <name>` starts from one of these; any other option overrides the scenario's choice. `git-dummy --list-scenarios` prints the list.

| Scenario | What you get |
|---|---|
| `clean` | A tidy linear history on `main`. |
| `history` | Twelve commits on `main`, three merged topic branches with their own commits, two tags: for log and graph demos. |
| `rebase-ready` | A feature branch diverged from `main` with commits on both, checked out on the feature. |
| `merge-conflict` | A merge stopped on a conflict, markers in the file. |
| `messy-worktree` | Staged, modified and untracked files plus a stash. |
| `ahead-of-remote` | Two local commits not pushed yet. |
| `behind-remote` | Two commits on the remote not fetched yet. |
| `diverged-remote` | Both sides moved on: push rejected, pull merges, force-push overwrites. |
| `detached-head` | HEAD detached at an older commit. |
| `release` | Tagged releases on `main` and a hotfix branch off the last one. |
| `orphan` | A `gh-pages` branch with its own root. |
| `criss-cross` | Two branches that each merged the other. |
| `octopus` | Three topic branches merged into `main` in one commit. |
| `submodule` | A submodule pinned to a small library repo built beside the repo. |
| `worktree` | A linked worktree beside the repo, checked out on a branch. |
| `reflog` | A few HEAD moves so the reflog has entries. |
| `large` | Two thousand commits on five branches, through `fast-import`. |
| `orders` | The sample app [git-sim's README](https://github.com/initialcommit-com/git-sim) draws: two topic branches, a tag, a remote, something in every working-tree zone, a stash and a reflog. Build it, then run the README's git-sim commands inside it. |
| `orders-behind` | The same app with a remote two commits ahead, for `fetch` and `pull`. |

## Python API

```python
from git_dummy import build, Spec

r = build(commits=6, branches=2, style="realistic", seed=7, remote=True, behind=2, git_dir="/tmp")
r["path"]                  # where it is
r["branches"]["main"]      # tip ids
r["remote"]["path"]        # the bare remote beside it
r["worktree"]["staged"]    # what is staged, modified, untracked, in conflict
r["commits"]               # every commit: sha, parents, author, message

build(scenario="merge-conflict", git_dir="/tmp", name="cx")
build(Spec.from_recipe("repo.yaml"))
```

`git_dummy.script(spec)` returns the shell script; `git_dummy.clean(path)` removes a repo git-dummy made.

## Command options and flags
Available options and flags include:

`--name`: The name of the dummy Git repo, defaults to "dummy".  
`--commits`: The number of commits to populate in the dummy Git repo, defaults to 5.  
`--branches`: The number of branches to generate in the dummy Git repo, defaults to 1.  
`--diverge-at`: The commit number at which branches diverge from `main`.  
`--merge`: A comma separated list of branch postfix ids to merge back into `main`.  
`--git-dir`: The path at which to store the dummy Git repo, defaults to current directory.  
`--no-subdir`: Initialize the dummy Git repo in the current directory instead of in a subdirectory.  
`--constant-sha`: Use constant values for commit author, email, and commit date parameters to yield consistent sha1 values across git-dummy runs.  
`--allow-nested`: Allow dummy repo creation within an existing Git repo, as long as it's not at the level of an existing .git/ folder.  
`--style`: `plain` (the classic `main.1` files and "Dummy commit #1" messages, the default) or `realistic`.  
`--seed`: Seed every random choice and fix the commit dates, so the same seed gives the same repository.  
`--branch-names`: Comma separated names for the branches other than `main`.  
`--tags`: Comma separated tags to place along `main`, the last on its tip.  
`--files`: Extra files added by every commit on `main`, for large trees.  
`--octopus`: Merge the unmerged branches into `main` in one octopus merge.  
`--criss-cross`: Make `main` and the first branch each merge the other.  
`--orphan-branch`: Add a branch with its own root and a single page.  
`--fast` / `--no-fast`: Write the history with `git fast-import` (default: only when it is large).  
`--remote`: Create a bare remote beside the repo (`<name>.git`), add it as `origin` by the relative path `../<name>.git`, push everything to it and track it. Git writes the remote's URL into messages like "Merge branch 'main' of ../<name>", so no path from your machine ends up in the history.  
`--ahead`: Commits on local `main` the remote does not have.  
`--behind`: Commits the remote gained since the last fetch.  
`--modified`, `--staged`, `--untracked`: Tracked files with uncommitted edits, edits staged for the next commit, and new files.  
`--conflict`: Leave a merge stopped on a conflict.  
`--stashes`: Entries on the stash.  
`--reflog`: Extra HEAD moves so the reflog has entries.  
`--detached`: Leave HEAD detached at the commit before the tip.  
`--checkout`: The branch to leave checked out.  
`--worktree`: Add a linked worktree beside the repo, checked out on this branch.  
`--submodule`: Add a submodule pinned to a small library repo built beside this one.  
`--scenario`, `--list-scenarios`: Start from a named scenario; list them.  
`--from`: Read the options from a JSON or YAML recipe file (YAML needs `pip install git-dummy[yaml]`).  
`--json`: Print what was built as JSON.  
`--print-script`: Print the plain `git` commands that would build the repo, and build nothing.  
`--clean`: Remove the dummy repo at the target path and what git-dummy made beside it.

## Command examples
Generate a dummy Git repo called "cheese" on your Desktop, with 2 branches and 10 commits on each branch:

```console
$ git-dummy --name=cheese --branches=2 --commits=10 --git-dir=~/Desktop
```

Generate a dummy repo with 4 branches `main`, `branch1`, `branch2`, and `branch3`. Branches diverge from `main` after the 2nd commit:

```console
$ git-dummy --branches=4 --diverge-at=2
```

Generate a dummy repo with 4 branches, so that `branch1` and `branch3` are merged back into `main`:

```console
$ git-dummy --branches=4 --merge=1,3
```

A realistic repository with a remote that has moved on, reproducible from its seed:

```console
$ git-dummy --style realistic --seed 42 --commits 8 --branches 2 --remote --behind 2 --ahead 1
```

A recipe file, then the same thing as a shell script for a machine without Python:

```console
$ cat repo.json
{"scenario": "rebase-ready", "name": "practice", "commits": 8}
$ git-dummy --from repo.json
$ git-dummy --from repo.json --print-script > build-practice.sh
```

Every option can also be set as an environment variable prefixed `git_dummy_`:

```console
$ export git_dummy_git_dir=~/Desktop
$ export git_dummy_style=realistic
```

Explicitly specifying options at the command-line takes precedence over the corresponding environment variable values.

## What gets created where
The repository goes in `<git-dir>/<name>` (or the current directory with `--no-subdir`). Everything else git-dummy makes sits beside it and is listed in the repo's `.git/git-dummy.json`, which is what `--clean` reads:

- `<name>.git`: the bare remote (`--remote`)
- `<name>-<branch>`: a linked worktree (`--worktree`)
- `<name>.lib`: the library a submodule points at (`--submodule`)

## Learn More
Learn more about this tool on the [git-dummy project page](https://initialcommit.com/tools/git-dummy). git-dummy is what [git-sim](https://github.com/initialcommit-com/git-sim) ([project page](https://initialcommit.com/tools/git-sim)) uses for its demos, its tests and the graphs in its README, and the sample repositories behind the [visual Git command reference](https://initialcommit.com/learn/git/visual-command-reference) come from the same idea.

## Authors
**Jacob Stopak** - on behalf of [Initial Commit](https://initialcommit.com)
