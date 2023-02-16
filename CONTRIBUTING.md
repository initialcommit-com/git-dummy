# Contributing to Git-Dummy

Thanks for checking out Git-Dummy and for your interest in contributing!

## Reporting bugs

To report a bug you found, please open a [GitHub issue](https://github.com/initialcommit-com/git-dummy/issues/new)
and describe the error or problem in detail. Please check [existing issues](https://github.com/initialcommit-com/git-dummy/issues)
to make sure it hasn't already been reported.

When submitting a new issue, it helps to include:

1) The steps you took that lead to the issue
2) Any error message(s) that you received
3) A description of any unexpected behavior
4) The version of Git-Dummy you're running
5) The version of Python you're running and whether it's system-level or in a virtual environment
6) The operating system and version you're running

## Suggesting enhancements or new features

If you've got a cool idea for a feature that you'd like to see implemented in
Git-Dummy, we'd love to hear about it!

To suggest an enhancement or new feature, please open a [GitHub issue](https://github.com/initialcommit-com/git-dummy/issues/new)
and describe your proposed idea in detail. Please include why you think this
idea would be beneficial to the Git-Dummy user base.

## Your first code contribution

Note: Git-Dummy is a new project so these steps are not fully optimized yet, but
they should get you going.

To start contributing code to Git-Dummy, you'll need to perform the following
steps:

1) [Fork the Git-Dummy codebase](https://github.com/initialcommit-com/git-dummy/fork)
so that you have a copy on GitHub that you can clone and work with
2) Clone the codebase down to your local machine
3) If you previously installed Git-Dummy normally using pip, uninstall it first using:

```console
$ pip uninstall git-dummy
```

4) To run the code locally from source, install the development package by running:

```console
$ cd path/to/git-dummy
$ python -m pip install -e .
```

This will install sources from your cloned repo such that you can edit the source and the changes are reflected instantly.

If you already have the dependencies, you can ignore those using the `--no-deps` flag:

```console
$ python -m pip install --no-deps -e .
```

5) You can run Git-Dummy commands locally like this:

```console
$ git-dummy [global options] <subcommand> [subcommand options]
```

5) After pushing your code changes up to your fork, [submit a pull request](https://github.com/initialcommit-com/git-dummy/compare) for me
to review your code, provide feedback, and integrate it into the codebase!

## Code style guide

Since Git-Dummy is a new project, we don't have an official code style set in
stone. For now just try and make your new code fit in with the existing style
you find in the codebase, and we'll update this section later if that changes.

## Code Formatting

This project uses the [`black`](https://github.com/psf/black) code formatter to keep all code in a constistent format.

Please install it in your development environment and run `black path/to/changed/files` before committing any changes.

## Commit conventions

We have a few simple rules for Git-Dummy commit messages:

1) Write commit messages in the [imperative mood](https://initialcommit.com/blog/Git-Commit-Message-Imperative-Mood)
2) Add a signoff trailer to your commits by using the `-s` flag when you make
your commits, like this:

```
$ git commit -sm "Fixed xyz..."
```

## Questions

If you have any additional questions about contributing to Git-Dummy, feel free
to [send me an email at jacob@initialcommit.io](mailto:jacob@initialcommit.io).
