"""Five hundred cases against Friday's scoring rules.

A client is right only when status and way_to_reach both match. Suggesting
call, text, or paper for someone who asked not to be contacted fails the run.
Notes that cannot be read must stop the run before any results file is written.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import NotesUnreadableError, process_folder
from tests.test_more_edges import noted, one, pages, run, sheet


PHRASES = [
    ("do not contact", "call", "No calls, no texts, and no emails"),
    ("do not contact", "text", "No emails, no calls, and no texts"),
    ("do not contact", "paper", "Don't call, don't text, and don't email"),
    ("do not contact", "call", "Don't reach out"),
    ("do not contact", "text", "No further outreach"),
    ("do not contact", "call", "Please don't contact her"),
    ("do not contact", "paper", "Asked not to be reached"),
    ("do not contact", "call", "Do not reach her"),
    ("call", "text", "Prefers a call"),
    ("text", "call", "Prefers a text"),
    ("paper", "call", "Prefers email"),
    ("text", "call", "She used to say do not contact. Text is fine now"),
]

DATES = [
    ("13th of October 2026", "20th of October 2026"),
    ("6th of November 2026", "13th of November 2026"),
    ("13 Oct 2026", "20 Oct 2026"),
    ("2026-10-13", "2026-10-20"),
]

SAME_NOTE = [
    ("Do not contact", "Text is fine", "text", "call"),
    ("Text is fine", "Do not contact", "do not contact", "text"),
    ("Please call", "No calls, no texts, and no emails", "do not contact", "call"),
    ("Prefers email", "Don't reach out", "do not contact", "paper"),
    ("Do not contact", "Prefers a call", "call", "text"),
    ("Call is fine", "Prefers email", "paper", "call"),
    ("No further outreach", "Please text", "text", "paper"),
    ("Prefers a text", "Please don't contact her", "do not contact", "text"),
]

PEOPLE = [
    ("Maeve O'Brien", "O'Brien"),
    ("Maeve O'Brien", "M. O'Brien"),
    ("Luca D'Angelo", "D'Angelo"),
    ("Pat Lee", "Pat Lee Jr"),
    ("Jean-Luc Martin", "Jean Luc Martin"),
    ("Anne-Marie Roy", "A. Roy"),
]

NAME_PHRASES = [
    ("do not contact", "call", "Don't reach out"),
    ("text", "call", "Prefers a text"),
    ("call", "text", "Prefers a call"),
    ("paper", "call", "Prefers email"),
    ("do not contact", "paper", "No calls, no texts, and no emails"),
    ("text", "paper", "Please text"),
]

PARTIALS = [
    "No emails this week",
    "Don't email the bill",
    "Phone bill was high",
    "She prefers the morning",
    "No texts",
    "Household emergency",
    "Seen in Halifax",
    "Do not phone him about the bill",
]

CHANNELS = [
    ("call", "call"),
    ("phone", "call"),
    ("telephone", "call"),
    ("text", "text"),
    ("sms", "text"),
    ("whatsapp", "text"),
    ("mobile", "text"),
    ("message", "text"),
    ("imessage", "text"),
    ("paper", "paper"),
    ("letter", "paper"),
    ("mail", "paper"),
    ("post", "paper"),
    ("email", "paper"),
    ("none", "do not contact"),
    ("no contact", "do not contact"),
    ("", "paper"),
    ("pigeon", "paper"),
]

CITIES = ["Halifax", "Ottawa", "Moncton", "Toronto"]

FORGOT = [
    "forgot",
    "forgot it",
    "did not bring",
    "didn't bring it",
    "left it at home",
    "not brought in",
]

SCORES = [
    ("8", "14", 1, 1),
    ("10", "10", 1, 0),
    ("18", "12", 1, 0),
    ("n/a", "14", 0, 0),
    ("", "12", 0, 0),
    ("9", "9.5", 1, 1),
    ("12 out of 25", "16 out of 25", 1, 1),
    ("8/25", "8/25", 1, 0),
    ("20", "19", 1, 0),
    ("7 of 25", "11 of 25", 1, 1),
]

AGENCIES = [
    ("harbour-friday-attendance.csv", "Harbour Friday"),
    ("st-john-register.csv", "St John"),
    ("tidewater-roster.csv", "Tidewater"),
    ("puffin-sheet.csv", "Puffin"),
    ("bedford-attendance.csv", "Bedford"),
    ("north-gate-register.csv", "North Gate"),
    ("kettle-sheet.csv", "Kettle"),
    ("moncton-roster.csv", "Moncton"),
    ("halifax-attendance.csv", "Halifax"),
    ("cedar-row-register.csv", "Cedar Row"),
]

DEFINITION = (
    'Definition of Improved: "A client who completed both Money Checks and '
    'increased their score from the first to the second."'
)
HALFWAY = 'Note: "This is a halfway view. Final scores are not yet available."'

FIFTEEN = [
    ("F1", "Nora Quinn", "call", "present", "present", "8", "14", "yes", "yes", "Prefers a call", "on track", "call"),
    ("F2", "Omar Haddad", "call", "missed", "missed", "8", "9", "yes", "yes", "Diary set", "stalled", "call"),
    ("F3", "Imani Cole", "text", "present", "present", "10", "10", "yes", "yes", "Prefers a text", "on track", "text"),
    ("F4", "Jules Perrin", "paper", "present", "present", "5", "9", "yes", "yes", "Prefers email", "on track", "paper"),
    ("F5", "Nia Roy", "call", "present", "present", "8", "12", "forgot", "forgot", "Don't reach out", "stalled", "do not contact"),
    ("F6", "Wes Adler", "call", "present", "present", "11", "15", "yes", "yes", "No calls, no texts, and no emails", "on track", "do not contact"),
    ("F7", "Ada Brooks", "call", "absent", "present", "8", "13", "no", "yes", "Diary set", "on track", "call"),
    ("F8", "Beau Martin", "text", "present", "present", "7", "8", "yes", "yes", "She used to say do not contact. Text is fine now", "on track", "text"),
    ("F9", "Cleo Marsh", "call", "present", "present", "n/a", "10", "yes", "yes", "Diary set", "on track", "call"),
    ("F10", "Drew Patel", "call", "present", "present", "9", "9", "yes", "yes", "Call is fine", "on track", "call"),
    ("F11", "Maeve O'Brien", "call", "present", "present", "8", "16", "yes", "yes", "Please text", "on track", "text"),
    ("F12", "Pat Lee", "call", "present", "present", "4", "8", "yes", "yes", "Prefers a call", "on track", "call"),
    ("F13", "Front Desk Trial", "call", "present", "present", "1", "2", "yes", "yes", "Don't reach out", "on track", "do not contact"),
    ("F14", "Lynn Savoie", "call", "present", "present", "8", "10", "yes", "yes", "Prefers a text", "on track", "text"),
    ("F15", "Lynn Smith", "paper", "present", "present", "6", "6", "yes", "yes", "Diary set", "on track", "paper"),
]


def phrase_layouts(older: str, newer: str, phrase: str) -> list[tuple[str, str]]:
    body = f"{phrase}."
    return [
        (
            "dash",
            f"Pat Lee - {older} - Dana - Diary set.\nPat Lee - {newer} - Dana - {body}\n",
        ),
        (
            "pipe",
            f"{older} | Dana | Pat Lee | Diary set.\n{newer} | Dana | Pat Lee | {body}\n",
        ),
        (
            "labelled",
            f"Date: {older} Name: Pat Lee Note: Diary set.\n"
            f"Date: {newer} Name: Pat Lee Note: {body}\n",
        ),
    ]


def same_note(when: str, earlier: str, later: str, layout: str) -> str:
    body = f"{earlier}. {later}."
    if layout == "dash":
        return f"Pat Lee - {when} - Dana - {body}\n"
    return f"{when} | Dana | Pat Lee | {body}\n"


class FridayRuleTests(unittest.TestCase):
    def test_utf16_notes_are_read(self) -> None:
        folder = Path(tempfile.mkdtemp())
        (folder / "harbour-attendance.csv").write_text(one("text"), encoding="utf-8")
        (folder / "harbour-diaries.csv").write_text(pages(["Pat Lee,1,yes"]), encoding="utf-8")
        (folder / "harbour-notes.txt").write_text(
            "13th of October 2026 | Dana | Pat Lee | Prefers a call.\n",
            encoding="utf-16",
        )
        report = process_folder(folder, output_dir=folder / "out")
        self.assertEqual(report.agency_name, "Harbour")
        self.assertEqual(report.clients[0].way_to_reach, "call")
        self.assertEqual(report.clients[0].status, "on track")

    def test_two_title_rows_are_skipped(self) -> None:
        attendance = (
            "Harbour roll\n"
            "Exported 12 November 2026\n"
            "Client ID,Learner,Reach by,Week 1,Week 2,Money Check One,Money Check Two\n"
            "P1,Pat Lee,text,present,present,8,14\n"
        )
        report = run(attendance, pages(["Pat Lee,1,yes"]), noted("Prefers a call."))
        self.assertEqual(report.clients[0].client_id, "P1")
        self.assertEqual(report.clients[0].way_to_reach, "call")
        self.assertEqual(report.completed_both, 1)
        self.assertEqual(report.improved, 1)

    def test_money_checks_follow_their_numbers_when_the_columns_are_reversed(self) -> None:
        attendance = (
            "Client ID,Learner,Reach by,Week 1,Week 2,Money Check Two,Money Check One\n"
            "P1,Pat Lee,call,present,present,15,10\n"
        )
        report = run(attendance, pages(["Pat Lee,1,yes"]), noted("Diary set."))
        self.assertEqual(report.completed_both, 1)
        self.assertEqual(report.improved, 1)
        self.assertEqual(report.clients[0].status, "on track")

    def test_week_columns_count_two_absences(self) -> None:
        attendance = (
            "Client ID,Learner,Reach by,Week 1,Week 2,Money Check One,Money Check Two\n"
            "P1,Pat Lee,call,missed,missed,8,9\n"
        )
        report = run(attendance, pages(["Pat Lee,1,yes"]), noted("Seen in Halifax. Diary set."))
        self.assertEqual(report.clients[0].status, "stalled")
        self.assertEqual(report.clients[0].way_to_reach, "call")
        self.assertEqual(report.clients[0].why, "Missed sessions 1 and 2")


def _contact(attendance_contact: str, notes: str, expected: str):
    def test(self) -> None:
        report = run(one(attendance_contact), pages(["Pat Lee,1,yes"]), notes)
        client = report.clients[0]
        self.assertEqual(client.status, "on track")
        self.assertEqual(client.way_to_reach, expected)
        self.assertGreaterEqual(len(client.why.split()), 2)
        self.assertLessEqual(len(client.why.split()), 8)

    return test


def _named(attendance_name: str, spoken: str, contact: str, notes: str, expected: str):
    def test(self) -> None:
        attendance = sheet([f"P1,{attendance_name},{contact},present,present,8,12"])
        report = run(attendance, pages([f"{attendance_name},1,yes"]), notes)
        self.assertEqual(report.total_clients, 1)
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, expected)

    return test


def _forgot(value: str, older: str, newer: str):
    def test(self) -> None:
        notes = (
            f"{older} | Dana | Pat Lee | Diary set.\n"
            f"{newer} | Dana | Pat Lee | Seen in Halifax.\n"
        )
        report = run(one("call"), pages([f"Pat Lee,1,{value}", f"Pat Lee,2,{value}"]), notes)
        self.assertEqual(report.clients[0].status, "stalled")
        self.assertEqual(report.clients[0].way_to_reach, "call")

    return test


def _forgot_excused(older: str, newer: str):
    def test(self) -> None:
        notes = (
            f"{older} | Dana | Pat Lee | I did not set the diary.\n"
            f"{newer} | Dana | Pat Lee | Not typed yet.\n"
        )
        report = run(one("call"), pages(["Pat Lee,1,forgot", "Pat Lee,2,forgot"]), notes)
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, "call")

    return test


def _channel(city: str, raw: str, expected: str):
    def test(self) -> None:
        notes = f"Pat Lee - 13th of October 2026 - Dana - Seen in {city}. Diary set.\n"
        report = run(one(raw), pages(["Pat Lee,1,yes"]), notes)
        self.assertEqual(report.clients[0].way_to_reach, expected)
        self.assertEqual(report.clients[0].status, "on track")

    return test


def _score(first: str, second: str, completed: int, improved: int):
    def test(self) -> None:
        attendance = sheet([f"P1,Pat Lee,call,present,present,{first},{second}"])
        report = run(attendance, pages(["Pat Lee,1,yes"]), noted("Seen in Ottawa. Diary set."))
        self.assertEqual(report.completed_both, completed)
        self.assertEqual(report.improved, improved)
        summary = report.summary_path.read_text(encoding="utf-8")
        self.assertIn(DEFINITION, summary)
        self.assertIn(HALFWAY, summary)
        self.assertNotIn("Pat", summary)

    return test


def _agency(filename: str, expected_name: str):
    def test(self) -> None:
        report = run(
            one("text"),
            pages(["Pat Lee,1,yes"]),
            noted("Prefers a call. Seen in Halifax."),
            attendance_name=filename,
        )
        self.assertEqual(report.agency_name, expected_name)
        self.assertEqual(report.total_clients, 1)
        self.assertEqual(report.clients[0].way_to_reach, "call")
        summary = report.summary_path.read_text(encoding="utf-8")
        self.assertIn(f"Number of Clients Who Started: {report.total_clients}", summary)
        self.assertIn(DEFINITION, summary)
        self.assertIn(HALFWAY, summary)
        self.assertNotIn("Pat", summary)
        self.assertTrue(report.results_path.read_text(encoding="utf-8").startswith(
            "client_id,status,way_to_reach,why\n"
        ))

    return test


def _fifteen(layout: str):
    def test(self) -> None:
        header = "Client ID,Learner,Reach by,Week 1,Week 2,Money Check One,Money Check Two"
        rows = []
        diary_rows = []
        note_lines = ["Lynn - 13th of October 2026 - Dana - Don't reach out.\n"]
        for item in FIFTEEN:
            client_id, name, contact, first, second, score_a, score_b, diary_a, diary_b, phrase, _status, _reach = item
            rows.append(",".join([client_id, name, contact, first, second, score_a, score_b]))
            diary_rows.extend([f"{name},1,{diary_a}", f"{name},2,{diary_b}"])
            spoken = "O'Brien" if name == "Maeve O'Brien" else "Pat Lee Jr" if name == "Pat Lee" else name
            body = f"{phrase}."
            if layout == "dash":
                note_lines.append(f"{spoken} - 20th of October 2026 - Dana - {body}\n")
            else:
                note_lines.append(f"20th of October 2026 | Dana | {spoken} | {body}\n")
        attendance = header + "\n" + "\n".join(rows) + "\n"
        if layout == "semi":
            attendance = attendance.replace(",", ";")
        report = run(
            attendance,
            pages(diary_rows),
            "".join(note_lines),
            attendance_name="harbour-friday-attendance.csv",
        )
        self.assertEqual(report.agency_name, "Harbour Friday")
        self.assertEqual(report.total_clients, 15)
        by_id = {client.client_id: client for client in report.clients}
        unsafe = []
        for item in FIFTEEN:
            client_id, _name, _contact, *_rest, status, reach = item
            # tuple unpack: last two are status, reach; phrase is index 9
            status = item[10]
            reach = item[11]
            got = by_id[client_id]
            if (got.status, got.way_to_reach) != (status, reach):
                unsafe.append((client_id, got.status, got.way_to_reach, status, reach))
            if reach == "do not contact":
                self.assertEqual(got.way_to_reach, "do not contact")
            self.assertGreaterEqual(len(got.why.split()), 2)
        self.assertEqual(unsafe, [])
        summary = report.summary_path.read_text(encoding="utf-8")
        self.assertIn("Number of Clients Who Started: 15", summary)
        self.assertIn(DEFINITION, summary)
        self.assertIn(HALFWAY, summary)
        for item in FIFTEEN:
            self.assertNotIn(item[1], summary)
        self.assertNotIn("O'Brien", summary)
        self.assertNotIn("Trial", summary)

    return test


def _halt(good: int, bad: int, expect_halt: bool):
    def test(self) -> None:
        folder = Path(tempfile.mkdtemp())
        (folder / "edge-attendance.csv").write_text(one("call"), encoding="utf-8")
        (folder / "edge-diaries.csv").write_text(pages(["Pat Lee,1,yes"]), encoding="utf-8")
        lines = [
            f"13 Oct 2026 | Dana | Pat Lee | Diary set {index}.\n" for index in range(good)
        ]
        lines.extend(f"this line has no date or client {index}\n" for index in range(bad))
        (folder / "edge-notes.txt").write_text("".join(lines), encoding="utf-8")
        if expect_halt:
            with self.assertRaises(NotesUnreadableError):
                process_folder(folder, output_dir=folder / "out")
            self.assertFalse((folder / "out" / "results.csv").exists())
            self.assertFalse((folder / "out" / "summary.md").exists())
        else:
            report = process_folder(folder, output_dir=folder / "out")
            self.assertEqual(report.clients[0].client_id, "P1")
            self.assertTrue(report.results_path.exists())

    return test


_index = 0
for expected, attendance_contact, phrase in PHRASES:
    for older, newer in DATES:
        for layout_name, notes in phrase_layouts(older, newer, phrase):
            setattr(
                FridayRuleTests,
                f"test_f{_index:03d}_{layout_name}",
                _contact(attendance_contact, notes, expected),
            )
            _index += 1

for earlier, later, expected, fallback in SAME_NOTE:
    for _older, newer in DATES:
        for layout_name in ("dash", "pipe"):
            setattr(
                FridayRuleTests,
                f"test_f{_index:03d}_{layout_name}",
                _contact(fallback, same_note(newer, earlier, later, layout_name), expected),
            )
            _index += 1

for attendance_name, spoken in PEOPLE:
    for expected, fallback, phrase in NAME_PHRASES:
        for layout_name in ("dash", "pipe"):
            when = "20th of October 2026"
            if layout_name == "dash":
                notes = f"{spoken} - {when} - Dana - {phrase}.\n"
            else:
                notes = f"{when} | Dana | {spoken} | {phrase}.\n"
            setattr(
                FridayRuleTests,
                f"test_f{_index:03d}_{layout_name}",
                _named(attendance_name, spoken, fallback, notes, expected),
            )
            _index += 1

for value in FORGOT:
    for older, newer in DATES:
        setattr(FridayRuleTests, f"test_f{_index:03d}_forgot", _forgot(value, older, newer))
        _index += 1

for older, newer in DATES:
    setattr(FridayRuleTests, f"test_f{_index:03d}_excuse", _forgot_excused(older, newer))
    _index += 1

for phrase in PARTIALS:
    for older, newer in DATES:
        for layout_name in ("dash", "pipe"):
            if layout_name == "dash":
                notes = (
                    f"Pat Lee - {older} - Dana - Diary set.\n"
                    f"Pat Lee - {newer} - Dana - {phrase}.\n"
                )
            else:
                notes = (
                    f"{older} | Dana | Pat Lee | Diary set.\n"
                    f"{newer} | Dana | Pat Lee | {phrase}.\n"
                )
            setattr(
                FridayRuleTests,
                f"test_f{_index:03d}_partial",
                _contact("call", notes, "call"),
            )
            _index += 1

for city in CITIES:
    for raw, expected in CHANNELS:
        setattr(FridayRuleTests, f"test_f{_index:03d}_channel", _channel(city, raw, expected))
        _index += 1

for first, second, completed, improved in SCORES:
    setattr(FridayRuleTests, f"test_f{_index:03d}_score", _score(first, second, completed, improved))
    _index += 1

for filename, agency in AGENCIES:
    setattr(FridayRuleTests, f"test_f{_index:03d}_agency", _agency(filename, agency))
    _index += 1

for good, bad, expect_halt in (
    (4, 6, True),
    (5, 5, False),
    (6, 6, False),
    (5, 7, True),
    (0, 4, True),
    (2, 6, True),
    (4, 4, False),
    (3, 8, True),
):
    setattr(
        FridayRuleTests,
        f"test_f{_index:03d}_halt",
        _halt(good, bad, expect_halt),
    )
    _index += 1

STATUS = [
    (one("call", "absent,present"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "on track", "call"),
    (one("call", "A.,A."), pages(["Pat Lee,1,yes"]), noted("Diary set."), "stalled", "call"),
    (one("call", "late,showed up"), pages(["Pat Lee,1,yes"]), noted("Diary set."), "on track", "call"),
    (one("call", "NS,NS"), pages(["Pat Lee,1,yes"]), noted("Seen in Halifax."), "stalled", "call"),
    (one("text", "present,present"), pages(["Pat Lee,1,", "Pat Lee,2,"]), noted("Diary set."), "on track", "text"),
    (one("call"), pages(["Pat Lee,1,no"]), noted("Diary set."), "on track", "call"),
    (one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), noted("Household emergency."), "stalled", "call"),
    (one("call"), pages(["Pat Lee,1,not typed yet", "Pat Lee,2,not typed yet"]), noted("Diary set."), "on track", "call"),
    (one("paper"), pages(["Pat Lee,1,yes"]), noted("Don't reach out."), "on track", "do not contact"),
    (one("call"), pages(["Pat Lee,1,yes"]), noted("No emails this week."), "on track", "call"),
    (
        "Client ID,Learner,Reach by,Week 1,Week 2,Money Check One,Money Check Two\nP1,Pat Lee,call,present,missed,8,10\n",
        pages(["Pat Lee,1,yes"]),
        noted("Diary set."),
        "on track",
        "call",
    ),
    (
        "Client ID,Learner,Reach by,Week 1,Week 2,Money Check One,Money Check Two\nP1,Pat Lee,text,missed,missed,4,4\n",
        pages(["Pat Lee,1,yes"]),
        noted("Prefers a text."),
        "stalled",
        "text",
    ),
    (one("call"), pages(["Pat Lee,1,forgot", "Pat Lee,2,yes"]), noted("Diary set."), "on track", "call"),
    (one("call"), pages(["Pat Lee,1,left it at home", "Pat Lee,2,left it at home"]), noted("Away for work."), "on track", "call"),
    (one("none"), pages(["Pat Lee,1,yes"]), noted("Diary set. Seen in Ottawa."), "on track", "do not contact"),
    (one("call"), pages(["Pat Lee,1,yes"]), noted("Text is fine. Do not contact."), "on track", "do not contact"),
    (one("text"), pages(["Pat Lee,1,yes"]), noted("Do not contact. Prefers a call."), "on track", "call"),
    (one("call", "missed,missed"), pages(["Pat Lee,1,yes"]), noted("Away for work on Oct 13 and Oct 20."), "on track", "call"),
    (one("email"), pages(["Pat Lee,1,yes"]), noted("Seen in Moncton. Diary set."), "on track", "paper"),
    (one("call"), pages(["Pat Lee,1,yes"]), noted("She prefers the morning. Diary set."), "on track", "call"),
]


def _status(attendance: str, diaries: str, notes: str, status: str, reach: str):
    def test(self) -> None:
        report = run(attendance, diaries, notes)
        client = report.clients[0]
        self.assertEqual(client.status, status)
        self.assertEqual(client.way_to_reach, reach)
        self.assertIn(client.way_to_reach, {"call", "text", "paper", "do not contact"})
        self.assertIn(client.status, {"on track", "stalled"})

    return test


for attendance, diaries, notes, status, reach in STATUS:
    setattr(FridayRuleTests, f"test_f{_index:03d}_status", _status(attendance, diaries, notes, status, reach))
    _index += 1

for layout_name in ("dash", "pipe", "semi", "dash2"):
    setattr(FridayRuleTests, f"test_f{_index:03d}_fifteen", _fifteen("dash" if layout_name == "dash2" else layout_name))
    _index += 1
