"""Command-line interface for the baseline PyFireCA static simulator."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from pyfireca.config import load_static_run_config
from pyfireca.workflow import run_static_config, validate_static_run


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyfireca",
        description="Run the validated static PyFireCA wildfire simulator.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="validate configuration and all referenced static raster inputs",
    )
    validate_parser.add_argument("config", type=Path, help="path to a version-1 YAML config")

    run_parser = subparsers.add_parser(
        "run",
        help="validate and execute one reproducible static simulation run",
    )
    run_parser.add_argument("config", type=Path, help="path to a version-1 YAML config")
    return parser


def _run_validate(config_path: Path) -> int:
    config = load_static_run_config(config_path)
    validate_static_run(config)
    print(f"Valid PyFireCA configuration: {config_path.resolve()}")
    return 0


def _run_simulation(config_path: Path) -> int:
    config = load_static_run_config(config_path)
    result, artifacts = run_static_config(config)
    metrics = result.summary_metrics()
    print(f"PyFireCA run complete: {artifacts.directory}")
    print(f"Burned cells: {metrics['burned_cell_count']}")
    print(f"Burned area: {metrics['burned_area_m2']:.3f} m^2")
    print(f"Last arrival: {metrics['last_arrival_s']:.3f} s")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the PyFireCA CLI and return a process exit status."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return _run_validate(args.config)
        if args.command == "run":
            return _run_simulation(args.config)
    except Exception as exc:  # noqa: BLE001 - CLI boundary converts failures to exit status.
        print(f"pyfireca: error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
