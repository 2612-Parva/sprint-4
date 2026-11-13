from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import NotesUnreadableError, process_folder


ROOT = Path(__file__).resolve().parents[1]


class ReporterAcceptanceTests(unittest.TestCase):
    def make_agency_folder(self, prefix: str) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        base = Path(temporary.name)
        inputs = base / "inputs"
        outputs = base / "outputs"
        inputs.mkdir()
        for suffix in ("attendance.csv", "diaries.csv", "counsellor-notes.txt"):
            source = ROOT / f"{prefix}-{suffix}"
            shutil.copy2(source, inputs / source.name)
        return temporary, inputs, outputs

    def test_bayfield_named_cases(self) -> None:
        temporary, inputs, outputs = self.make_agency_folder("bayfield")
        self.addCleanup(temporary.cleanup)

        report = process_folder(inputs, output_dir=outputs)
        by_id = {row.client_id: row for row in report.clients}

        self.assertEqual(report.agency_name, "Bayfield")
        self.assertEqual(report.total_clients, 6)
        self.assertEqual((by_id["B11"].status, by_id["B11"].way_to_reach), ("on track", "call"))
        self.assertEqual((by_id["B12"].status, by_id["B12"].way_to_reach), ("on track", "paper"))
        self.assertEqual(
            (by_id["B15"].status, by_id["B15"].way_to_reach),
            ("stalled", "do not contact"),
        )
        self.assertEqual((by_id["B13"].status, by_id["B13"].way_to_reach), ("stalled", "call"))

    def test_cole_street_named_cases(self) -> None:
        temporary, inputs, outputs = self.make_agency_folder("cole-street")
        self.addCleanup(temporary.cleanup)

        report = process_folder(inputs, output_dir=outputs)
        by_id = {row.client_id: row for row in report.clients}

        self.assertEqual(report.agency_name, "Cole Street")
        self.assertEqual(report.total_clients, 48)
        self.assertEqual(
            (by_id["C-1100"].status, by_id["C-1100"].way_to_reach),
            ("stalled", "text"),
        )
        self.assertEqual(
            (by_id["C-1111"].status, by_id["C-1111"].way_to_reach),
            ("on track", "text"),
        )
        self.assertEqual(
            (by_id["C-1127"].status, by_id["C-1127"].way_to_reach),
            ("stalled", "do not contact"),
        )
        self.assertEqual(
            (by_id["C-1133"].status, by_id["C-1133"].way_to_reach),
            ("on track", "do not contact"),
        )
        self.assertEqual(by_id["C-1101"].way_to_reach, "text")
        self.assertEqual(by_id["C-1102"].way_to_reach, "text")
        self.assertEqual(by_id["C-1110"].way_to_reach, "call")
        self.assertEqual(by_id["C-1115"].way_to_reach, "paper")
        self.assertEqual(by_id["C-1118"].way_to_reach, "paper")
        self.assertEqual(by_id["C-1121"].way_to_reach, "call")
        for result in report.clients:
            self.assertGreaterEqual(len(result.why.split()), 3)
            self.assertLessEqual(len(result.why.split()), 5)

    def test_summary_is_anonymous_and_has_required_lines(self) -> None:
        temporary, inputs, outputs = self.make_agency_folder("cole-street")
        self.addCleanup(temporary.cleanup)

        report = process_folder(inputs, output_dir=outputs)
        summary = report.summary_path.read_text(encoding="utf-8")

        self.assertIn("- Agency Name: Cole Street", summary)
        self.assertIn("- Total Clients: 48", summary)
        self.assertIn("- Number of Clients Who Started: 48", summary)
        self.assertIn("- Completed Both Money Checks:", summary)
        self.assertIn("- Improved:", summary)
        self.assertIn(
            '- Definition of Improved: "A client who completed both Money Checks and '
            'increased their score from the first to the second."',
            summary,
        )
        self.assertIn(
            '- Note: "This is a halfway view. Final scores are not yet available."',
            summary,
        )
        self.assertNotIn("Raymond", summary)
        self.assertNotIn("902-", summary)

    def test_missing_notes_halts_without_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            inputs = base / "inputs"
            outputs = base / "outputs"
            inputs.mkdir()
            shutil.copy2(
                ROOT / "bayfield-attendance.csv",
                inputs / "unknown-agency-attendance.csv",
            )

            with self.assertRaises(NotesUnreadableError):
                process_folder(inputs, output_dir=outputs)

            self.assertFalse((outputs / "results.csv").exists())
            self.assertFalse((outputs / "summary.md").exists())

    def test_cli_prints_exact_notes_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            inputs = base / "inputs"
            outputs = base / "outputs"
            inputs.mkdir()
            shutil.copy2(
                ROOT / "bayfield-attendance.csv",
                inputs / "unknown-agency-attendance.csv",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "run.py"),
                    "--folder",
                    str(inputs),
                    "--output",
                    str(outputs),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertEqual(completed.stdout.strip(), "ERROR: Cannot read notes. Halting.")
            self.assertFalse((outputs / "results.csv").exists())
            self.assertFalse((outputs / "summary.md").exists())

    def test_unrecognizable_note_dates_halt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            inputs = base / "inputs"
            outputs = base / "outputs"
            inputs.mkdir()
            shutil.copy2(
                ROOT / "bayfield-attendance.csv",
                inputs / "example-attendance.csv",
            )
            shutil.copy2(
                ROOT / "bayfield-diaries.csv",
                inputs / "example-diaries.csv",
            )
            (inputs / "example-notes.txt").write_text(
                "Thirteenth of October | Carol: Diary set.\n"
                "Twentieth of October | Theo: HW not set.\n",
                encoding="utf-8",
            )

            with self.assertRaises(NotesUnreadableError):
                process_folder(inputs, output_dir=outputs)

            self.assertFalse((outputs / "results.csv").exists())
            self.assertFalse((outputs / "summary.md").exists())


if __name__ == "__main__":
    unittest.main()
