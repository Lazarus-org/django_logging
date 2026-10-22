"""Guard that metadata, the tox environments and CI test matrix agree.

Run with Python 3.11+ and PyYAML (in CI's static job). This doesn't
execute Django; it prevents accidental loss of promised compatibility
coverage.

"""

from __future__ import annotations

import configparser
import sys
from pathlib import Path

import tomllib
import yaml

ROOT = Path(__file__).resolve().parent.parent


def validate() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_python = project["project"]["requires-python"]
    poetry_python = project["tool"]["poetry"]["dependencies"]["python"]
    assert project_python == poetry_python, "Conflicting Python metadata constraints"
    assert project_python == ">=3.10,<3.15", "Unexpected Python compatibility change"

    declared = set(project["project"]["classifiers"])
    for python in ("3.10", "3.11", "3.12", "3.13", "3.14"):
        assert f"Programming Language :: Python :: {python}" in declared
    for django in ("5.2", "6.0", "6.1"):
        assert f"Framework :: Django :: {django}" in declared

    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "tox.ini")
    tox_envs = set(config["tox"]["env_list"].split())
    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    rows = ci["jobs"]["test"]["strategy"]["matrix"]["include"]
    ci_envs = {f"py{row['py']}-django{row['django']}" for row in rows}
    assert tox_envs == ci_envs, (
        f"Missing CI environments: {sorted(tox_envs - ci_envs)}; "
        f"Unexpected CI environments: {sorted(ci_envs - tox_envs)}"
    )
    assert len(ci_envs) == len(rows), "Duplicate CI matrix rows"

    for row in rows:
        py = row["py"]
        assert row["python"].replace(".", "") == py
        if row["django"] in ("60", "61"):
            assert int(py) >= 312, "Django 6 requires Python >=3.12"

    release = yaml.safe_load(
        (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    )
    assert release["jobs"]["verify"]["uses"] == "./.github/workflows/ci.yml"
    assert "verify" in release["jobs"]["release"]["needs"].split()
    assert "test" in ci["jobs"]["package"]["needs"]
    assert "static" in ci["jobs"]["package"]["needs"]
    print(f"Release matrix verified: {len(ci_envs)} Python/Django combinations")


if __name__ == "__main__":
    try:
        validate()
    except (AssertionError, KeyError, ValueError) as exc:
        sys.exit(f"Release configuration validation failed: {exc}")
