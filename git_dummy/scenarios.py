"""Named repository shapes: the dozen situations a Git tutorial, a test suite
or a git-sim demo keeps needing. Each is a set of options on top of a Spec;
`git-dummy --scenario <name>` and `Spec.from_recipe` apply them, and any
option given alongside overrides the scenario's choice."""

from __future__ import annotations

from typing import Dict

from git_dummy.spec import Spec

SCENARIOS: Dict[str, Dict] = {
    "clean": {
        "_doc": "A tidy linear history on main and nothing else.",
        "style": "realistic",
        "commits": 6,
    },
    "history": {
        "_doc": "A longer history with three merged topic branches, for log and graph demos.",
        "style": "realistic",
        "commits": 12,
        "branches": 4,
        "diverge_at": 6,
        "merge": [1, 2, 3],
        "tags": ["v1.0.0", "v1.1.0"],
    },
    "rebase-ready": {
        "_doc": "A feature branch that diverged from main, with new commits on both, checked out on the feature.",
        "style": "realistic",
        "commits": 6,
        "branches": 2,
        "diverge_at": 4,
        "branch_names": ["feature/pagination"],
        "checkout": "feature/pagination",
    },
    "merge-conflict": {
        "_doc": "A merge stopped on a conflict, with markers in the file, ready for `git status` and a resolution.",
        "style": "realistic",
        "commits": 4,
        "conflict": True,
    },
    "messy-worktree": {
        "_doc": "Staged, modified and untracked files plus a stash: every zone of the working tree has something in it.",
        "style": "realistic",
        "commits": 5,
        "staged": 1,
        "modified": 2,
        "untracked": 2,
        "stashes": 1,
    },
    "ahead-of-remote": {
        "_doc": "A remote, with two local commits not pushed yet: a push has something to send.",
        "style": "realistic",
        "commits": 5,
        "remote": True,
        "ahead": 2,
    },
    "behind-remote": {
        "_doc": "A remote that gained two commits since the last fetch: fetch and pull have something to bring in.",
        "style": "realistic",
        "commits": 5,
        "remote": True,
        "behind": 2,
    },
    "diverged-remote": {
        "_doc": "Local and remote both moved on: a push is rejected, a pull merges or rebases, force-push overwrites.",
        "style": "realistic",
        "commits": 5,
        "remote": True,
        "ahead": 1,
        "behind": 2,
    },
    "detached-head": {
        "_doc": "HEAD detached at an older commit, the state people fall into and do not recognise.",
        "style": "realistic",
        "commits": 5,
        "detached": True,
    },
    "release": {
        "_doc": "Tagged releases on main and a hotfix branch off the last one.",
        "style": "realistic",
        "commits": 8,
        "branches": 2,
        "diverge_at": 7,
        "branch_names": ["hotfix/1.1.1"],
        "tags": ["v1.0.0", "v1.1.0"],
    },
    "orphan": {
        "_doc": "A docs branch with its own root, the shape of a gh-pages site.",
        "style": "realistic",
        "commits": 5,
        "orphan_branch": "gh-pages",
    },
    "criss-cross": {
        "_doc": "Two branches that each merged the other: the case that makes merge bases interesting.",
        "style": "realistic",
        "commits": 5,
        "branches": 2,
        "diverge_at": 3,
        "criss_cross": True,
    },
    "octopus": {
        "_doc": "Three topic branches merged into main in one commit.",
        "style": "realistic",
        "commits": 5,
        "branches": 4,
        "diverge_at": 3,
        "octopus": True,
    },
    "submodule": {
        "_doc": "A repository with a submodule, pinned to a commit of a small library beside it.",
        "style": "realistic",
        "commits": 4,
        "submodule": True,
    },
    "worktree": {
        "_doc": "A second working tree checked out on a branch, beside the repository.",
        "style": "realistic",
        "commits": 5,
        "branches": 2,
        "diverge_at": 3,
        "branch_names": ["feature/pagination"],
        "worktree": "feature/pagination",
    },
    "reflog": {
        "_doc": "A history with a few HEAD moves, so the reflog has entries to show.",
        "style": "realistic",
        "commits": 6,
        "reflog": 3,
    },
    "large": {
        "_doc": "Two thousand commits on five branches, built with fast-import, for performance testing.",
        "commits": 400,
        "branches": 5,
        "diverge_at": 200,
        "fast": True,
    },
    "orders": {
        "_doc": "The sample app git-sim's README draws: two topic branches, a tag, a remote one commit behind local main, something in every working-tree zone, a stash and the reflog.",
        "name": "orders",
        "style": "realistic",
        "seed": 42,
        "commits": 6,
        "branches": 3,
        "diverge_at": 4,
        "branch_names": ["feature/pagination", "fix/order-totals"],
        "tags": ["v1.0.0"],
        "remote": True,
        "ahead": 1,
        "modified": 1,
        "staged": 1,
        "untracked": 1,
        "stashes": 1,
        "reflog": 2,
    },
    "orders-behind": {
        "_doc": "The same sample app with a remote that gained two commits since the last fetch: git-sim's README draws fetch and pull on it.",
        "name": "orders-behind",
        "style": "realistic",
        "seed": 42,
        "commits": 6,
        "remote": True,
        "behind": 2,
    },
}


def names():
    return list(SCENARIOS)


def describe(name: str) -> str:
    return SCENARIOS[name].get("_doc", "")


def apply_scenario(name: str, spec: Spec) -> Spec:
    if name not in SCENARIOS:
        raise ValueError(f"unknown scenario '{name}'; one of: {', '.join(names())}")
    merged = spec.to_dict()
    for key, value in SCENARIOS[name].items():
        if key.startswith("_"):
            continue
        merged[key] = value
    return Spec.from_dict(merged)
