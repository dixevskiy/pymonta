import argparse
from pathlib import Path

from pycut.proj_funcs import generate_project


def main():
    parser = argparse.ArgumentParser("pycut")
    parser.add_argument(
        "-p", "--proj_path", help="specify project root directory", type=str
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<COMMAND>"
    )
    subparsers.add_parser("init", help="initialize a project")
    args = parser.parse_args()
    if args.command == "init":
        proj_path = args.proj_path if args.proj_path else str(Path().cwd())
        generate_project(proj_path)
        print(f"Created a project at {proj_path} for you!")


if __name__ == "__main__":
    main()
