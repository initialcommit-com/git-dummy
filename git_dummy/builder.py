"""Build a repository from a Spec.

Two ways to make the history: plain `git` commands, which can also be
written out as a shell script instead of run; and `git fast-import`, used for
large histories, which writes thousands of commits in one process. Everything
after the history (remote, working-tree states, stashes, worktrees,
submodule) runs as plain commands in both cases.

Nothing here uses GitPython: the user's own `git` does the work, so the
repository is exactly what that Git version would make.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import random
import shlex
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

from git_dummy.content import Content, INITIAL_MESSAGE
from git_dummy.spec import Spec

MARKER = "git-dummy.json"
# What --constant-sha has always meant: this instant, which the old GitPython
# path read as UTC (git itself would read a bare stamp in local time).
CLASSIC_DATE = "2023-01-01T00:00:00+00:00"
CLASSIC_AUTHOR = ("Git Dummy", "dumdum@git.dummy")
REALISTIC_BASE = datetime.datetime(2024, 3, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
FAST_THRESHOLD = 300  # commits; above this the history goes through fast-import


class BuildError(Exception):
    pass


# ---- running (or recording) commands ---------------------------------------------------


class Shell:
    """Runs commands in a directory, or records them as a POSIX shell script."""

    def __init__(self, cwd: pathlib.Path, dry: bool = False):
        self.cwd = pathlib.Path(cwd)
        self.dry = dry
        self.lines: List[str] = []
        self.env: Dict[str, str] = {}

    # -- recording helpers
    def _q(self, s) -> str:
        return shlex.quote(str(s))

    def comment(self, text: str):
        if self.dry:
            self.lines.append(f"# {text}")

    def cd(self, path: pathlib.Path):
        if self.dry:
            self.lines.append(f"cd {self._q(self._rel(path))}")
        self.cwd = pathlib.Path(path)

    def _rel(self, path) -> str:
        try:
            return os.path.relpath(path, self.cwd).replace("\\", "/")
        except ValueError:
            return str(path)

    # -- git
    def git(self, *args, input: Optional[str] = None, env: Optional[Dict[str, str]] = None, check=True, quiet=False) -> str:
        args = [str(a) for a in args]
        if self.dry:
            prefix = "".join(f"{k}={self._q(v)} " for k, v in (env or {}).items())
            line = prefix + "git " + " ".join(self._q(a) for a in args)
            if input is not None:
                line += " <<'GIT_DUMMY_EOF'\n" + input.rstrip("\n") + "\nGIT_DUMMY_EOF"
            self.lines.append(line)
            return ""
        full_env = dict(os.environ)
        full_env.update(self.env)
        if env:
            full_env.update(env)
        try:
            # Bytes in and out: a text pipe would turn the newlines of a
            # fast-import stream into CRLF on Windows and break its byte counts.
            proc = subprocess.run(
                ["git", *args],
                cwd=str(self.cwd),
                input=input.encode("utf-8") if input is not None else None,
                capture_output=True,
                env=full_env,
            )
        except FileNotFoundError as e:
            raise BuildError("git is not installed or not on PATH") from e
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        if check and proc.returncode != 0:
            raise BuildError(f"git {' '.join(args)} failed: {stderr.strip() or stdout.strip()}")
        return stdout

    # -- files
    def write(self, rel: str, text: str):
        if self.dry:
            self.lines.append(f"mkdir -p {self._q(os.path.dirname(rel) or '.')}" if "/" in rel else "")
            self.lines.append(f"cat > {self._q(rel)} <<'GIT_DUMMY_EOF'\n{text.rstrip(chr(10))}\nGIT_DUMMY_EOF" if text else f": > {self._q(rel)}")
            self.lines = [l for l in self.lines if l != ""]
            return
        path = self.cwd / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def append(self, rel: str, text: str):
        if self.dry:
            self.lines.append(f"cat >> {self._q(rel)} <<'GIT_DUMMY_EOF'\n{text.rstrip(chr(10))}\nGIT_DUMMY_EOF")
            return
        with open(self.cwd / rel, "a", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def mkdir(self, path: pathlib.Path):
        if self.dry:
            self.lines.append(f"mkdir -p {self._q(self._rel(path))}")
            return
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    def rmtree(self, path: pathlib.Path):
        if self.dry:
            self.lines.append(f"rm -rf {self._q(self._rel(path))}")
            return
        _rmtree(path)


def _rmtree(path):
    def onerror(func, p, exc):
        try:
            os.chmod(p, 0o777)
            func(p)
        except Exception:
            pass

    if os.path.isdir(path):
        shutil.rmtree(path, onerror=onerror)


# ---- the plan: what commits exist before any command runs -----------------------------


class CommitPlan:
    def __init__(self, message: str, files: List[Tuple[str, str, bool]], author: Tuple[str, str]):
        self.message = message
        self.files = files  # (path, text, append)
        self.author = author


class BranchPlan:
    def __init__(self, name: str, index: int, back: int, commits: List[CommitPlan]):
        self.name = name
        self.index = index  # the N in branchN, which --merge refers to
        self.back = back  # the branch starts at main~<back> as main stands when it is made
        self.commits = commits


class Builder:
    def __init__(self, spec: Spec, dry: bool = False):
        self.spec = spec
        self.dry = dry
        self.path = spec.path()
        self.parent = self.path.parent
        self.sh = Shell(self.parent, dry=dry)
        seed = spec.seed if spec.seed is not None else (0 if spec.constant_sha else random.randrange(1 << 30))
        self.rng = random.Random(seed)
        self.seed = seed
        self.content = Content(seed)
        self.realistic = spec.style == "realistic"
        self.constant = spec.constant_sha or spec.seed is not None
        self.counter = 0  # commits made so far, for dates
        self.tracked: List[str] = []  # files on main, in creation order
        self.created: List[str] = []  # paths made outside the repository
        self.branch_names: List[str] = []
        self.result: Dict = {}

    # -- dates and identities ----------------------------------------------------------
    def _date_env(self) -> Dict[str, str]:
        if not self.constant:
            return {}
        if self.realistic or self.spec.seed is not None and not self.spec.constant_sha:
            when = REALISTIC_BASE + datetime.timedelta(hours=self.counter)
            stamp = when.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        else:
            stamp = CLASSIC_DATE
        return {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}

    def _author_env(self, author: Optional[Tuple[str, str]]) -> Dict[str, str]:
        if not author:
            return {}
        return {
            "GIT_AUTHOR_NAME": author[0],
            "GIT_AUTHOR_EMAIL": author[1],
            "GIT_COMMITTER_NAME": author[0],
            "GIT_COMMITTER_EMAIL": author[1],
        }

    def commit(self, message: str, author: Optional[Tuple[str, str]] = None, extra: Tuple[str, ...] = ()):
        # The message goes in verbatim, without the newline `-m` would add:
        # that is how git-dummy's commits have always been stored, and it is
        # what keeps --constant-sha ids the same as before.
        env = {**self._date_env(), **self._author_env(author)}
        if self.dry:
            prefix = "".join(f"{k}={shlex.quote(v)} " for k, v in env.items())
            args = " ".join(shlex.quote(a) for a in extra)
            self.sh.lines.append(f"printf '%s' {shlex.quote(message)} | {prefix}git commit -q --cleanup=verbatim {args}{' ' if args else ''}-F -")
        else:
            self.sh.git("commit", "-q", "--cleanup=verbatim", *extra, "-F", "-", input=message, env=env)
        self.counter += 1

    # -- the plan ---------------------------------------------------------------------
    def plan(self) -> Tuple[List[CommitPlan], List[BranchPlan]]:
        s = self.spec
        main: List[CommitPlan] = []
        if self.realistic:
            files = [(p, t, False) for p, t in Content.initial_files()]
            main.append(CommitPlan(INITIAL_MESSAGE, files + self._extra_files(1), self.content.author()))
            for c in range(2, s.commits + 1):
                msg, changes = self.content.change()
                main.append(CommitPlan(msg, [(p, t, True) for p, t in changes] + self._extra_files(c), self.content.author()))
        else:
            for c in range(1, s.commits + 1):
                main.append(CommitPlan(f"Dummy commit #{c} on main", [(f"main.{c}", "", False)] + self._extra_files(c), None))

        branches: List[BranchPlan] = []
        # git-dummy has always made the branches from the highest number down,
        # merging each into main as it goes, so a merged branch is never part of
        # a later branch's history. The same order is kept here.
        for i in range(s.branches - 1, 0, -1):
            name = s.branch_names[i - 1] if i - 1 < len(s.branch_names) else (
                self.content.branch_name(i) if self.realistic else f"branch{i}"
            )
            r = (s.commits - s.diverge_at) if s.diverge_at else (self.rng.choice(range(1, s.commits)) if s.commits > 1 else 0)
            r = max(0, min(r, s.commits))
            commits = []
            for d in range(s.commits - r + 1, s.commits + 1):
                if self.realistic:
                    slug = name.split("/")[-1].replace("-", "_")
                    msg = f"{self._realistic_branch_message(name, d)}"
                    commits.append(CommitPlan(msg, [(f"src/{slug}.py", f"# {msg}\n", True)], self.content.author()))
                else:
                    commits.append(CommitPlan(f"Dummy commit #{d} on {name}", [(f"{name}.{d}", "", False)], None))
            branches.append(BranchPlan(name, i, r, commits))
        return main, branches

    def _realistic_branch_message(self, branch: str, n: int) -> str:
        topic = branch.split("/")[-1].replace("-", " ")
        verbs = ["Start", "Continue", "Wire up", "Test", "Polish", "Finish"]
        return f"{verbs[(n - 1) % len(verbs)]} {topic}"

    def _extra_files(self, c: int) -> List[Tuple[str, str, bool]]:
        return [(f"data/file-{c}-{k}.txt", f"record {c}-{k}\n", False) for k in range(1, self.spec.files + 1)]

    # -- building ------------------------------------------------------------------------
    def build(self) -> Dict:
        s = self.spec
        if not self.dry:
            self._check_target()
        self.sh.comment(f"git-dummy: {self._describe()}")
        self.sh.mkdir(self.path)
        self.sh.cd(self.path)
        self._init()
        main, branches = self.plan()
        total = len(main) + sum(len(b.commits) for b in branches)
        fast = s.fast if s.fast is not None else total >= FAST_THRESHOLD
        if fast and not self.dry:
            self._history_fast(main, branches)
        else:
            self._history_plain(main, branches)
        self.branch_names = ["main"] + [b.name for b in branches]
        self._structure(branches)
        if s.submodule:
            self._submodule()
        if s.remote:
            self._remote()
        if s.reflog:
            self._reflog_moves()
        if s.checkout:
            self.sh.git("checkout", "-q", s.checkout)
        if s.worktree:
            self._worktree()
        if s.conflict:
            self._conflict()
        if s.stashes:
            self._stashes()
        self._dirty()
        if s.detached:
            self.sh.git("checkout", "-q", "--detach", "HEAD~1" if s.commits > 1 else "HEAD")
        if not self.dry:
            self._write_marker()
            self.result = self._gather()
        return self.result

    def _describe(self) -> str:
        s = self.spec
        bits = [f"{s.branches} branch(es)", f"{s.commits} commit(s)"]
        if s.merges():
            bits.append(f"merging {','.join(map(str, s.merges()))}")
        if s.remote:
            bits.append("a remote" + (f" {s.ahead} ahead" if s.ahead else "") + (f" {s.behind} behind" if s.behind else ""))
        return ", ".join(bits)

    def _check_target(self):
        from git_dummy.util import is_git_dir, is_inside_git_dir

        if is_git_dir(self.path):
            raise BuildError(f"Git repository already exists at {self.path}")
        if not self.spec.allow_nested and is_inside_git_dir(self.path):
            raise BuildError(f"Git repository already exists at {self.path} or a parent: use --allow-nested to override")

    def _init(self):
        self.sh.git("init", "-q", "-b", "main", ".", check=False) if self.dry else self._init_real()
        self.sh.git("config", "init.defaultBranch", "main")
        if self.spec.constant_sha:
            self.sh.git("config", "user.name", CLASSIC_AUTHOR[0])
            self.sh.git("config", "user.email", CLASSIC_AUTHOR[1])
        elif not self.dry and not self._has_identity():
            self.sh.git("config", "user.name", CLASSIC_AUTHOR[0])
            self.sh.git("config", "user.email", CLASSIC_AUTHOR[1])

    def _init_real(self):
        proc = subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=str(self.path), capture_output=True, text=True)
        if proc.returncode != 0:  # git older than 2.28: no -b
            self.sh.git("init", "-q", ".")
            self.sh.git("symbolic-ref", "HEAD", "refs/heads/main")

    def _has_identity(self) -> bool:
        out = subprocess.run(["git", "config", "--get", "user.email"], cwd=str(self.path), capture_output=True, text=True)
        return out.returncode == 0 and bool(out.stdout.strip())

    # -- history, plain ------------------------------------------------------------------
    def _apply(self, cp: CommitPlan):
        for path, text, append in cp.files:
            if append and path in self.tracked:
                self.sh.append(path, text)
            else:
                self.sh.write(path, text)
                if path not in self.tracked:
                    self.tracked.append(path)
            self.sh.git("add", "--", path)
        self.commit(cp.message, cp.author)

    def _history_plain(self, main: List[CommitPlan], branches: List[BranchPlan]):
        for cp in main:
            self._apply(cp)
        merges = self.spec.merges()
        for bp in branches:
            self.sh.git("checkout", "-q", "main")
            self.sh.git("checkout", "-q", "-b", bp.name, f"main~{bp.back}" if bp.back else "main")
            for cp in bp.commits:
                self._apply(cp)
            if bp.index in merges:
                self._merge_into_main(bp.name)
        self.sh.git("checkout", "-q", "main")

    def _merge_into_main(self, branch: str):
        # The merge commit lists the branch as its first parent and main as the
        # second, as git-dummy has always done, so existing --constant-sha
        # histories keep their ids.
        msg = f"Merge branch '{branch}'" if self.realistic else f"Merge {branch} into main"
        self.sh.git("checkout", "-q", "--detach", branch)
        self.sh.git("merge", "-q", "--no-ff", "--no-commit", "main")
        self.commit(msg)
        self.sh.git("branch", "-f", "main", "HEAD")
        self.sh.git("checkout", "-q", "main")

    # -- history, fast-import -------------------------------------------------------------
    def _history_fast(self, main: List[CommitPlan], branches: List[BranchPlan]):
        marks: List[str] = []
        blobs: Dict[str, int] = {}
        stream: List[str] = []
        mark = [0]

        def next_mark():
            mark[0] += 1
            return mark[0]

        def blob(text: str) -> int:
            if text in blobs:
                return blobs[text]
            m = next_mark()
            data = text.encode("utf-8")
            stream.append(f"blob\nmark :{m}\ndata {len(data)}\n{text}\n")
            blobs[text] = m
            return m

        base_unix = int(REALISTIC_BASE.timestamp()) if (self.realistic or self.spec.seed is not None) else 1672531200
        name, email = CLASSIC_AUTHOR if (self.spec.constant_sha or self.realistic) else self._identity()
        counter = [0]

        def ident(author):
            if self.constant:
                when = base_unix + (3600 * counter[0] if self.realistic else 0)
            else:
                when = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
            n, e = author or (name, email)
            return f"{n} <{e}> {when} +0000"

        def commit(ref: str, cp: CommitPlan, parents: List[int], files_state: Dict[str, str]) -> int:
            m = next_mark()
            for path, text, append in cp.files:
                files_state[path] = (files_state.get(path, "") + text) if append else text
            who = ident(cp.author)
            data = cp.message.encode("utf-8")
            lines = [f"commit {ref}", f"mark :{m}", f"author {who}", f"committer {who}", f"data {len(data)}", cp.message]
            if parents:
                lines.append(f"from :{parents[0]}")
                for p in parents[1:]:
                    lines.append(f"merge :{p}")
            for path, text, append in cp.files:
                lines.append(f"M 100644 :{blob(files_state[path])} {path}")
            stream.append("\n".join(lines) + "\n\n")
            counter[0] += 1
            return m

        # main
        first_parent: Dict[int, Optional[int]] = {}
        states: Dict[int, Dict[str, str]] = {}  # the tree at each mark
        state: Dict[str, str] = {}
        parent: List[int] = []
        main_tip: Optional[int] = None
        for cp in main:
            m = commit("refs/heads/main", cp, parent, state)
            first_parent[m] = parent[0] if parent else None
            states[m] = dict(state)
            parent = [m]
            main_tip = m
            for path, _, _ in cp.files:
                if path not in self.tracked:
                    self.tracked.append(path)

        def back_from(mark: Optional[int], steps: int) -> Optional[int]:
            """main~<steps>: follow first parents, as git does."""
            for _ in range(steps):
                if mark is None:
                    break
                mark = first_parent.get(mark)
            return mark

        merges = self.spec.merges()
        for bp in branches:
            base = back_from(main_tip, bp.back)
            bstate = dict(states[base]) if base is not None else {}
            bparent = [base] if base is not None else []
            tip = base
            for cp in bp.commits:
                tip = commit(f"refs/heads/{bp.name}", cp, bparent, bstate)
                first_parent[tip] = bparent[0] if bparent else None
                states[tip] = dict(bstate)
                bparent = [tip]
            if not bp.commits and base is not None:
                stream.append(f"reset refs/heads/{bp.name}\nfrom :{base}\n\n")
            if bp.index in merges and tip is not None and main_tip is not None:
                merged = dict(states[main_tip])
                merged.update(bstate)
                msg = f"Merge branch '{bp.name}'" if self.realistic else f"Merge {bp.name} into main"
                # fast-import starts the merge's tree from its first parent (the
                # branch), so everything main added since the base must be listed.
                mp = CommitPlan(msg, [(p, t, False) for p, t in merged.items() if bstate.get(p) != t], None)
                merge_mark = commit("refs/heads/main", mp, [tip, main_tip], merged)
                first_parent[merge_mark] = tip  # the branch is the first parent, as it always was
                states[merge_mark] = dict(merged)
                main_tip = merge_mark
        stream.append("done\n")
        self.sh.git("fast-import", "--quiet", "--done", input="".join(stream))
        self.sh.git("checkout", "-q", "-f", "main")
        self.counter = counter[0]

    def _identity(self) -> Tuple[str, str]:
        name = self.sh.git("config", "--get", "user.name", check=False).strip() or CLASSIC_AUTHOR[0]
        email = self.sh.git("config", "--get", "user.email", check=False).strip() or CLASSIC_AUTHOR[1]
        return name, email

    # -- structure ----------------------------------------------------------------------
    def _structure(self, branches: List[BranchPlan]):
        s = self.spec
        if s.octopus and len(branches) >= 2:
            unmerged = [b.name for i, b in enumerate(branches, start=1) if i not in s.merges()]
            if len(unmerged) >= 2:
                self.sh.git("checkout", "-q", "main")
                names = ", ".join(f"'{b}'" for b in unmerged)
                self.sh.git("merge", "-q", "--no-ff", "--no-edit", "-m", f"Merge branches {names}", *unmerged, env=self._date_env())
                self.counter += 1
        if s.criss_cross and branches:
            other = branches[0].name
            self.sh.git("checkout", "-q", "main")
            self.sh.git("branch", "-f", "git-dummy-tmp-main", "main")
            self.sh.git("branch", "-f", "git-dummy-tmp-other", other)
            self.sh.git("merge", "-q", "--no-ff", "--no-edit", "-m", f"Merge {other} into main", "git-dummy-tmp-other", env=self._date_env())
            self.counter += 1
            self.sh.git("checkout", "-q", other)
            self.sh.git("merge", "-q", "--no-ff", "--no-edit", "-m", f"Merge main into {other}", "git-dummy-tmp-main", env=self._date_env())
            self.counter += 1
            self.sh.git("branch", "-D", "-q", "git-dummy-tmp-main", "git-dummy-tmp-other")
            self.sh.git("checkout", "-q", "main")
        if s.orphan_branch:
            self.sh.git("checkout", "-q", "--orphan", s.orphan_branch)
            self.sh.git("rm", "-r", "-f", "-q", "--cached", ".")
            self.sh.git("clean", "-fdq")
            self.sh.write("index.html", f"<h1>{s.name}</h1>\n<p>Published from the {s.orphan_branch} branch.</p>\n")
            self.sh.git("add", "index.html")
            self.commit(f"Start the {s.orphan_branch} site", self.content.author() if self.realistic else None)
            self.sh.git("checkout", "-q", "-f", "main")
        if s.tags:
            # Spread the tags over main's first-parent history, the last one on
            # the tip, once every merge that moves main has happened.
            n = len(s.tags)
            depth = int(self.sh.git("rev-list", "--count", "--first-parent", "main").strip() or s.commits) if not self.dry else s.commits
            for i, tag in enumerate(s.tags):
                back = max(0, round((n - 1 - i) * (depth - 1) / max(n, 1)))
                self.sh.git("tag", tag, f"main~{back}" if back else "main")

    # -- submodule ----------------------------------------------------------------------
    def _submodule(self):
        lib = self.parent / f"{self.spec.name}.lib"
        self.created.append(str(lib))
        self.sh.mkdir(lib)
        self.sh.cd(lib)
        self._init_at(lib)
        self.sh.write("lib.py", "def helper():\n    return 42\n")
        self.sh.git("add", "lib.py")
        self.commit("Add the helper library", self.content.author() if self.realistic else None)
        self.sh.append("lib.py", "\n\ndef version():\n    return '1.1'\n")
        self.sh.git("add", "lib.py")
        self.commit("Report the library version", self.content.author() if self.realistic else None)
        self.sh.cd(self.path)
        url = "../" + lib.name if self.dry else str(lib)
        self.sh.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", url, "lib")
        self.commit("Add lib as a submodule")

    def _init_at(self, where: pathlib.Path):
        if self.dry:
            self.sh.git("init", "-q", "-b", "main", ".")
        else:
            proc = subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=str(where), capture_output=True, text=True)
            if proc.returncode != 0:
                self.sh.git("init", "-q", ".")
                self.sh.git("symbolic-ref", "HEAD", "refs/heads/main")
        if self.spec.constant_sha or (not self.dry and not self._has_identity_at(where)):
            self.sh.git("config", "user.name", CLASSIC_AUTHOR[0])
            self.sh.git("config", "user.email", CLASSIC_AUTHOR[1])

    def _has_identity_at(self, where) -> bool:
        out = subprocess.run(["git", "config", "--get", "user.email"], cwd=str(where), capture_output=True, text=True)
        return out.returncode == 0 and bool(out.stdout.strip())

    # -- remote --------------------------------------------------------------------------
    def _remote(self):
        s = self.spec
        bare = self.parent / f"{s.name}.origin.git"
        self.created.append(str(bare))
        url = "../" + bare.name if self.dry else str(bare)
        self.sh.git("init", "-q", "--bare", "-b", "main", url, check=not self.dry)
        self.sh.git("remote", "add", "origin", url)
        self.sh.git("push", "-q", "--all", "origin")
        if s.tags:
            self.sh.git("push", "-q", "--tags", "origin")
        for b in self.branch_names:
            self.sh.git("branch", "-q", f"--set-upstream-to=origin/{b}", b)
        if s.behind:
            self._colleague_commits(url, s.behind)
        for k in range(1, s.ahead + 1):
            self.sh.git("checkout", "-q", "main")
            n = s.commits + k
            if self.realistic:
                msg, changes = self.content.change()
                cp = CommitPlan(msg, [(p, t, True) for p, t in changes], self.content.author())
            else:
                cp = CommitPlan(f"Dummy commit #{n} on main", [(f"main.{n}", "", False)], None)
            self._apply(cp)

    def _colleague_commits(self, url: str, count: int):
        """Commits that reach the remote after our last fetch: pushed from a
        second clone, so this repository does not know about them."""
        clone = self.parent / f".{self.spec.name}-colleague"
        if self.dry:
            self.sh.lines.append("colleague=$(mktemp -d)")
            self.sh.lines.append(f"git clone -q {shlex.quote(url)} \"$colleague\"")
            for k in range(1, count + 1):
                self.sh.lines.append(f"printf '%s\\n' 'Change {k} from a colleague' >> \"$colleague\"/docs/CHANGELOG.md 2>/dev/null || {{ mkdir -p \"$colleague\"/docs; printf '%s\\n' 'Change {k} from a colleague' > \"$colleague\"/docs/CHANGELOG.md; }}")
                self.sh.lines.append(f"git -C \"$colleague\" add docs/CHANGELOG.md && git -C \"$colleague\" -c user.name=Colleague -c user.email=colleague@example.com commit -q -m 'Update the changelog ({k})'")
            self.sh.lines.append("git -C \"$colleague\" push -q origin main")
            self.sh.lines.append('rm -rf "$colleague"')
            return
        _rmtree(clone)
        self.sh.git("clone", "-q", url, str(clone))
        env = {"GIT_AUTHOR_NAME": "Colleague", "GIT_AUTHOR_EMAIL": "colleague@example.com", "GIT_COMMITTER_NAME": "Colleague", "GIT_COMMITTER_EMAIL": "colleague@example.com"}
        sh = Shell(clone)
        for k in range(1, count + 1):
            (clone / "docs").mkdir(exist_ok=True)
            with open(clone / "docs" / "CHANGELOG.md", "a", encoding="utf-8", newline="\n") as f:
                f.write(f"- Change {k} from a colleague\n")
            sh.git("add", "docs/CHANGELOG.md")
            sh.git("commit", "-q", "-m", f"Update the changelog ({k})", env={**env, **self._date_env()})
            self.counter += 1
        sh.git("push", "-q", "origin", "main")
        _rmtree(clone)

    # -- reflog, worktree, dirty states --------------------------------------------------
    def _reflog_moves(self):
        for _ in range(self.spec.reflog):
            if self.spec.commits > 1:
                self.sh.git("checkout", "-q", "HEAD~1")
            self.sh.git("checkout", "-q", "main")

    def _worktree(self):
        branch = self.spec.worktree
        slug = branch.replace("/", "-")
        where = self.parent / f"{self.spec.name}-{slug}"
        self.created.append(str(where))
        target = "../" + where.name if self.dry else str(where)
        self.sh.git("worktree", "add", "-q", target, branch)

    def _victims(self, count: int, skip: List[str]) -> List[str]:
        """Tracked files to dirty, oldest first, never the same file twice."""
        pool = [f for f in self.tracked if f not in skip and not f.startswith("data/")]
        return pool[:count]

    def _conflict(self):
        target = self.tracked[0] if self.tracked else "main.1"
        branch = "feature/conflict" if self.realistic else "conflict"
        self.sh.git("checkout", "-q", "-b", branch)
        self.sh.write(target, self._first_line(target) + "theirs: the version committed on the branch\n")
        self.sh.git("add", "--", target)
        self.commit(f"Change {target} on {branch}", self.content.author() if self.realistic else None)
        self.sh.git("checkout", "-q", "main")
        self.sh.write(target, self._first_line(target) + "ours: the version committed on main\n")
        self.sh.git("add", "--", target)
        self.commit(f"Change {target} on main", self.content.author() if self.realistic else None)
        self.sh.git("merge", "-q", branch, check=False)
        self._conflict_file = target

    def _first_line(self, path: str) -> str:
        if self.dry or not (self.path / path).exists():
            return ""
        text = (self.path / path).read_text(encoding="utf-8")
        first = text.split("\n", 1)[0]
        return first + "\n" if first else ""

    def _stashes(self):
        victims = self._victims(1, [getattr(self, "_conflict_file", "")])
        target = victims[0] if victims else "main.1"
        for i in range(self.spec.stashes):
            self.sh.append(target, f"work in progress {i + 1}\n")
            note = self.content.stash_note(i) if self.realistic else f"WIP {i + 1}"
            # dated like the commits, so a stash's sha is the same on every build
            self.sh.git("stash", "push", "-q", "-m", note, "--", target, env=self._date_env())

    def _dirty(self):
        s = self.spec
        skip = [getattr(self, "_conflict_file", "")]
        modified = self._victims(s.modified, skip)
        staged = self._victims(s.modified + s.staged, skip)[s.modified:]
        for f in modified:
            self.sh.append(f, "an uncommitted edit\n")
        for f in staged:
            self.sh.append(f, "a staged edit\n")
            self.sh.git("add", "--", f)
        for i in range(1, s.untracked + 1):
            name = f"notes-{i}.txt" if i > 1 else "scratch.txt"
            self.sh.write(name, "not tracked yet\n")
        self._states = {"modified": modified, "staged": staged, "untracked": [f"notes-{i}.txt" if i > 1 else "scratch.txt" for i in range(1, s.untracked + 1)]}

    # -- afterwards --------------------------------------------------------------------------
    def _write_marker(self):
        marker = {"spec": self.spec.to_dict(), "created": self.created, "seed": self.seed}
        git_dir = self.sh.git("rev-parse", "--git-dir").strip()
        path = pathlib.Path(git_dir)
        if not path.is_absolute():
            path = self.path / path
        (path / MARKER).write_text(json.dumps(marker, indent=1), encoding="utf-8")

    def _gather(self) -> Dict:
        g = self.sh.git
        refs = {}
        for line in g("for-each-ref", "--format=%(refname)%09%(objectname)").splitlines():
            name, sha = line.split("\t")
            refs[name] = sha
        branches = {n[len("refs/heads/"):]: s for n, s in refs.items() if n.startswith("refs/heads/")}
        tags = {n[len("refs/tags/"):]: s for n, s in refs.items() if n.startswith("refs/tags/")}
        remote_branches = {n[len("refs/remotes/"):]: s for n, s in refs.items() if n.startswith("refs/remotes/")}
        head_sha = g("rev-parse", "HEAD", check=False).strip()
        head_branch = g("symbolic-ref", "-q", "--short", "HEAD", check=False).strip() or None
        commits = []
        for line in g("log", "--all", "--date-order", "--format=%H%x09%P%x09%an%x09%s").splitlines():
            sha, parents, author, subject = line.split("\t", 3)
            commits.append({"sha": sha, "parents": parents.split(), "author": author, "message": subject})
        status = g("status", "--porcelain", "-z", check=False)
        modified, staged, untracked, conflicts = [], [], [], []
        for rec in status.split("\0"):
            if len(rec) < 4:
                continue
            x, y, path = rec[0], rec[1], rec[3:]
            if x in "UDA" and y in "UDA" and (x == "U" or y == "U" or (x == y)):
                conflicts.append(path)
            elif rec[:2] == "??":
                untracked.append(path)
            else:
                if x != " ":
                    staged.append(path)
                if y != " ":
                    modified.append(path)
        stashes = [l.split(": ", 1)[-1] for l in g("stash", "list", check=False).splitlines()]
        worktrees = [l[len("worktree "):] for l in g("worktree", "list", "--porcelain", check=False).splitlines() if l.startswith("worktree ")][1:]
        result = {
            "path": str(self.path),
            "seed": self.seed,
            "head": {"branch": head_branch, "sha": head_sha},
            "branches": branches,
            "tags": tags,
            "commits": commits,
            "files": g("ls-files", check=False).split("\n")[:-1] if g("ls-files", check=False) else [],
            "worktree": {"modified": modified, "staged": staged, "untracked": untracked, "conflicts": conflicts},
            "stashes": stashes,
            "worktrees": worktrees,
            "submodules": ["lib"] if self.spec.submodule else [],
            "remote": None,
        }
        if self.spec.remote:
            bare = self.parent / f"{self.spec.name}.origin.git"
            result["remote"] = {"name": "origin", "path": str(bare), "branches": remote_branches}
        return result


# ---- public entry points ------------------------------------------------------------------


def build(spec: Optional[Spec] = None, **options) -> Dict:
    """Build the repository a Spec (or keyword options) describes and return a
    description of what was made: path, head, branches, tags, commits, files,
    working-tree state, stashes, worktrees and the remote."""
    if spec is None:
        spec = Spec.from_dict(options)
    elif options:
        merged = spec.to_dict()
        merged.update(options)
        spec = Spec.from_dict(merged)
    return Builder(spec).build()


def script(spec: Spec) -> str:
    """The plain-shell equivalent of building the Spec, without building it."""
    b = Builder(spec, dry=True)
    b.build()
    head = ["#!/bin/sh", "# Generated by git-dummy. Runs with sh or bash; on Windows, Git Bash.", "set -e", ""]
    return "\n".join(head + b.sh.lines) + "\n"


def clean(path: str) -> List[str]:
    """Remove a repository git-dummy made, and what it made beside it. Refuses
    anything without git-dummy's marker file."""
    root = pathlib.Path(os.path.expanduser(path)).resolve()
    marker = None
    for candidate in (root / ".git" / MARKER, root / MARKER):
        if candidate.exists():
            marker = candidate
            break
    if marker is None:
        raise BuildError(f"{root} was not made by git-dummy (no {MARKER} in its .git/); not removing it")
    data = json.loads(marker.read_text(encoding="utf-8"))
    removed = []
    for extra in data.get("created", []):
        if os.path.exists(extra):
            _rmtree(extra)
            removed.append(extra)
    _rmtree(root)
    removed.append(str(root))
    return removed
