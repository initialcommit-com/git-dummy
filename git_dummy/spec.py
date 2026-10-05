"""What to build: one plain object with every option, shared by the command
line, the Python API, recipe files and the named scenarios."""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Spec:
    # where
    name: str = "dummy"
    git_dir: str = "."
    no_subdir: bool = False
    allow_nested: bool = False

    # history
    commits: int = 5
    branches: int = 1
    diverge_at: int = 0
    merge: List[int] = field(default_factory=list)
    branch_names: List[str] = field(default_factory=list)
    style: str = "plain"  # plain (main.1, "Dummy commit #1 on main") or realistic
    constant_sha: bool = False
    seed: Optional[int] = None
    fast: Optional[bool] = None  # None: fast-import when the history is large

    # structure
    tags: List[str] = field(default_factory=list)
    octopus: bool = False
    criss_cross: bool = False
    orphan_branch: Optional[str] = None
    files: int = 0  # extra files per commit, for large trees

    # remote
    remote: bool = False
    ahead: int = 0
    behind: int = 0

    # working tree and reflog
    modified: int = 0
    staged: int = 0
    untracked: int = 0
    conflict: bool = False
    stashes: int = 0
    reflog: int = 0
    detached: bool = False
    checkout: Optional[str] = None
    worktree: Optional[str] = None
    submodule: bool = False

    def __post_init__(self):
        # a pathlib.Path (pytest's tmp_path, say) is as good as a string, and the
        # spec is written out as JSON (the repo's .git/git-dummy.json)
        if isinstance(self.git_dir, os.PathLike):
            self.git_dir = os.fspath(self.git_dir)

    # ---- helpers -------------------------------------------------------------------
    def path(self) -> pathlib.Path:
        base = pathlib.Path(os.path.expanduser(str(self.git_dir))).resolve()
        return base if self.no_subdir else base / self.name

    def merges(self) -> List[int]:
        return [int(x) for x in self.merge if str(x).strip()]

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Spec":
        known = {f.name for f in dataclasses.fields(cls)}
        unknown = sorted(set(data) - known)
        if unknown:
            raise ValueError(f"unknown option(s): {', '.join(unknown)}")
        clean = dict(data)
        for key in ("merge", "tags", "branch_names"):
            v = clean.get(key)
            if isinstance(v, str):
                clean[key] = [p.strip() for p in v.split(",") if p.strip()]
        if "merge" in clean:
            clean["merge"] = [int(x) for x in clean["merge"]]
        return cls(**clean)

    @classmethod
    def from_recipe(cls, path: str) -> "Spec":
        """A recipe is a JSON or YAML file holding the same keys as the options.
        YAML needs PyYAML installed; JSON always works."""
        text = pathlib.Path(path).read_text(encoding="utf-8")
        data = None
        if path.lower().endswith((".yaml", ".yml")):
            try:
                import yaml  # type: ignore
            except ImportError as e:
                raise ValueError("reading a YAML recipe needs PyYAML: pip install pyyaml") from e
            data = yaml.safe_load(text)
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                try:
                    import yaml  # type: ignore

                    data = yaml.safe_load(text)
                except ImportError as e:
                    raise ValueError("recipe is not JSON; install PyYAML to use YAML") from e
        if not isinstance(data, dict):
            raise ValueError("a recipe must be a mapping of option names to values")
        if "scenario" in data:
            from git_dummy.scenarios import apply_scenario

            base = apply_scenario(data.pop("scenario"), cls())
            merged = base.to_dict()
            merged.update(data)
            return cls.from_dict(merged)
        return cls.from_dict(data)
