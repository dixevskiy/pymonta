"""
Command line interface for `pymonta`.

This module provides the entry point for the `pymonta` CLI. It exposes two
subcommands:
- `init` : Creates a new project structure at the specified path.
- `version` : Prints the installed version of `pymonta`.

The actual project generation is delegated to `pymonta.proj_funcs.generate_project`.
"""

import argparse
import importlib.metadata
from pathlib import Path

from pymonta.proj_funcs import generate_project


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
        "pymonta", description="video editing tool for tech nerds"
    )
    parser.add_argument(
        "-p", "--proj_path", help="specify project root directory", type=str
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<COMMAND>"
    )
    subparsers.add_parser("init", help="initialize a project")
    subparsers.add_parser("version", help="get version of pymonta")
    subparsers.add_parser("help", help="get basic information about how to use library")
    args = parser.parse_args()

    if args.command == "init":
        proj_path = args.proj_path if args.proj_path else str(Path().cwd())
        generate_project(proj_path)
        print(f"Created a project at {proj_path} for you!")

    if args.command == "version":
        print(f"You are using pymonta version {importlib.metadata.version('pymonta')}")

    if args.command == "help":
        print(
            "pymonta is a tool library for video editing with Python\nHow to use it:\n0. Install pymonta\n1. Create a project with pymonta init\n2. Check out generated video_script.py\n3. Import the lib and use help(pymonta) to know more\n4. Edit video_script.py accordingly\n5. Run python video_script.py to render video"
        )


if __name__ == "__main__":
    main()
