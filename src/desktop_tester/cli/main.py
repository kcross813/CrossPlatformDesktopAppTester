"""CLI entry point using Click."""

from __future__ import annotations

import click

from desktop_tester import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """DesktopTester - Desktop Application UAT Tool."""
    pass


@cli.command()
@click.argument("project_dir", type=click.Path(exists=True))
@click.option("--test", "-t", multiple=True, help="Specific test file(s) to run")
@click.option("--tag", multiple=True, help="Run tests matching these tags")
@click.option(
    "--report", "-r",
    type=click.Choice(["html", "json", "both"]),
    default="html",
    help="Report format",
)
@click.option("--output", "-o", type=click.Path(), help="Report output directory")
@click.option("--timeout", type=float, default=30.0, help="Global timeout per test")
@click.option("--slow-mode", type=float, default=0.0, help="Delay between steps (seconds)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(project_dir, test, tag, report, output, timeout, slow_mode, verbose):
    """Run tests in a DesktopTester project."""
    from desktop_tester.cli.run_cmd import execute_run

    exit_code = execute_run(
        project_dir=project_dir,
        test_files=test,
        tags=tag,
        report_format=report,
        output_dir=output,
        timeout=timeout,
        slow_mode=slow_mode,
        verbose=verbose,
    )
    raise SystemExit(exit_code)


@cli.command()
@click.argument("directory", type=click.Path())
@click.option("--name", "-n", prompt="Project name", help="Project name")
@click.option("--target", "-t", default="", help="Target app (bundle ID or name)")
def init(directory, name, target):
    """Initialize a new DesktopTester project."""
    from desktop_tester.cli.init_cmd import execute_init

    execute_init(directory, name, target)


@cli.command()
@click.argument("results_json", type=click.Path(exists=True))
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["html", "json"]),
    default="html",
    help="Report format",
)
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file path")
def report(results_json, fmt, output):
    """Generate a report from a JSON results file."""
    from desktop_tester.cli.report_cmd import execute_report

    execute_report(results_json, fmt, output)


@cli.command()
def gui():
    """Launch the DesktopTester GUI."""
    from desktop_tester.gui.app import run_app
    run_app()
