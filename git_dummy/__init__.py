"""git-dummy: generate Git repositories with the history, remote and
working-tree state you ask for.

    from git_dummy import build, Spec

    result = build(commits=6, branches=2, remote=True, behind=2, style="realistic")
    result["path"], result["branches"], result["remote"]

    build(Spec.from_recipe("repo.yaml"))
    build(scenario="merge-conflict", git_dir="/tmp")
"""

from git_dummy.builder import BuildError, build as _build, clean, script
from git_dummy.scenarios import SCENARIOS, apply_scenario, describe, names as scenario_names
from git_dummy.spec import Spec

__all__ = ["build", "clean", "script", "Spec", "BuildError", "SCENARIOS", "scenario_names", "describe"]


def build(spec: Spec = None, scenario: str = None, **options):
    """Build a repository. Pass a Spec, a scenario name, keyword options, or a
    scenario plus options that override it."""
    if scenario is not None:
        base = apply_scenario(scenario, spec or Spec())
        merged = base.to_dict()
        merged.update(options)
        return _build(Spec.from_dict(merged))
    return _build(spec, **options)
