"""Ensure a release tag names the distribution version being uploaded."""

import sys
from pathlib import Path

import tomllib


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check_release_tag.py vX.Y.Z")
    tag = sys.argv[1]
    with (Path(__file__).resolve().parent.parent / "pyproject.toml").open("rb") as file:
        version = tomllib.load(file)["project"]["version"]
    if tag != f"v{version}":
        raise SystemExit(
            f"Release tag {tag!r} does not match pyproject version v{version}"
        )
    print(f"Release tag verified: {tag}")


if __name__ == "__main__":
    main()
