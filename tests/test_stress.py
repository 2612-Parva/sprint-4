from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import process_folder


ATTENDANCE = """Case Number;Participant;Worker;Preferred Route;Session 1;Session 2;Session 3;Session 4;First Score;Second Score
O1;Patrice Leblanc;Adele Fortin;call;showed;showed;showed;showed;8/25;14/25
O2;Alex Martin;Adele Fortin;text;showed;showed;showed;showed;10/25;10/25
O3;Alex Nguyen;Adele Fortin;call;showed;showed;showed;showed;9/25;11/25
O4;Nia Singh;Adele Fortin;text;showed;showed;showed;showed;12/25;13/25
O5;Omar Haddad;Adele Fortin;email;missed;missed;showed;showed;7/25;7/25
O6;Renee Cormier;Adele Fortin;text;showed;showed;showed;showed;15/25;16/25
O7;Sam Cole;Adele Fortin;call;showed;showed;showed;showed;10/25;10/25
O8;Sam Reid;Adele Fortin;text;showed;showed;showed;showed;8/25;8/25
"""

DIARIES = """Participant,Week Number,Returned
Patrice Leblanc,1,not returned
Patrice Leblanc,2,not returned
Renee Cormier,1,not returned
Renee Cormier,2,not returned
"""

NOTES = """October 6, 2026 | Adele Fortin | Patrice Leblanc | Asked us not to reach out: no calls, no texts, no mail.
October 20, 2026 | Adele Fortin | Patrice Leblanc | Own phone now. Text is fine. Homework not assigned this week.
October 6, 2026 | Adele Fortin | Alex | Text is fine.
October 6, 2026 | Adele Fortin | Nia Singh | No calls, no texts, and no mail between sessions.
October 6, 2026 | Adele Fortin | Omar Haddad | Away for work in Ottawa, told us ahead.
October 13, 2026 | Adele Fortin | Omar Haddad | Still away for work.
October 6, 2026 | Adele Fortin | Renee Cormier | Diary set for next week.
October 10, 2026 | Adele Fortin | Extra Person | This date belongs to nobody on the sheet.
October 13, 2026 | Adele Fortin | Renee Cormier | Session ran over. Did not give the diary.
October 6, 2026 | Adele Fortin | Sam | Asked us not to reach out: no calls, no texts, no mail.
"""


SHEET = """Client ID,Client,Reach by,Mtg 1,Mtg 2,Check A,Check B
P1,Pat Lee,call,present,present,8,10
"""

PAGES = """Client,Week,Handed in
Pat Lee,1,yes
Pat Lee,2,yes
"""


def run_notes(folder_name: str, notes: str):
    folder = Path(folder_name)
    folder.mkdir()
    (folder / "sample-attendance.csv").write_text(SHEET, encoding="utf-8")
    (folder / "sample-diaries.csv").write_text(PAGES, encoding="utf-8")
    (folder / "sample-notes.txt").write_text(notes, encoding="utf-8")
    report = process_folder(folder, output_dir=folder / "out")
    return report.clients[0].way_to_reach


class StressScenarioTests(unittest.TestCase):
    def test_ottawa_style_changes_do_not_create_wrong_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "ottawa-roster.csv").write_text(ATTENDANCE, encoding="utf-8")
            (folder / "ottawa-weekly-pages.csv").write_text(DIARIES, encoding="utf-8")
            (folder / "ottawa-session-log.txt").write_text(NOTES, encoding="utf-8")

            report = process_folder(folder, output_dir=folder / "out")
            by_id = {row.client_id: row for row in report.clients}

            self.assertEqual(report.agency_name, "Ottawa")
            self.assertEqual(report.total_clients, 8)
            self.assertEqual((by_id["O1"].status, by_id["O1"].way_to_reach), ("on track", "text"))
            self.assertEqual(by_id["O2"].way_to_reach, "text")
            self.assertEqual(by_id["O3"].way_to_reach, "call")
            self.assertEqual(by_id["O7"].way_to_reach, "call")
            self.assertEqual(by_id["O8"].way_to_reach, "text")
            self.assertEqual(by_id["O4"].way_to_reach, "do not contact")
            self.assertEqual((by_id["O5"].status, by_id["O5"].way_to_reach), ("on track", "paper"))
            self.assertEqual(by_id["O6"].status, "on track")
            self.assertEqual(report.completed_both, 8)
            self.assertEqual(report.improved, 4)
            self.assertTrue(any("Alex" in warning for warning in report.warnings))
            summary = report.summary_path.read_text(encoding="utf-8")
            self.assertNotIn("Patrice", summary)
            self.assertIn("This is a halfway view.", summary)

    def test_month_first_dates_follow_a_proven_clue(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            contact = run_notes(
                str(Path(temporary) / "month"),
                "03/11/2026 | Worker | Pat Lee | Asked us not to reach out: no calls, no texts, no mail.\n"
                "03/15/2026 | Worker | Pat Lee | Own phone now. Text is fine.\n",
            )
            self.assertEqual(contact, "text")

    def test_ambiguous_dates_stay_day_first(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            contact = run_notes(
                str(Path(temporary) / "day"),
                "03/11/2026 | Worker | Pat Lee | Own phone now. Text is fine.\n"
                "04/10/2026 | Worker | Pat Lee | Asked us not to reach out: no calls, no texts, no mail.\n",
            )
            self.assertEqual(contact, "text")

    def test_reordered_names_and_case_numbers_still_match(self) -> None:
        notes = (
            "2026-11-03 | Worker | Lee, Pat | Own phone now. Text is fine.\n"
            "2026-11-03 | Worker | P2 | No calls, no texts, and no mail between sessions.\n"
        )
        sheet = SHEET + "P2,Nia Singh,text,present,present,9,9\n"
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "sample-attendance.csv").write_text(sheet, encoding="utf-8")
            (folder / "sample-diaries.csv").write_text(PAGES, encoding="utf-8")
            (folder / "sample-notes.txt").write_text(notes, encoding="utf-8")
            report = process_folder(folder, output_dir=folder / "out")
            by_id = {row.client_id: row for row in report.clients}
            self.assertEqual(by_id["P1"].way_to_reach, "text")
            self.assertEqual(by_id["P2"].way_to_reach, "do not contact")
            self.assertEqual(report.warnings, [])


if __name__ == "__main__":
    unittest.main()
