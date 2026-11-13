"""Four hundred generated cases. Each one is a different way to write the same rules."""

from __future__ import annotations

import unittest

from tests.test_more_edges import noted, one, pages, run, sheet


PHRASES = [
    ("do not contact", "call", "Do not contact"),
    ("do not contact", "call", "Don't contact"),
    ("do not contact", "call", "Do-not-contact"),
    ("do not contact", "call", "Do not reach out"),
    ("do not contact", "call", "Asked us not to reach out"),
    ("do not contact", "call", "She asked not to be contacted"),
    ("do not contact", "call", "No calls, no texts, no mail"),
    ("do not contact", "call", "No texts, no calls, no mail"),
    ("do not contact", "call", "No phone calls, no text messages, and no letters"),
    ("do not contact", "call", "No phone, no text, and no post"),
    ("do not contact", "call", "Do not phone, do not text, and do not send mail"),
    ("text", "call", "Text is fine"),
    ("text", "call", "Texts are okay"),
    ("text", "call", "Text preferred"),
    ("text", "call", "Text only"),
    ("text", "call", "Texting is okay"),
    ("text", "call", "SMS is fine"),
    ("text", "call", "WhatsApp is fine"),
    ("text", "call", "iMessage is okay"),
    ("call", "text", "Call is fine"),
    ("call", "text", "Calls only"),
    ("call", "text", "Phones only"),
    ("call", "text", "Please call"),
    ("call", "text", "No texts, call evenings"),
    ("call", "text", "Call evenings"),
    ("paper", "call", "Letter only"),
    ("paper", "call", "Letter is preferred"),
    ("paper", "call", "Mail is preferred"),
    ("paper", "call", "Post only"),
    ("paper", "call", "Email is fine"),
    ("paper", "call", "Paper is preferred"),
]

DATES = [
    ("13 Oct 2026", "20 Oct 2026"),
    ("2026-10-13", "2026-10-20"),
    ("13-Oct-2026", "20-Oct-2026"),
    ("October 13th, 2026", "October 20th, 2026"),
]


def layouts(older: str, newer: str, body: str) -> list[tuple[str, str]]:
    return [
        ("pipe", f"{older} | Dana | Pat Lee | Diary set.\n{newer} | Dana | Pat Lee | {body}.\n"),
        ("paren", f"Pat Lee ({older}, Dana): Diary set.\nPat Lee ({newer}, Dana): {body}.\n"),
        (
            "labelled",
            f"Date: {older} Client: Pat Lee Note: Diary set.\n"
            f"Date: {newer} Client: Pat Lee Note: {body}.\n",
        ),
    ]


def both_days(excuse: str) -> str:
    return (
        f"13 Oct 2026 | Dana | Pat Lee | {excuse}\n"
        f"20 Oct 2026 | Dana | Pat Lee | {excuse}\n"
    )


STATUS_CASES = [
    ("present", one("call"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "on track", "call"),
    ("one_absence", one("call", "absent,present"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "on track", "call"),
    ("two_absences", one("call", "absent,absent"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "stalled", "call"),
    ("dotted_absences", one("call", "A.,A."), pages(["Pat Lee,1,yes"]), noted("Diary set."), "stalled", "call"),
    ("no_shows", one("call", "no show,no show"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "stalled", "call"),
    ("ns", one("call", "NS,NS"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "stalled", "call"),
    ("missed", one("call", "missed,missed"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "stalled", "call"),
    ("did_not_attend", one("call", "did not attend,did not attend"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "stalled", "call"),
    ("late", one("call", "late,late"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "on track", "call"),
    ("showed_up", one("call", "showed up,showed up"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "on track", "call"),
    ("letter_p", one("call", "P,P"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "on track", "call"),
    ("here", one("call", "here,here"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "on track", "call"),
    ("one_diary", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,yes"]), both_days("Diary set."), "on track", "call"),
    ("two_diaries", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("Diary set."), "stalled", "call"),
    ("diary_n", one("call"), pages(["Pat Lee,1,N", "Pat Lee,2,N"]), both_days("Diary set."), "stalled", "call"),
    ("not_returned", one("call"), pages(["Pat Lee,1,not returned", "Pat Lee,2,not returned"]), both_days("Diary set."), "stalled", "call"),
    ("wasnt_handed", one("call"), pages(["Pat Lee,1,wasn't handed in", "Pat Lee,2,wasn't handed in"]), both_days("Diary set."), "stalled", "call"),
    ("returned", one("call"), pages(["Pat Lee,1,Returned", "Pat Lee,2,Returned"]), noted("Diary set."), "on track", "call"),
    ("hw_not_set", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("HW not set."), "on track", "call"),
    ("wasnt_set", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("Homework wasn't set."), "on track", "call"),
    ("didnt_set", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("I didn't set the diary."), "on track", "call"),
    ("on_hold", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("Diary on hold."), "on track", "call"),
    ("ran_long", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("Session ran long."), "on track", "call"),
    ("went_long", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("Session went long."), "on track", "call"),
    ("not_given", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("Did not give the diary."), "on track", "call"),
    ("household", one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), both_days("Reviewed the household budget."), "stalled", "call"),
    ("mixed_miss", one("call", "absent,present"), pages(["Pat Lee,1,no", "Pat Lee,2,yes"]), both_days("Diary set."), "on track", "call"),
    ("away", one("call", "absent,absent"), pages(["Pat Lee,1,yes"]), both_days("Away for work, told us ahead."), "on track", "call"),
]


class MatrixTests(unittest.TestCase):
    pass


def _contact_test(attendance_contact: str, notes: str, expected: str):
    def test(self) -> None:
        report = run(one(attendance_contact), pages(["Pat Lee,1,yes"]), notes)
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, expected)
        if expected == "do not contact":
            self.assertNotIn(report.clients[0].way_to_reach, {"call", "text", "paper"})

    return test


def _status_test(attendance: str, diaries: str, notes: str, status: str, contact: str):
    def test(self) -> None:
        report = run(attendance, diaries, notes)
        self.assertEqual(report.clients[0].status, status)
        self.assertEqual(report.clients[0].way_to_reach, contact)

    return test


_index = 0
for expected, attendance_contact, phrase in PHRASES:
    for older, newer in DATES:
        for layout_name, notes in layouts(older, newer, phrase):
            name = f"test_m{_index:03d}_{layout_name}"
            setattr(
                MatrixTests,
                name,
                _contact_test(attendance_contact, notes, expected),
            )
            _index += 1

for case_name, attendance, diaries, notes, status, contact in STATUS_CASES:
    setattr(
        MatrixTests,
        f"test_m{_index:03d}_{case_name}",
        _status_test(attendance, diaries, notes, status, contact),
    )
    _index += 1


if __name__ == "__main__":
    unittest.main()
