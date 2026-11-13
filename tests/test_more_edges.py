"""Fifty-four more edges. Each one is a result that can still come out wrong."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import InputDiscoveryError, process_folder


def run(
    attendance: str,
    diaries: str,
    notes: str,
    stem: str = "edge",
    attendance_name: str | None = None,
) -> object:
    folder = Path(tempfile.mkdtemp())
    (folder / (attendance_name or f"{stem}-attendance.csv")).write_text(attendance, encoding="utf-8")
    (folder / f"{stem}-diaries.csv").write_text(diaries, encoding="utf-8")
    (folder / f"{stem}-notes.txt").write_text(notes, encoding="utf-8")
    return process_folder(folder, output_dir=folder / "out")


def sheet(rows: list[str], header: str | None = None) -> str:
    header = header or "Client ID,Client,Reach by,Mtg 1,Mtg 2,Check A,Check B"
    return header + "\n" + "\n".join(rows) + "\n"


def pages(rows: list[str]) -> str:
    return "Client,Week,Handed in\n" + "\n".join(rows) + "\n"


def one(contact: str, sessions: str = "present,present", scores: str = "8,10") -> str:
    return sheet([f"P1,Pat Lee,{contact},{sessions},{scores}"])


def noted(body: str, when: str = "13 Oct 2026") -> str:
    return f"{when} | Dana | Pat Lee | {body}\n"


class MoreEdgeTests(unittest.TestCase):
    def test_mail_is_preferred_means_paper(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("Mail is preferred."))
        self.assertEqual(report.clients[0].way_to_reach, "paper")

    def test_phones_only_means_call(self) -> None:
        report = run(one("text"), pages(["Pat Lee,1,yes"]), noted("Phones only."))
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_sms_is_fine_means_text(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("SMS is fine."))
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_imessage_is_okay_means_text(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("iMessage is okay."))
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_letter_is_preferred_means_paper(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("Letter is preferred."))
        self.assertEqual(report.clients[0].way_to_reach, "paper")

    def test_text_preferred_without_is_means_text(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("Text preferred."))
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_hyphenated_do_not_contact(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("Do-not-contact."))
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_apostrophe_dont_contact(self) -> None:
        report = run(one("text"), pages(["Pat Lee,1,yes"]), noted("Don't contact."))
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_asked_not_to_be_contacted(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("She asked not to be contacted."))
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_no_phone_no_text_no_post_is_do_not_contact(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,yes"]),
            noted("No phone, no text, and no post."),
        )
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_do_not_phone_alone_is_not_a_full_ban(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("Do not phone him about the bill."))
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_please_call_means_call(self) -> None:
        report = run(one("text"), pages(["Pat Lee,1,yes"]), noted("Please call."))
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_texting_is_okay_means_text(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("Texting is okay."))
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_late_counts_as_present(self) -> None:
        report = run(one("call", "late,late"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].status, "on track")

    def test_showed_up_counts_as_present(self) -> None:
        report = run(one("call", "showed up,showed up"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].status, "on track")

    def test_two_no_shows_stall(self) -> None:
        report = run(one("call", "no show,no show"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].status, "stalled")
        self.assertEqual(report.clients[0].why, "Missed sessions 1 and 2")

    def test_returned_diary_is_not_a_miss(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,Returned", "Pat Lee,2,Returned"]), noted("Diary set."))
        self.assertEqual(report.clients[0].status, "on track")

    def test_y_and_n_diary_values(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,N", "Pat Lee,2,N"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary set.\n20 Oct 2026 | Dana | Pat Lee | Diary set.\n",
        )
        self.assertEqual(report.clients[0].status, "stalled")
        self.assertEqual(report.clients[0].why, "Missed two diaries")

    def test_accented_attendance_name_matches_plain_note(self) -> None:
        report = run(
            sheet(["P1,Josée Landry,call,present,present,8,10"]),
            pages(["Josée Landry,1,yes"]),
            "13 Oct 2026 | Dana | Josee Landry | Text is fine.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_hyphenated_name_matches_spaced_note(self) -> None:
        report = run(
            sheet(["P1,Jean-Luc Bergeron,call,present,present,8,10"]),
            pages(["Jean-Luc Bergeron,1,yes"]),
            "13 Oct 2026 | Dana | Jean Luc Bergeron | Text is fine.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_unique_last_name_matches(self) -> None:
        report = run(
            sheet(["P1,Jean-Luc Bergeron,call,present,present,8,10"]),
            pages(["Jean-Luc Bergeron,1,yes"]),
            "13 Oct 2026 | Dana | Bergeron | Text is fine.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_shared_last_name_does_not_guess(self) -> None:
        report = run(
            sheet(["P1,Sam Cole,paper,present,present,8,9", "P2,Darnell Cole,call,present,present,8,9"]),
            pages(["Sam Cole,1,yes", "Darnell Cole,1,yes"]),
            "13 Oct 2026 | Dana | Cole | Text is fine.\n",
        )
        by_id = {row.client_id: row.way_to_reach for row in report.clients}
        self.assertEqual(by_id, {"P1": "paper", "P2": "call"})

    def test_hyphenated_case_number_matches_compact_note(self) -> None:
        report = run(
            sheet(["C-10,Nia Singh,text,present,present,8,8"]),
            pages(["Nia Singh,1,yes"]),
            "13 Oct 2026 | Dana | C10 | Do not contact.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_empty_contact_falls_back_to_paper(self) -> None:
        report = run(one(""), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].way_to_reach, "paper")

    def test_attendance_none_is_do_not_contact(self) -> None:
        report = run(one("none"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_attendance_mobile_is_text(self) -> None:
        report = run(one("mobile"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_attendance_telephone_is_call(self) -> None:
        report = run(one("telephone"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_attendance_post_is_paper(self) -> None:
        report = run(one("post"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].way_to_reach, "paper")

    def test_unknown_contact_word_is_paper(self) -> None:
        report = run(one("pigeon"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].way_to_reach, "paper")

    def test_fraction_scores_count_as_improved(self) -> None:
        report = run(one("call", scores="8/25,14/25"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual((report.completed_both, report.improved), (1, 1))

    def test_score_out_of_uses_the_earned_number(self) -> None:
        report = run(
            one("call", scores="12 out of 25,16 out of 25"),
            pages(["Pat Lee,1,yes"]),
            noted("Diary set."),
        )
        self.assertEqual(report.improved, 1)

    def test_blank_first_score_is_not_completed(self) -> None:
        report = run(one("call", scores=",10"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.completed_both, 0)

    def test_equal_scores_are_not_improved(self) -> None:
        report = run(one("call", scores="9,9"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual((report.completed_both, report.improved), (1, 0))

    def test_na_score_is_not_completed(self) -> None:
        report = run(one("call", scores="n/a,10"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.completed_both, 0)

    def test_iso_date_makes_the_later_note_win(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,yes"]),
            "2026-10-13 | Dana | Pat Lee | Text is fine.\n2026-11-03 | Dana | Pat Lee | Do not contact.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_nov_3_2026_is_read(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Text is fine.\nNov 3 2026 | Dana | Pat Lee | Do not contact.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_ordinal_day_is_read(self) -> None:
        report = run(
            one("text"),
            pages(["Pat Lee,1,yes"]),
            "21st October 2026 | Dana | Pat Lee | Please call.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_counsellor_initial_still_matches_the_client(self) -> None:
        header = "Client ID,Client,Staff,Reach by,Mtg 1,Mtg 2,Check A,Check B"
        report = run(
            sheet(["P1,Pat Lee,Dana,call,present,present,8,10"], header),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | D. | Pat Lee | Text is fine.\n",
        )
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_on_hold_does_not_excuse_the_earlier_miss(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,no", "Pat Lee,2,no"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary was set.\n20 Oct 2026 | Dana | Pat Lee | Diary on hold.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")
        self.assertNotEqual(report.clients[0].why, "Missed two diaries")

    def test_hw_not_set_excuses_the_diaries(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,no", "Pat Lee,2,no"]),
            "13 Oct 2026 | Dana | Pat Lee | HW not set.\n20 Oct 2026 | Dana | Pat Lee | HW not set.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_did_not_give_the_diary_excuses_it(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,no", "Pat Lee,2,no"]),
            "13 Oct 2026 | Dana | Pat Lee | Did not give the diary.\n"
            "20 Oct 2026 | Dana | Pat Lee | Did not give the diary.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_session_went_long_excuses_the_diary(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,no", "Pat Lee,2,no"]),
            "13 Oct 2026 | Dana | Pat Lee | Session went long.\n"
            "20 Oct 2026 | Dana | Pat Lee | Session went long.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_away_for_work_excuses_two_absences(self) -> None:
        report = run(
            one("call", "absent,absent"),
            pages(["Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Away for work, told us ahead.\n"
            "20 Oct 2026 | Dana | Pat Lee | Still away for work.\n",
        )
        self.assertEqual(report.clients[0].status, "on track")

    def test_bom_does_not_hide_the_header(self) -> None:
        report = run(
            "\ufeff" + one("call"),
            pages(["Pat Lee,1,yes"]),
            noted("Text is fine."),
        )
        self.assertEqual(report.clients[0].way_to_reach, "text")

    def test_session_columns_follow_their_numbers(self) -> None:
        header = "Client ID,Client,Reach by,Session 4,Session 1,Session 3,Session 2,Check A,Check B"
        report = run(
            sheet(["P1,Pat Lee,call,absent,present,absent,present,8,10"], header),
            pages(["Pat Lee,1,yes"]),
            noted("Diary set."),
        )
        self.assertEqual(report.clients[0].why, "Missed sessions 3 and 4")

    def test_check_columns_follow_letter_order(self) -> None:
        header = "Client ID,Client,Reach by,Mtg 1,Mtg 2,Check B,Check A"
        report = run(
            sheet(["P1,Pat Lee,call,present,present,15,10"], header),
            pages(["Pat Lee,1,yes"]),
            noted("Diary set."),
        )
        self.assertEqual(report.improved, 1)

    def test_no_diary_rows_stays_on_track(self) -> None:
        report = run(one("call"), pages(["Someone Else,1,no"]), noted("Diary set."))
        self.assertEqual(report.clients[0].status, "on track")

    def test_blank_sessions_are_not_absences(self) -> None:
        report = run(one("call", ","), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.clients[0].status, "on track")

    def test_client_ids_stay_in_attendance_order(self) -> None:
        report = run(
            sheet(["B2,Nia Singh,text,present,present,8,8", "B1,Pat Lee,call,present,present,8,9"]),
            pages(["Nia Singh,1,yes", "Pat Lee,1,yes"]),
            "13 Oct 2026 | Dana | Pat Lee | Diary set.\n13 Oct 2026 | Dana | Nia Singh | Diary set.\n",
        )
        self.assertEqual([row.client_id for row in report.clients], ["B2", "B1"])

    def test_client_id_is_kept_exactly(self) -> None:
        report = run(
            sheet(["C-1100,Pat Lee,call,present,present,8,9"]),
            pages(["Pat Lee,1,yes"]),
            noted("Diary set."),
        )
        self.assertEqual(report.clients[0].client_id, "C-1100")

    def test_blank_line_blocks_are_one_note_each(self) -> None:
        notes = (
            "13 Oct 2026\nDana | Pat Lee\nText is fine.\n\n"
            "20 Oct 2026\nDana | Pat Lee\nDo not contact.\n"
        )
        report = run(one("call"), pages(["Pat Lee,1,yes"]), notes)
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")

    def test_summary_states_the_improved_definition(self) -> None:
        report = run(one("call"), pages(["Pat Lee,1,yes"]), noted("Diary set."))
        summary = report.summary_path.read_text(encoding="utf-8")
        self.assertIn(
            'Definition of Improved: "A client who completed both Money Checks and increased their score from the first to the second."',
            summary,
        )
        self.assertIn('Note: "This is a halfway view. Final scores are not yet available."', summary)
        self.assertNotIn("Pat Lee", summary)

    def test_roster_word_is_left_out_of_the_agency_name(self) -> None:
        report = run(
            one("call"),
            pages(["Pat Lee,1,yes"]),
            noted("Diary set."),
            attendance_name="pine-roster.csv",
        )
        self.assertEqual(report.agency_name, "Pine")
        self.assertEqual(report.total_clients, 1)

    def test_duplicate_client_id_writes_nothing(self) -> None:
        folder = Path(tempfile.mkdtemp())
        (folder / "edge-attendance.csv").write_text(
            sheet(["P1,Pat Lee,call,present,present,8,9", "P1,Nia Singh,text,present,present,8,9"]),
            encoding="utf-8",
        )
        (folder / "edge-diaries.csv").write_text(pages(["Pat Lee,1,yes"]), encoding="utf-8")
        (folder / "edge-notes.txt").write_text(noted("Diary set."), encoding="utf-8")
        with self.assertRaises(InputDiscoveryError):
            process_folder(folder, output_dir=folder / "out")
        self.assertFalse((folder / "out" / "results.csv").exists())
        self.assertFalse((folder / "out" / "summary.md").exists())


if __name__ == "__main__":
    unittest.main()
