"""Fourth holdout. Maple Court, Cedar Row, Lakeside, and North Shore are not reused.

Dates are written 13-Oct-2026. Score columns say Check One and Check Two.
One diary excuse says "wasn't set", and one no-contact line says "no post".
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import process_folder


ATTENDANCE = """Riverbend export
Case No;Learner;Coach;Preferred channel;Visit 1;Visit 2;Visit 3;Visit 4;Check One;Check Two
B1;Marie Tremblay;Dana;call;showed;showed;showed;showed;8;14
B2;Rosa Silva;Dana;text;showed;showed;showed;showed;10;10
B3;Jean-Luc Bergeron;Dana;call;showed;showed;did not attend;did not attend;9;8
B4;Amina Yusuf;Dana;call;showed;showed;showed;showed;12;16
B5;Theo Banks;Dana;call;showed;showed;showed;showed;7;7
B6;Omar Haddad;Dana;call;showed;showed;did not attend;did not attend;9;9
B7;Darnell Cole;Dana;call;showed;showed;showed;showed;6;11
B8;Sam Cole;Dana;paper;showed;showed;showed;showed;10;10
B9;Sam Reid;Dana;call;showed;showed;showed;showed;11;14
B10;Nia Singh;Dana;text;showed;showed;showed;showed;8;8
B11;Leblanc, Patrice;Dana;call;showed;showed;showed;showed;9;12
B12;Leah Cormier;Dana;call;showed;did not attend;showed;showed;14;15
B13;Cam Lowe;Dana;text;showed;showed;showed;showed;4;
B14;Josée Landry;Dana;text;showed;showed;showed;showed;5;10
B15;Paula Zwicker;Dana;text;showed;showed;showed;showed;13;13
"""

DIARIES = """Learner,Week No,Handed in
Amina Yusuf,1,no
Amina Yusuf,2,no
Theo Banks,1,no
Theo Banks,2,no
Paula Zwicker,1,no
Paula Zwicker,2,no
Marie Tremblay,1,yes
Marie Tremblay,2,yes
"""

NOTES = """Riverbend log typed from the book. Not a client.
13-Oct-2026 | Dana | Marie Tremblay | No calls, no texts, and no post.
27-Oct-2026 | Dana | Marie Tremblay | Own phone now. Texts are okay.
13-Oct-2026 | Dana | Rosa Silva | No calls, no texts, and no post.
03-Nov-2026 | Dana | Jean-Luc Bergeron | Reviewed the household budget.
13-Oct-2026 | Dana | Amina Yusuf | Homework wasn't set this week.
20-Oct-2026 | Dana | Amina Yusuf | Homework wasn't set this week. Post only from now on.
13-Oct-2026 | Dana | Theo Banks | Diary was set and collected.
20-Oct-2026 | Dana | Theo Banks | Diary was set and collected.
20-Oct-2026 | Dana | Omar Haddad | Away for work, told us ahead.
13-Oct-2026 | Dana | Darnell Cole | Do not reach out.
20-Oct-2026 | Dana | Sam | Texts are okay.
13-Oct-2026 | Dana | B10 | Do not reach out.
27-Oct-2026 | Dana | Patrice Leblanc | Texts are okay.
13-Oct-2026 | Dana | Cam Lowe | Diary set for next week.
03-Nov-2026 | Dana | Leah Cormier | Diary set for next week.
27-Oct-2026 | Dana | Josee Landry | Call is fine.
13-Oct-2026 | Dana | Paula Zwicker | Diary on hold until the move is done.
27-Oct-2026 | Dana | Paula Zwicker | Still on hold.
"""

EXPECTED = {
    "B1": ("on track", "text"),
    "B2": ("on track", "do not contact"),
    "B3": ("stalled", "call"),
    "B4": ("on track", "paper"),
    "B5": ("stalled", "call"),
    "B6": ("on track", "call"),
    "B7": ("on track", "do not contact"),
    "B8": ("on track", "paper"),
    "B9": ("on track", "call"),
    "B10": ("on track", "do not contact"),
    "B11": ("on track", "text"),
    "B12": ("on track", "call"),
    "B13": ("on track", "text"),
    "B14": ("on track", "call"),
    "B15": ("on track", "text"),
}


class RiverbendHoldoutTests(unittest.TestCase):
    def test_first_run_reaches_fifteen_of_fifteen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "riverbend-sheet.csv").write_text(ATTENDANCE, encoding="utf-8")
            (folder / "riverbend-homework.csv").write_text(DIARIES, encoding="utf-8")
            (folder / "riverbend-log.txt").write_text(NOTES, encoding="utf-8")
            report = process_folder(folder, output_dir=folder / "out")
            by_id = {row.client_id: row for row in report.clients}
            mismatches = {
                client_id: (
                    (by_id[client_id].status, by_id[client_id].way_to_reach),
                    EXPECTED[client_id],
                )
                for client_id in EXPECTED
                if (by_id[client_id].status, by_id[client_id].way_to_reach) != EXPECTED[client_id]
            }
            unsafe = [
                client_id
                for client_id, (_, contact) in EXPECTED.items()
                if contact == "do not contact" and by_id[client_id].way_to_reach != "do not contact"
            ]
            self.assertEqual(report.agency_name, "Riverbend")
            self.assertEqual(report.total_clients, 15)
            self.assertEqual(list(by_id), list(EXPECTED))
            self.assertEqual(unsafe, [])
            self.assertEqual(mismatches, {})
            self.assertEqual(report.completed_both, 14)
            self.assertEqual(report.improved, 7)
            summary = report.summary_path.read_text(encoding="utf-8")
            self.assertIn("Number of Clients Who Started: 15", summary)
            self.assertIn("This is a halfway view.", summary)
            self.assertNotIn("Marie", summary)
            self.assertNotIn("Rosa", summary)


if __name__ == "__main__":
    unittest.main()
