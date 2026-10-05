"""End-to-end tests: real git, real repositories in a temp folder."""

import json
import os
import subprocess
import sys

import pytest

from git_dummy import BuildError, Spec, build, clean, scenario_names, script


def git(path, *args):
    proc = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, f"git {' '.join(args)}: {proc.stderr}"
    return proc.stdout.strip()


def rev_list_count(path, spec):
    return int(git(path, "rev-list", "--count", spec))


@pytest.fixture(autouse=True)
def isolate_git_config(tmp_path, monkeypatch):
    cfg = tmp_path / "gitconfig"
    cfg.write_text("[user]\n\tname = Test\n\temail = test@example.com\n[init]\n\tdefaultBranch = main\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(cfg))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for key in list(os.environ):
        if key.startswith("git_dummy_") or key in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
            monkeypatch.delenv(key, raising=False)


def test_classic_defaults_are_unchanged(tmp_path):
    r = build(git_dir=str(tmp_path), name="classic", commits=5, branches=3, diverge_at=2, merge=[1])
    path = tmp_path / "classic"
    assert r["path"] == str(path)
    assert set(r["branches"]) == {"main", "branch1", "branch2"}
    # main: 5 commits plus the merge of branch1
    assert rev_list_count(path, "main") == 5 + 3 + 1
    assert rev_list_count(path, "branch2") == 5
    assert sorted(f for f in r["files"] if f.startswith("main.")) == [f"main.{i}" for i in range(1, 6)]
    assert git(path, "log", "-1", "--format=%s", "main") == "Merge branch1 into main"
    # the merge lists the branch first, as it always has
    parents = git(path, "log", "-1", "--format=%P", "main").split()
    assert parents[0] == r["branches"]["branch1"]
    assert git(path, "symbolic-ref", "--short", "HEAD") == "main"


def test_constant_sha_is_reproducible(tmp_path):
    a = build(git_dir=str(tmp_path), name="a", commits=4, branches=2, constant_sha=True)
    b = build(git_dir=str(tmp_path), name="b", commits=4, branches=2, constant_sha=True)
    assert a["branches"] == b["branches"]
    assert a["branches"]["main"] == b["branches"]["main"]


def test_seed_makes_realistic_content_reproducible(tmp_path):
    a = build(git_dir=str(tmp_path), name="a", commits=6, branches=3, style="realistic", seed=7)
    b = build(git_dir=str(tmp_path), name="b", commits=6, branches=3, style="realistic", seed=7)
    assert a["branches"] == b["branches"]
    messages = [c["message"] for c in a["commits"]]
    assert "Initial commit" in messages
    assert not any(m.startswith("Dummy commit") for m in messages)
    assert "README.md" in a["files"] and "app.py" in a["files"]
    assert any(b.startswith("feature/") or b.startswith("fix/") for b in a["branches"])
    authors = {c["author"] for c in a["commits"]}
    assert len(authors) > 1


def test_remote_ahead_and_behind(tmp_path):
    r = build(git_dir=str(tmp_path), name="rem", commits=4, remote=True, ahead=2, behind=3)
    path = tmp_path / "rem"
    remote = r["remote"]["path"]
    assert os.path.isdir(remote)
    assert os.path.basename(remote) == "rem.git"
    # added by a relative path, so no path from this machine gets into messages
    assert git(path, "remote", "get-url", "origin") == "../rem.git"
    # local main is 2 ahead of what it last fetched
    assert rev_list_count(path, "origin/main..main") == 2
    # the remote itself moved on by 3 that we have not fetched
    assert rev_list_count(remote, "main") == 4 + 3
    git(path, "fetch", "-q", "origin")
    assert rev_list_count(path, "main..origin/main") == 3
    assert git(path, "rev-parse", "--abbrev-ref", "main@{upstream}") == "origin/main"
    git(path, "merge", "-q", "--no-edit", "origin/main")
    git(path, "pull", "-q", "--no-rebase", "--no-edit")
    assert str(tmp_path) not in git(path, "log", "--format=%s", "-n", "3")


def test_build_from_a_scenario_with_overrides(tmp_path):
    r = build(scenario="orders", git_dir=str(tmp_path), commits=4)
    assert os.path.basename(r["path"]) == "orders"
    assert {"feature/pagination", "fix/order-totals"} <= set(r["branches"])
    assert r["remote"] is not None and os.path.basename(r["remote"]["path"]) == "orders.git"
    assert r["stashes"] and r["worktree"]["untracked"]


def test_orders_scenarios_are_reproducible(tmp_path):
    a = build(scenario="orders", git_dir=str(tmp_path / "a"))
    b = build(scenario="orders", git_dir=str(tmp_path / "b"))
    assert [c["sha"] for c in a["commits"]] == [c["sha"] for c in b["commits"]]
    behind = build(scenario="orders-behind", git_dir=str(tmp_path / "a"))
    path = behind["path"]
    git(path, "fetch", "-q", "origin")
    assert rev_list_count(path, "main..origin/main") == 2


def test_working_tree_states_and_stashes(tmp_path):
    r = build(git_dir=str(tmp_path), name="dirty", commits=5, modified=2, staged=1, untracked=2, stashes=2)
    assert len(r["worktree"]["modified"]) == 2
    assert len(r["worktree"]["staged"]) == 1
    assert sorted(r["worktree"]["untracked"]) == ["notes-2.txt", "scratch.txt"]
    assert len(r["stashes"]) == 2
    assert not set(r["worktree"]["modified"]) & set(r["worktree"]["staged"])


def test_conflict_leaves_a_stopped_merge(tmp_path):
    r = build(git_dir=str(tmp_path), name="cx", commits=3, conflict=True, style="realistic")
    path = tmp_path / "cx"
    assert r["worktree"]["conflicts"], r["worktree"]
    assert (path / ".git" / "MERGE_HEAD").exists()
    text = (path / r["worktree"]["conflicts"][0]).read_text(encoding="utf-8")
    assert "<<<<<<<" in text and ">>>>>>>" in text


def test_tags_octopus_orphan_and_detached(tmp_path):
    r = build(git_dir=str(tmp_path), name="shape", commits=6, branches=4, diverge_at=3,
              tags=["v1.0", "v2.0"], octopus=True, orphan_branch="gh-pages", detached=True)
    path = tmp_path / "shape"
    assert set(r["tags"]) == {"v1.0", "v2.0"}
    assert git(path, "rev-parse", "v2.0") == r["branches"]["main"]
    tip_parents = git(path, "log", "-1", "--format=%P", "main").split()
    assert len(tip_parents) == 4  # main plus three branches in one merge
    assert git(path, "rev-list", "--max-parents=0", "gh-pages") != git(path, "rev-list", "--max-parents=0", "main")
    assert r["head"]["branch"] is None
    assert r["head"]["sha"] == git(path, "rev-parse", "main~1")


def test_criss_cross(tmp_path):
    r = build(git_dir=str(tmp_path), name="cc", commits=4, branches=2, diverge_at=2, criss_cross=True)
    path = tmp_path / "cc"
    bases = git(path, "merge-base", "--all", "main", "branch1").split()
    assert len(bases) == 2


def test_worktree_and_submodule(tmp_path):
    r = build(git_dir=str(tmp_path), name="wt", commits=4, branches=2, diverge_at=2, worktree="branch1", submodule=True)
    path = tmp_path / "wt"
    assert len(r["worktrees"]) == 1 and os.path.isdir(r["worktrees"][0])
    assert git(r["worktrees"][0], "symbolic-ref", "--short", "HEAD") == "branch1"
    assert (path / ".gitmodules").exists()
    assert git(path, "ls-files", "-s", "lib").startswith("160000")


def test_reflog_and_checkout(tmp_path):
    r = build(git_dir=str(tmp_path), name="rl", commits=4, branches=2, diverge_at=2, reflog=3, checkout="branch1")
    path = tmp_path / "rl"
    assert r["head"]["branch"] == "branch1"
    assert int(git(path, "reflog", "show", "--format=%H", "HEAD").count("\n")) >= 6


@pytest.mark.parametrize("name", scenario_names())
def test_every_scenario_builds(tmp_path, name):
    r = build(scenario=name, git_dir=str(tmp_path), name=f"s-{name.replace('/', '-')}")
    assert os.path.isdir(r["path"])
    assert r["commits"]


def test_large_history_uses_fast_import(tmp_path):
    r = build(git_dir=str(tmp_path), name="big", commits=350, branches=3, diverge_at=100, merge=[1], fast=True, constant_sha=True)
    path = tmp_path / "big"
    assert rev_list_count(path, "main") == 350 + 250 + 1
    assert rev_list_count(path, "branch2") == 350
    assert (path / "main.350").exists()
    assert git(path, "status", "--porcelain") == ""


def test_fast_and_plain_agree_for_constant_sha(tmp_path):
    a = build(git_dir=str(tmp_path), name="plain", commits=6, branches=2, diverge_at=3, constant_sha=True, fast=False)
    b = build(git_dir=str(tmp_path), name="fast", commits=6, branches=2, diverge_at=3, constant_sha=True, fast=True)
    # trees and messages match; ids differ only by the timezone convention of the two paths
    for branch in ("main", "branch1"):
        assert git(tmp_path / "plain", "rev-parse", f"{branch}^{{tree}}") == git(tmp_path / "fast", "rev-parse", f"{branch}^{{tree}}")
        assert git(tmp_path / "plain", "log", "--format=%s", branch) == git(tmp_path / "fast", "log", "--format=%s", branch)


def test_print_script_runs(tmp_path):
    spec = Spec(git_dir=str(tmp_path / "out"), name="scripted", commits=3, branches=2, diverge_at=1,
                tags=["v1"], staged=1, untracked=1, remote=True, behind=1, ahead=1, constant_sha=True)
    text = script(spec)
    assert text.startswith("#!/bin/sh")
    assert "git init" in text and "git commit" in text and "fast-import" not in text
    sh = None
    for candidate in ("sh", r"C:\Program Files\Git\usr\bin\sh.exe"):
        try:
            subprocess.run([candidate, "-c", "true"], capture_output=True, check=True)
            sh = candidate
            break
        except (OSError, subprocess.CalledProcessError):
            continue
    if sh is None:
        pytest.skip("no sh to run the script with")
    (tmp_path / "out").mkdir()
    (tmp_path / "build.sh").write_text(text, encoding="utf-8", newline="\n")
    proc = subprocess.run([sh, str(tmp_path / "build.sh")], cwd=str(tmp_path / "out"), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    path = tmp_path / "out" / "scripted"
    assert rev_list_count(path, "main") == 3 + 1
    assert git(path, "tag") == "v1"
    assert git(path, "status", "--porcelain").count("\n") + 1 == 2
    assert rev_list_count(path, "origin/main..main") == 1


def test_recipe_json_and_clean(tmp_path):
    recipe = tmp_path / "repo.json"
    recipe.write_text(json.dumps({"scenario": "messy-worktree", "name": "fromfile", "commits": 3}), encoding="utf-8")
    spec = Spec.from_recipe(str(recipe))
    assert spec.style == "realistic" and spec.commits == 3 and spec.stashes == 1
    spec.git_dir = str(tmp_path)
    r = build(spec)
    assert os.path.isdir(r["path"])
    removed = clean(r["path"])
    assert not os.path.exists(r["path"]) and removed
    with pytest.raises(BuildError):
        clean(str(tmp_path))  # not made by git-dummy


def test_refuses_to_build_inside_a_repository(tmp_path):
    build(git_dir=str(tmp_path), name="outer", commits=1)
    with pytest.raises(BuildError):
        build(git_dir=str(tmp_path / "outer"), name="inner", commits=1)
    build(git_dir=str(tmp_path / "outer"), name="inner", commits=1, allow_nested=True)


def test_cli_json_and_list(tmp_path):
    env = dict(os.environ)
    out = subprocess.run([sys.executable, "-m", "git_dummy", "--list-scenarios"], capture_output=True, text=True, env=env)
    assert out.returncode == 0 and "merge-conflict" in out.stdout
    out = subprocess.run(
        [sys.executable, "-m", "git_dummy", "--git-dir", str(tmp_path), "--name", "cli", "--commits", "3", "--json", "--seed", "1", "--style", "realistic"],
        capture_output=True, text=True, env=env,
    )
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data["head"]["branch"] == "main" and len(data["commits"]) == 3
    out = subprocess.run([sys.executable, "-m", "git_dummy", "--git-dir", str(tmp_path), "--name", "cli", "--clean"], capture_output=True, text=True, env=env)
    assert out.returncode == 0 and not (tmp_path / "cli").exists()
