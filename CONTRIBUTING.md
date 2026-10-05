# Contributing to git-dummy

Thanks for checking out git-dummy and for your interest in contributing!

## Ways to help

- ⭐ [Star the repo](https://github.com/initialcommit-com/git-dummy)
- [Open an issue](https://github.com/initialcommit-com/git-dummy/issues/new): a bug, a repository shape you need, or even a small friction or a confusing message
- Tell people about git-dummy, especially anyone writing Git tutorials or testing Git tools
- Contribute code, as described below

## Reporting bugs

Please check [existing issues](https://github.com/initialcommit-com/git-dummy/issues) first, then [open a new one](https://github.com/initialcommit-com/git-dummy/issues/new) with:

1) The command you ran (or your recipe file), and what you expected to get
2) What you got instead, with any error message
3) Your git-dummy version (`pip show git-dummy`), Git version (`git --version`), Python version, and operating system

`git-dummy ... --print-script` prints the exact `git` commands a build runs, which often shows where it went wrong.

## Suggesting a scenario or feature

[Open an issue](https://github.com/initialcommit-com/git-dummy/issues/new) describing the repository you need and what you'd use it for: a tutorial, a test, a demo. If it's a situation people get into in real repositories, it might make a good named scenario.

## Setting up for development

You need Python 3.8 or later, and Git 2.28 or later.

1) [Fork the repository](https://github.com/initialcommit-com/git-dummy/fork) and clone your fork
2) Create a virtual environment and install git-dummy from source, with YAML support and pytest:

```console
$ cd path/to/git-dummy
$ python -m venv .venv
$ source .venv/bin/activate          # Windows: .venv\Scripts\activate
$ python -m pip install -e ".[yaml]" pytest
```

The editable install (`-e`) means your changes take effect as soon as you save. If you had installed git-dummy with pip before, `pip uninstall git-dummy` first.

3) Build a repo with your local copy:

```console
$ git-dummy --scenario merge-conflict --git-dir /tmp
```

## Where things are

- `git_dummy/spec.py`: every option, in one `Spec` shared by the command line, the Python API, recipe files, and scenarios
- `git_dummy/builder.py`: builds the repository a `Spec` describes, or records it as a shell script for `--print-script`
- `git_dummy/scenarios.py`: the named scenarios
- `git_dummy/content.py`: the realistic files, commit messages, and authors
- `git_dummy/__main__.py`: the command line

## Running the tests

```console
$ pytest tests
```

Two things the tests protect, which a change must keep:

- **The classic ids don't change.** A plain build with `--constant-sha` must produce the same commit ids as git-dummy 0.1.2, byte for byte. [git-sim](https://github.com/initialcommit-com/git-sim)'s test fixtures depend on them.
- **The same seed builds the same repository.** Seeded builds are reproducible, so documentation and tests can show their commit ids.

If you work on git-sim too, run its validation suite (`pytest tests/validation` in git-sim) with git-dummy checked out beside it. It builds every repository shape it tests from your local git-dummy.

## Adding a scenario

1) Add an entry to `SCENARIOS` in `git_dummy/scenarios.py`, with a `_doc` line that says what situation it sets up
2) Add a row to the Scenarios table in the README
3) Add a test that builds it and checks the state it promises

## Code style

Match the code around your change: its naming, its comment density, and its idioms. The codebase isn't formatted with a single tool, so don't run a formatter over whole files, which would bury your change in unrelated edits.

## Commits and pull requests

1) Write commit messages in the [imperative mood](https://initialcommit.com/blog/Git-Commit-Message-Imperative-Mood): "Add", "Fix", "Build", not "Added" or "Fixes"
2) Sign off your commits with `-s`, which adds a `Signed-off-by` trailer:

```console
$ git commit -s -m "Add a scenario for a rebase stopped on a conflict"
```

3) Push to your fork and [open a pull request](https://github.com/initialcommit-com/git-dummy/compare) against `main`, saying what changed and how you tested it.

## Questions

Feel free to [email me at jacob@initialcommit.io](mailto:jacob@initialcommit.io) with any questions about contributing.
