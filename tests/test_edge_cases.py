"""Edge cases for the scored fields. Each test is one way the result can go wrong."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import NotesUnreadableError, process_folder


def run(attendance: str, diaries: str, notes: str, stem: str = "edge"):
    folder = Path(tempfile.mkdtemp())
    (folder / f"{stem}-attendance.csv").write_text(attendance, encoding="utf-8")
    (folder / f"{stem}-diaries.csv").write_text(diaries, encoding="utf-8")
    (folder / f"{stem}-notes.txt").write_text(notes, encoding="utf-8")
    return process_folder(folder, output_dir=folder / "out")


def sheet(rows: list[str]) -> str:
    header = "Client ID,Client,Reach by,Mtg 1,Mtg 2,Check A,Check B\n"
    return header + "\n".join(rows) + "\n"


def pages(rows: list[str]) -> str:
    return "Client,Week,Handed in\n" + "\n".join(rows) + "\n"


class EdgeCaseTests(unittest.TestCase):
    def test_calls_only_means_call(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,text,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Calls only from now on.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_email_is_fine_means_paper(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Email is fine.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "paper")

    def test_whatsapp_is_fine_means_text(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | WhatsApp is fine.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_newest_do_not_contact_beats_older_text(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Text is fine.\n"
            "20 Oct 2026 | Dana | Pat Lee | Do not contact.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_same_day_later_line_wins(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Text is fine.\n"
            "13 Oct 2026 | Dana | Pat Lee | No calls, no texts, and no mail.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_no_texts_alone_keeps_the_attendance_call(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | No texts.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_one_absence_and_one_diary_miss_stays_on_track(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,absent,present,8,10"]),
            pages(["Pat Lee,1,no", "Pat Lee,2,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary set.\n20 Oct 2026 | Dana | Pat Lee | Diary set.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_two_dotted_absences_stall(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,A.,A.,8,9"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Seen the household budget.\n",
        )
        self.assertEqual((report.clients[0].status, report.clients[0].way_to_reach), ("stalled", "call"))

    def test_wasnt_handed_in_counts_as_two_misses(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,wasn't handed in", "Pat Lee,2,wasn't handed in"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary was set.\n20 Oct 2026 | Dana | Pat Lee | Diary was set.\n",
        )
        self.assertEqual(report.clients[0].status, "stalled")

    def test_wasnt_set_excuses_both_diary_weeks(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,12"]),
            pages(["Pat Lee,1,no", "Pat Lee,2,no"]),
            "13 Oct 2026 | Dana | Pat Lee | Homework wasn't set.\n"
            "20 Oct 2026 | Dana | Pat Lee | Homework wasn't set.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_moving_this_week_excuses_both_absences(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,text,absent,absent,8,9"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Moving this week, told us ahead.\n"
            "20 Oct 2026 | Dana | Pat Lee | Still moving this week.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_ran_long_excuses_only_that_diary_week(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,no", "Pat Lee,2,no"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary was set.\n"
            "20 Oct 2026 | Dana | Pat Lee | Session ran long.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_household_does_not_excuse_two_diary_misses(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,8"]),
            pages(["Pat Lee,1,no", "Pat Lee,2,no"]),
            "13 Oct 2026 | Dana | Pat Lee | Reviewed the household budget.\n"
            "20 Oct 2026 | Dana | Pat Lee | Reviewed the household budget.\n",
        )
        self.assertEqual(report.clients[0].status, "stalled")

    def test_blank_diary_is_not_a_miss(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,", "Pat Lee,2,"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary set.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_lower_second_score_is_not_improved(self) -> None:
        report = run(
            sheet(
                [
                    "P1,Pat Lee,call,present,present,14,10",
                    "P2,Nia Singh,text,present,present,8,",
                    "P3,Rosa Silva,call,present,present,9,9",
                ]
            ),
            pages(["Pat Lee,1,yes", "Nia Singh,1,yes", "Rosa Silva,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary set.\n"
            "13 Oct 2026 | Dana | Nia Singh | Diary set.\n"
            "13 Oct 2026 | Dana | Rosa Silva | Diary set.\n",
        )
        self.assertEqual(report.completed_both, 2)
        self.assertEqual(report.improved, 0)
        summary = report.summary_path.read_text(encoding="utf-8")
        self.assertIn("Number of Clients Who Started: 3", summary)
        self.assertIn("This is a halfway view.", summary)
        self.assertNotIn("Pat Lee", summary)

    def test_shared_first_name_does_not_change_either_client(self) -> None:
        report = run(
            sheet(
                [
                    "P1,Sam Cole,paper,present,present,8,9",
                    "P2,Sam Reid,call,present,present,8,9",
                ]
            ),
            pages(["Sam Cole,1,yes", "Sam Reid,1,yes"]),
            "13 Oct 2026 | Dana | Sam | Do not reach out.\n",
        )
        by_id = {row.client_id: row.way_to_reach for row in report.clients}
        self.assertEqual(by_id, {"P1": "paper", "P2": "call"})
        self.assertTrue(report.warnings)

    def test_marie_t_matches_marie_tremblay(self) -> None:
        report = run(
            sheet(["P1,Marie Tremblay,call,present,present,8,11"]),
            pages(["Marie Tremblay,1,yes"]),
            "13 Oct 2026 | Dana | Marie T. | Text is fine.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_labelled_note_with_client_before_date(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "Client: Pat Lee Date: 13 Oct 2026 Note: Calls only.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_parenthesis_note_layout(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "Pat Lee (13 Oct 2026, Dana): Email is fine.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "paper")

    def test_third_of_november_date_orders_the_newer_note(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Text is fine.\n"
            "3rd November 2026 | Dana | Pat Lee | Do not contact.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_header_spaces_and_crlf_notes(self) -> None:
        attendance = (
            " Client ID , Client , Reach by , Mtg 1 , Mtg 2 , Check A , Check B \n"
            "P1,Pat Lee,call,present,present,8,10\n"
        )
        notes = "13 Oct 2026 | Dana | Pat Lee | Text is fine.\r\n"
        report = run(attendance, pages(["Pat Lee,1,yes"]), notes)
        self.assertEqual(report.clients[0].way_to_reach, "text")
        self.assertEqual(report.agency_name, "Edge")
        self.assertEqual(report.total_clients, 1)

    def test_a_few_unreadable_lines_do_not_stop_the_run(self) -> None:
        notes = "".join(
            f"13 Oct 2026 | Dana | Pat Lee | Diary set {index}.\n" for index in range(6)
        ) + "".join(f"garbage line {index}\n" for index in range(4))
        report = run(
            sheet(["P1,Pat Lee,call,present,present,8,10"]),
            pages(["Pat Lee,1,yes"]),
            notes,
        )
        self.assertEqual(report.total_clients, 1)
        self.assertTrue(report.results_path.exists())

    def test_most_unreadable_lines_write_nothing(self) -> None:
        notes = "".join(
            f"13 Oct 2026 | Dana | Pat Lee | Diary set {index}.\n" for index in range(4)
        ) + "".join(f"garbage line {index}\n" for index in range(6))
        folder = Path(tempfile.mkdtemp())
        (folder / "edge-attendance.csv").write_text(
            sheet(["P1,Pat Lee,call,present,present,8,10"]), encoding="utf-8"
        )
        (folder / "edge-diaries.csv").write_text(pages(["Pat Lee,1,yes"]), encoding="utf-8")
        (folder / "edge-notes.txt").write_text(notes, encoding="utf-8")
        with self.assertRaises(NotesUnreadableError):
            process_folder(folder, output_dir=folder / "out")
        self.assertFalse((folder / "out" / "results.csv").exists())
        self.assertFalse((folder / "out" / "summary.md").exists())

    def test_why_stays_a_few_words_and_columns_stay_fixed(self) -> None:
        report = run(
            sheet(["P1,Pat Lee,call,absent,absent,8,9"]),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary set.\n",
        )
        header = report.results_path.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(header, "client_id,status,way_to_reach,why")
        why = report.clients[0].why
        self.assertGreaterEqual(len(why.split()), 2)
        self.assertLessEqual(len(why.split()), 6)


if __name__ == "__main__":
    unittest.main()
