"""
Command‑line interface for `pycut`.

This module provides the entry point for the `pycut` CLI. It exposes two
subcommands:
- `init` : Creates a new project structure at the specified path.
- `version` : Prints the installed version of `pycut`.

The actual project generation is delegated to `pycut.proj_funcs.generate_project`.
"""

import argparse
import importlib.metadata
from pathlib import Path

from pycut.proj_funcs import generate_project


def main() -> None:
    """Parse command line arguments and execute the requested subcommand.

    This function sets up an argument parser with:
        - A positional `-p/--proj_path` option (used by `init`).
        - Two subcommands: `init` and `version`.

    - For `init`: creates a project at the given path (current directory by default).
    - For `version`: prints the package version from installed metadata.

    Returns:
        None

    Raises:
        Any exception raised by `generate_project` (e.g., file permission errors)
            will propagate to the caller.
    """
    parser = argparse.ArgumentParser(
        "pycut", description="video editing tool for tech nerds"
    )
    parser.add_argument(
        "-p", "--proj_path", help="specify project root directory", type=str
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<COMMAND>"
    )
    subparsers.add_parser("init", help="initialize a project")
    subparsers.add_parser("version", help="get version of pycut")
    args = parser.parse_args()

    if args.command == "init":
        proj_path = args.proj_path if args.proj_path else str(Path().cwd())
        generate_project(proj_path)
        print(f"Created a project at {proj_path} for you!")

    if args.command == "version":
        print(f"You are using pycut version {importlib.metadata.version('pycut')}")


if __name__ == "__main__":
    main()