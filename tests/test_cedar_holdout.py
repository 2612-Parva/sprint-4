"""A second holdout. Cole Street, Bayfield, Lakeside, and North Shore are not used.

Fifteen clients, semicolon headings, ordinal dates, initials, a shared first name,
and a do-not-contact sentence that does not use the training wording.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import NotesUnreadableError, process_folder


ATTENDANCE = """Cedar Row roll
Record Number;Learner;Coach;Preferred channel;Visit 1;Visit 2;Visit 3;Visit 4;First check;Second check
R1;Marie Tremblay;Dana;call;P;P;P;P;8;14
R2;Rosa Silva;Dana;call;P;P;P;P;10;10
R3;Jean-Luc Bergeron;Dana;call;P;P;A;NS;9;8
R4;Amina Yusuf;Dana;call;P;P;P;P;12;12
R5;Theo Banks;Dana;call;P;P;P;P;7;11
R6;Omar Haddad;Dana;call;P;P;A;A;9;9
R7;Darnell Cole;Dana;text;P;P;P;P;6;6
R8;Sam Cole;Dana;paper;P;P;P;P;10;13
R9;Sam Reid;Dana;call;P;P;P;P;11;11
R10;Nia Singh;Dana;text;P;P;P;P;8;8
R11;Leblanc, Patrice;Dana;call;P;P;P;P;9;12
R12;Leah Cormier;Dana;call;P;A;P;P;14;14
R13;Cam Lowe;Dana;text;P;P;P;P;4;
R14;Josée Landry;Dana;text;P;P;P;P;5/25;10/25
R15;Paula Zwicker;Dana;text;P;P;P;P;13;17
"""

DIARIES = """Learner,Week No,Handed in
Marie Tremblay,1,yes
Marie Tremblay,2,yes
Amina Yusuf,1,no
Amina Yusuf,2,no
Theo Banks,1,no
Theo Banks,2,no
Paula Zwicker,1,no
Paula Zwicker,2,no
Jean-Luc Bergeron,1,yes
Jean-Luc Bergeron,2,yes
"""

NOTES = """Cedar Row log. Copied in Ottawa. Not a client line.
6th October 2026 | Dana | Rosa Silva | Do not phone, do not text, and do not send mail.
6th October 2026 | Dana | Paula Zwicker | Diary on hold until the move is done.
6th October 2026 | Dana | Leah Cormier | Diary set for next week.
6th October 2026 | Dana | Cam Lowe | Diary set for next week.
6th October 2026 | Dana | Marie Tremblay | Asked us not to reach out: no calls, no texts, no mail.
13th October 2026 | Dana | Omar Haddad | Away for work, told us ahead, back after two visits.
13th October 2026 | Dana | Theo Banks | HW not set this week.
13th October 2026 | Dana | Sam | Text is fine.
13th October 2026 | Dana | Amina Yusuf | Letter only. Reviewed the household budget.
20th October 2026 | Dana | Marie Tremblay | Own phone now. Text is fine.
20th October 2026 | Dana | Darnell Cole | No texts, call evenings.
20th October 2026 | Dana | Patrice Leblanc | Text is fine.
20th October 2026 | Dana | Josee Landry | Call is fine.
27th October 2026 | Dana | Jean-Luc Bergeron | Reviewed the household budget. Diary was set.
27th October 2026 | Dana | Leah Cormier | Diary set for next week.
6th October 2026 | Dana | R10 | Do not phone, do not text, and do not send mail.
6th October 2026 | Dana | M. Tremblay | Seen this week. Diary set.
"""

EXPECTED = {
    "R1": ("on track", "text"),
    "R2": ("on track", "do not contact"),
    "R3": ("stalled", "call"),
    "R4": ("stalled", "paper"),
    "R5": ("on track", "call"),
    "R6": ("on track", "call"),
    "R7": ("on track", "call"),
    "R8": ("on track", "paper"),
    "R9": ("on track", "call"),
    "R10": ("on track", "do not contact"),
    "R11": ("on track", "text"),
    "R12": ("on track", "call"),
    "R13": ("on track", "text"),
    "R14": ("on track", "call"),
    "R15": ("on track", "text"),
}


class CedarHoldoutTests(unittest.TestCase):
    def test_first_run_scores_fifteen_of_fifteen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "cedar-row-sheet.csv").write_text(ATTENDANCE, encoding="utf-8")
            (folder / "cedar-row-homework.csv").write_text(DIARIES, encoding="utf-8")
            (folder / "cedar-row-log.txt").write_text(NOTES, encoding="utf-8")

            report = process_folder(folder, output_dir=folder / "out")
            by_id = {row.client_id: row for row in report.clients}
            mismatches = {
                client_id: (by_id[client_id].status, by_id[client_id].way_to_reach)
                for client_id in EXPECTED
                if (by_id[client_id].status, by_id[client_id].way_to_reach) != EXPECTED[client_id]
            }
            unsafe = [
                client_id
                for client_id, (_, contact) in EXPECTED.items()
                if contact == "do not contact" and by_id[client_id].way_to_reach != "do not contact"
            ]

            self.assertEqual(report.agency_name, "Cedar Row")
            self.assertEqual(report.total_clients, 15)
            self.assertEqual(list(by_id), list(EXPECTED))
            self.assertEqual(unsafe, [])
            self.assertEqual(mismatches, {})
            self.assertEqual(report.completed_both, 14)
            self.assertEqual(report.improved, 6)
            summary = report.summary_path.read_text(encoding="utf-8")
            self.assertIn("Number of Clients Who Started: 15", summary)
            self.assertIn("This is a halfway view.", summary)
            self.assertNotIn("Marie", summary)
            self.assertNotIn("Rosa", summary)
            columns = report.results_path.read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(columns, "client_id,status,way_to_reach,why")

    def test_unreadable_cedar_notes_do_not_write_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "cedar-row-sheet.csv").write_text(ATTENDANCE, encoding="utf-8")
            (folder / "cedar-row-homework.csv").write_text(DIARIES, encoding="utf-8")
            (folder / "cedar-row-log.txt").write_text(
                "\n".join(f"???? line {index}" for index in range(12)),
                encoding="utf-8",
            )
            with self.assertRaises(NotesUnreadableError):
                process_folder(folder, output_dir=folder / "out")
            self.assertFalse((folder / "out" / "results.csv").exists())
            self.assertFalse((folder / "out" / "summary.md").exists())


if __name__ == "__main__":
    unittest.main()
