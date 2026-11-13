"""Third holdout. Lakeside, North Shore, and Cedar Row are not reused.

The name column sits beside a client-number column that also says "client".
Two do-not-contact sentences avoid the training phrases. A diary excuse uses
"didn't", and the newest text permission says "texts are okay".
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import process_folder


ATTENDANCE = """Maple Court export
Client #;Learner;Coach;Preferred channel;Visit 1;Visit 2;Visit 3;Visit 4;First check;Second check
M1;Marie Tremblay;Dana;call;showed;showed;showed;showed;8;14
M2;Rosa Silva;Dana;text;showed;showed;showed;showed;10;10
M3;Jean-Luc Bergeron;Dana;call;showed;showed;no-show;no-show;9;8
M4;Amina Yusuf;Dana;call;showed;showed;showed;showed;12;16
M5;Theo Banks;Dana;call;showed;showed;showed;showed;7;7
M6;Omar Haddad;Dana;call;showed;showed;no-show;no-show;9;9
M7;Darnell Cole;Dana;call;showed;showed;showed;showed;6;11
M8;Sam Cole;Dana;paper;showed;showed;showed;showed;10;10
M9;Sam Reid;Dana;call;showed;showed;showed;showed;11;14
M10;Nia Singh;Dana;text;showed;showed;showed;showed;8;8
M11;Leblanc, Patrice;Dana;call;showed;showed;showed;showed;9;12
M12;Leah Cormier;Dana;call;showed;no-show;showed;showed;14;15
M13;Cam Lowe;Dana;text;showed;showed;showed;showed;4;
M14;Josée Landry;Dana;text;showed;showed;showed;showed;5;10
M15;Paula Zwicker;Dana;text;showed;showed;showed;showed;13;13
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

NOTES = """Maple Court notes from the paper book. Not a client.
October 6th, 2026 | Dana | Marie Tremblay | Do not reach out until she asks.
October 20th, 2026 | Dana | Marie Tremblay | Own phone now. Texts are okay.
October 6th, 2026 | Dana | Rosa Silva | Do not reach out.
October 27th, 2026 | Dana | Jean-Luc Bergeron | Reviewed the household budget.
October 6th, 2026 | Dana | Amina Yusuf | I didn't set the diary this week.
October 13th, 2026 | Dana | Amina Yusuf | I didn't set the diary this week. Mail only from now on.
October 6th, 2026 | Dana | Theo Banks | Diary was set and collected.
October 13th, 2026 | Dana | Theo Banks | Diary was set and collected.
October 13th, 2026 | Dana | Omar Haddad | Away for work, told us ahead.
October 6th, 2026 | Dana | Darnell Cole | No phone calls, no text messages, and no letters.
October 13th, 2026 | Dana | Sam | Texts are okay.
October 6th, 2026 | Dana | M10 | Do not reach out.
October 20th, 2026 | Dana | Patrice Leblanc | Texts are okay.
October 6th, 2026 | Dana | Cam Lowe | Diary set for next week.
October 27th, 2026 | Dana | Leah Cormier | Diary set for next week.
October 20th, 2026 | Dana | Josee Landry | Call is fine.
October 6th, 2026 | Dana | Paula Zwicker | Diary on hold until the move is done.
October 20th, 2026 | Dana | Paula Zwicker | Still on hold. Session went long, so no new diary.
"""

EXPECTED = {
    "M1": ("on track", "text"),
    "M2": ("on track", "do not contact"),
    "M3": ("stalled", "call"),
    "M4": ("on track", "paper"),
    "M5": ("stalled", "call"),
    "M6": ("on track", "call"),
    "M7": ("on track", "do not contact"),
    "M8": ("on track", "paper"),
    "M9": ("on track", "call"),
    "M10": ("on track", "do not contact"),
    "M11": ("on track", "text"),
    "M12": ("on track", "call"),
    "M13": ("on track", "text"),
    "M14": ("on track", "call"),
    "M15": ("on track", "text"),
}


class MapleHoldoutTests(unittest.TestCase):
    def test_first_run_reaches_fifteen_of_fifteen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "maple-court-sheet.csv").write_text(ATTENDANCE, encoding="utf-8")
            (folder / "maple-court-homework.csv").write_text(DIARIES, encoding="utf-8")
            (folder / "maple-court-log.txt").write_text(NOTES, encoding="utf-8")
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
            self.assertEqual(report.agency_name, "Maple Court")
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
            self.assertNotIn("Darnell", summary)


if __name__ == "__main__":
    unittest.main()
