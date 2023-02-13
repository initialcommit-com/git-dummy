# git-dummy
[![GitHub license](https://img.shields.io/github/license/initialcommit-com/git-dummy)](https://github.com/initialcommit-com/git-dummy/blob/main/LICENSE)
[![GitHub tag](https://img.shields.io/github/v/release/initialcommit-com/git-dummy)](https://img.shields.io/github/v/release/initialcommit-com/git-dummy)
[![Downloads](https://static.pepy.tech/badge/git-dummy)](https://pepy.tech/project/git-dummy)
[![Contributors](https://img.shields.io/github/contributors/initialcommit-com/git-dummy)](https://github.com/initialcommit-com/git-dummy/graphs/contributors)
[![Share](https://img.shields.io/twitter/url?label=Share&url=https%3A%2F%2Ftwitter.com%2Finitcommit)](https://twitter.com/intent/tweet?text=Check%20out%20git%2Ddummy%20%2D%20a%20tool%20to%20generate%20dummy%20Git%20repos%20populated%20with%20the%20desired%20number%20of%20commits,%20branches,%20and%20structure,%20by%20%40initcommit!%20https%3A%2F%2Fgithub%2Ecom%2Finitialcommit%2Dcom%2Fgit%2Ddummy)

Generate dummy Git repositories and populate them with the desired number of commits, branches, and structure.

Example: `$ git-dummy --commits=5`

This will initialize a new Git repo in the current directory with 5 commits on a single branch.

## Use cases
- Programatically generate Git repos for functional testing of Git tools
- Mimic scenarios in real Git repos to practice on without touching real data
- Generate Git demo repos to teach or learn from

## Features
- Run a one-liner git-dummy command in the terminal to generate a dummy Git repo based on your parameters
- Customize the repo name, path, number of commits, branches, and structure

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
* Python 3.7 or greater
* Pip (Package manager for Python)

## Command options and flags
Available options and flags include:

`--name`: The name of the dummy Git repo, defaults to "dummy".  
`--commits`: The number of commits to populate in the dummy Git repo, defaults to 5.  
`--git-dir`: The path at which to store the dummy Git repo, defaults to current directory.

## Basic command examples
Generate a dummy Git repo called "cheese" with 10 commits on your Desktop:

```console
$ git-dummy --name=cheese --commits=10 --git-dir=~/Desktop
```

For convenience, environment variables can be set for any command-line option available in git-dummy. All environment variables start with `git_dummy_` followed by the name of the option.

For example, the `--git-dir` option can be set as an environment variable like:

```console
$ export git_dummy_git_dir=~/Desktop
```

Similarly, the `--name` option can be set like:

```console
$ export git_dummy_name=cheese
```

In general:

```console
$ export git_dummy_option_name=option_value
```

Explicitly specifying options at the command-line takes precedence over the corresponding environment variable values.

## Learn More
Learn more about this tool on the [git-dummy project page](https://initialcommit.com/tools/git-dummy).

## Authors
**Jacob Stopak** - on behalf of [Initial Commit](https://initialcommit.com)
