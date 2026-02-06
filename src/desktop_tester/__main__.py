"""Entry point for `python -m desktop_tester`."""

import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] != "gui":
        from desktop_tester.cli.main import cli
        cli()
    else:
        from desktop_tester.gui.app import run_app
        run_app()


if __name__ == "__main__":
    main()
