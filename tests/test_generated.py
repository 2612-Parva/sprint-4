"""Holdout cases built from the training files, not copied from them.

Cole Street and Bayfield stay the training data. This file is a new agency
with mixed layouts, accents, reordered names, case numbers, old instructions,
and one shared first name.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import NotesUnreadableError, process_folder


ATTENDANCE = """Participant ID	Full Name	Advisor	How to reach	Class 1	Class 2	Class 3	Class 4	Baseline score	Midpoint score
C01	Marie Tremblay	Dana	call	showed	showed	showed	showed	8/25	14/25
C02	Jean-Luc Bergeron	Dana	text	showed	showed	absent	no show	10/25	9/25
C03	Amina Yusuf	Dana	call	showed	showed	showed	showed	12/25	12/25
C04	Theo Banks	Dana	call	showed	showed	showed	showed	7/25	11/25
C05	Omar Haddad	Dana	call	showed	showed	missed	missed	9/25	9/25
C06	Rosa Silva	Dana	text	showed	showed	showed	showed	15/25	16/25
C07	Darnell Cole	Dana	text	showed	showed	showed	showed	6/25	6/25
C08	Alex Martin	Dana	paper	showed	showed	showed	showed	10/25	13/25
C09	Alex Nguyen	Dana	call	showed	showed	showed	showed	11/25	11/25
C10	Nia Singh	Dana	text	showed	showed	showed	showed	8/25	8/25
C11	Patrice Leblanc	Dana	call	showed	showed	showed	showed	9/25	12/25
C12	Leah Cormier	Dana	call	showed	absent	showed	showed	14/25	14/25
C13	Cam Lowe	Dana	text	showed	showed	showed	showed	4/25	
C14	Josée Landry	Dana	call	showed	showed	showed	showed	5/25	10/25
C15	Paula Zwicker	Dana	text	showed	showed	showed	showed	13/25	17/25
"""

DIARIES = """Full Name,Homework week,Handed in
Marie Tremblay,1,yes
Marie Tremblay,2,yes
Amina Yusuf,1,not returned
Amina Yusuf,2,not returned
Theo Banks,1,not returned
Theo Banks,2,not returned
Rosa Silva,1,yes
Rosa Silva,2,yes
Paula Zwicker,1,no
Paula Zwicker,2,no
Jean-Luc Bergeron,1,yes
Jean-Luc Bergeron,2,yes
"""

NOTES = """Lakeside notes copied from paper. Ottawa office. This line is not a client.
Staff reminder: keep the halfway scores blank when the second check is not done.
[2026-10-06] Dana | Marie Tremblay: Asked us not to reach out: no calls, no texts, no mail.
October 20, 2026 | Dana | Marie Tremblay | Own phone now. Text is fine.
October 27, 2026 | Dana | Jean-Luc Bergeron | Reviewed the household budget. Diary was set.
October 13, 2026 | Dana | Amina Yusuf | Letter only from now on.
October 13, 2026 | Dana | Theo Banks | Homework not assigned this week.
October 13, 2026 | Dana | Omar Haddad | Away for work Oct 20 + Oct 27, told us ahead.
[2026-10-06] Dana | Rosa Silva: No calls, no texts, and no mail between sessions.
October 20, 2026 | Dana | Darnell Cole | No texts, call evenings.
October 13, 2026 | Dana | Alex | Text is fine.
October 6, 2026 | Dana | C10 | No calls, no texts, and no mail between sessions.
October 20, 2026 | Dana | Leblanc, Patrice | Text is fine.
October 6, 2026 | Dana | Cam Lowe | Diary set for next week.
October 6, 2026 | Dana | Leah Cormier | Diary set for next week.
October 27, 2026 | Dana | Leah Cormier | Diary set for next week.
October 20, 2026 | Dana | Josee Landry | Text is fine.
[2026-10-06] Dana | Paula Zwicker: Diary on hold until she is back from the move.
"""

EXPECTED = {
    "C01": ("on track", "text"),
    "C02": ("stalled", "text"),
    "C03": ("stalled", "paper"),
    "C04": ("on track", "call"),
    "C05": ("on track", "call"),
    "C06": ("on track", "do not contact"),
    "C07": ("on track", "call"),
    "C08": ("on track", "paper"),
    "C09": ("on track", "call"),
    "C10": ("on track", "do not contact"),
    "C11": ("on track", "text"),
    "C12": ("on track", "call"),
    "C13": ("on track", "text"),
    "C14": ("on track", "text"),
    "C15": ("on track", "text"),
}


class GeneratedHoldoutTests(unittest.TestCase):
    def test_fifteen_complex_clients_keep_their_own_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "lakeside-register.csv").write_text(ATTENDANCE, encoding="utf-8")
            (folder / "lakeside-weekly.csv").write_text(DIARIES, encoding="utf-8")
            (folder / "lakeside-notes.txt").write_text(NOTES, encoding="utf-8")

            report = process_folder(folder, output_dir=folder / "out")
            by_id = {row.client_id: row for row in report.clients}

            self.assertEqual(report.agency_name, "Lakeside")
            self.assertEqual(report.total_clients, 15)
            self.assertEqual(list(by_id), list(EXPECTED))
            mismatches = {
                client_id: (row.status, row.way_to_reach)
                for client_id, row in by_id.items()
                if (row.status, row.way_to_reach) != EXPECTED[client_id]
            }
            self.assertEqual(mismatches, {})
            self.assertEqual(report.completed_both, 14)
            self.assertEqual(report.improved, 7)
            self.assertTrue(any("Alex" in warning for warning in report.warnings))
            summary = report.summary_path.read_text(encoding="utf-8")
            for name in ("Marie", "Jean", "Amina", "Josée", "Paula"):
                self.assertNotIn(name, summary)
            self.assertIn("This is a halfway view.", summary)

    def test_mostly_unreadable_generated_notes_still_halt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "lakeside-register.csv").write_text(ATTENDANCE, encoding="utf-8")
            (folder / "lakeside-weekly.csv").write_text(DIARIES, encoding="utf-8")
            (folder / "lakeside-notes.txt").write_text(
                "\n".join(f"noise {index} @@@@ ####" for index in range(12)),
                encoding="utf-8",
            )
            with self.assertRaises(NotesUnreadableError):
                process_folder(folder, output_dir=folder / "out")
            self.assertFalse((folder / "out" / "results.csv").exists())

    def test_title_row_reordered_sheet_and_swapped_contact_words(self) -> None:
        attendance = """North Shore attendance export
Participant ID,Full Name,Advisor,How to reach,Class 1,Class 2,Class 3,Class 4,Baseline score,Midpoint score
N1,"Tremblay, Marie",Dana,text,showed,showed,showed,showed,8,10
N2,"Bergeron, Jean-Luc",Dana,call,showed,showed,showed,showed,8,8
N3,"Cole, Darnell",Dana,paper,showed,showed,showed,showed,8,9
"""
        diaries = """Full Name,Homework week,Handed in
"Tremblay, Marie",1,yes
"Bergeron, Jean-Luc",1,yes
"Cole, Darnell",1,yes
"""
        notes = """October 6, 2026 | Dana | Marie Tremblay | Call is fine.
October 6, 2026 | Dana | Bergeron | Text only from now on.
October 6, 2026 | Dana | Cole | Phone is fine.
"""
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "north-shore-register.csv").write_text(attendance, encoding="utf-8")
            (folder / "north-shore-weekly.csv").write_text(diaries, encoding="utf-8")
            (folder / "north-shore-notes.txt").write_text(notes, encoding="utf-8")
            report = process_folder(folder, output_dir=folder / "out")
            by_id = {row.client_id: row for row in report.clients}
            self.assertEqual(report.agency_name, "North Shore")
            self.assertEqual(report.total_clients, 3)
            self.assertEqual(by_id["N1"].way_to_reach, "call")
            self.assertEqual(by_id["N2"].way_to_reach, "text")
            self.assertEqual(by_id["N3"].way_to_reach, "call")
            self.assertTrue(all(row.status == "on track" for row in report.clients))


if __name__ == "__main__":
    unittest.main()
