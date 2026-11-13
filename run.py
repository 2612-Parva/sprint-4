from __future__ import annotations

import argparse
import sys

from steady_money.reporter import (
    InputDiscoveryError,
    NotesUnreadableError,
    process_folder,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create Steady Money triage and impact reports from an agency folder."
    )
    parser.add_argument(
        "--folder",
        required=True,
        help="Folder containing attendance, diary, and counsellor-note files.",
    )
    parser.add_argument(
        "--output",
        help="Output folder. Defaults to the input folder.",
    )
    parser.add_argument(
        "--agency",
        help="Optional filename hint when one folder contains more than one agency.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = process_folder(
            args.folder,
            output_dir=args.output,
            agency_hint=args.agency,
            announce=print,
        )
    except NotesUnreadableError:
        print("ERROR: Cannot read notes. Halting.")
        return 2
    except InputDiscoveryError as exc:
        print(f"ERROR: {exc}")
        return 2
    except OSError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"Wrote: {report.results_path}")
    print(f"Wrote: {report.summary_path}")
    for warning in report.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
