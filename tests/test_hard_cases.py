"""Five hundred hard cases. Dates, names, and note layouts are mixed on purpose."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import NotesUnreadableError, process_folder
from tests.test_more_edges import noted, one, pages, run, sheet


PHRASES = [
    ("do not contact", "call", "No calls - no texts - no emails"),
    ("text", "call", "Do not contact - prefers a text"),
    ("call", "paper", "Prefers email - phone call only"),
    ("paper", "call", "Write only"),
    ("text", "paper", "Text message only"),
    ("do not contact", "text", "No calls / no texts / no emails"),
    ("call", "text", "Don't reach out — prefers a call"),
    ("paper", "text", "Text is fine — prefers email"),
    ("do not contact", "call", "No emails, no calls, and no texts"),
    ("text", "paper", "Write only - text message only"),
]

DATES = [
    ("13 Oct. 2026", "20 Oct. 2026"),
    ("Oct. 13, 2026", "Oct. 20, 2026"),
    ("the 13th of October 2026", "the 20th of October 2026"),
    ("13th of October 2026", "20th of October 2026"),
]

SAME_NOTE = [
    ("Do not contact", "Text message only", "text", "call"),
    ("Text is fine", "No calls / no texts / no emails", "do not contact", "text"),
    ("Write only", "Phone call only", "call", "paper"),
    ("Prefers a call", "Don't reach out", "do not contact", "call"),
    ("No further outreach", "Prefers a text", "text", "paper"),
    ("Please text", "Write only", "paper", "text"),
    ("Do not contact", "Phone call only", "call", "text"),
    ("Prefers email", "No calls - no texts - no emails", "do not contact", "paper"),
]

SPLIT = [
    ("Maeve", "O'Brien", "O'Brien"),
    ("Maeve", "O'Brien", "M. O'Brien"),
    ("Luca", "D'Angelo", "D'Angelo"),
    ("Mary", "MacDonald", "Mac Donald"),
    ("Mary", "MacDonald", "Mary Mac Donald"),
    ("Anne", "Roy", "A. Roy"),
]

SPLIT_PHRASES = [
    ("do not contact", "call", "Don't reach out"),
    ("text", "call", "Text message only"),
    ("call", "text", "Phone call only"),
    ("paper", "call", "Write only"),
    ("do not contact", "paper", "No calls - no texts - no emails"),
    ("text", "paper", "Do not contact - prefers a text"),
    ("call", "paper", "Prefers email - phone call only"),
    ("paper", "text", "Text is fine — prefers email"),
]

PARTIALS = [
    "No emails this week",
    "Don't email the bill",
    "She prefers the morning",
    "No texts",
    "Household emergency",
    "Phone bill was high",
    "Do not phone him about the bill",
    "Seen in Halifax only",
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

CHANNEL_DATES = ["13 Oct. 2026", "the 20th of October 2026"]

FORGOT = ["forgot", "forgot it", "did not bring", "didn't bring it", "left it at home", "not brought in"]

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
    ("hard-case-attendance.csv", "Hard Case"),
    ("st-john-register.csv", "St John"),
    ("macdonald-sheet.csv", "Macdonald"),
    ("o-brien-roster.csv", "O Brien"),
    ("harbour-friday-attendance.csv", "Harbour Friday"),
    ("tidewater-register.csv", "Tidewater"),
    ("puffin-sheet.csv", "Puffin"),
    ("bedford-attendance.csv", "Bedford"),
    ("north-gate-roster.csv", "North Gate"),
    ("cedar-row-register.csv", "Cedar Row"),
]

DEFINITION = (
    'Definition of Improved: "A client who completed both Money Checks and '
    'increased their score from the first to the second."'
)
HALFWAY = 'Note: "This is a halfway view. Final scores are not yet available."'

FIFTEEN = [
    ("H1", "Nora", "Quinn", "call", "present", "present", "8", "14", "yes", "yes", "Phone call only", "on track", "call"),
    ("H2", "Omar", "Haddad", "call", "missed", "missed", "8", "9", "yes", "yes", "Diary set", "stalled", "call"),
    ("H3", "Imani", "Cole", "text", "present", "present", "10", "10", "yes", "yes", "Text message only", "on track", "text"),
    ("H4", "Jules", "Perrin", "paper", "present", "present", "5", "9", "yes", "yes", "Write only", "on track", "paper"),
    ("H5", "Nia", "Roy", "call", "present", "present", "8", "12", "forgot", "forgot", "No calls - no texts - no emails", "stalled", "do not contact"),
    ("H6", "Wes", "Adler", "call", "present", "present", "11", "15", "yes", "yes", "No calls / no texts / no emails", "on track", "do not contact"),
    ("H7", "Ada", "Brooks", "call", "absent", "present", "8", "13", "no", "yes", "Diary set", "on track", "call"),
    ("H8", "Beau", "Martin", "text", "present", "present", "7", "8", "yes", "yes", "Do not contact - prefers a text", "on track", "text"),
    ("H9", "Maeve", "O'Brien", "call", "present", "present", "8", "16", "yes", "yes", "Text message only", "on track", "text"),
    ("H10", "Mary", "MacDonald", "call", "present", "present", "4", "9", "yes", "yes", "Phone call only", "on track", "call"),
    ("H11", "Front Desk", "Trial", "call", "present", "present", "1", "2", "yes", "yes", "Don't reach out", "on track", "do not contact"),
    ("H12", "Alex", "Roy", "call", "present", "present", "6", "6", "yes", "yes", "Diary set", "on track", "call"),
    ("H13", "Alex", "Roy", "text", "present", "present", "9", "11", "yes", "yes", "Diary set", "on track", "text"),
    ("H14", "Lynn", "Savoie", "paper", "present", "present", "3", "8", "yes", "yes", "Write only", "on track", "paper"),
    ("H15", "Drew", "Patel", "call", "present", "present", "n/a", "10", "yes", "yes", "Diary set", "on track", "call"),
]


def phrase_layouts(older: str, newer: str, phrase: str) -> list[tuple[str, str]]:
    body = phrase if phrase.endswith(".") else f"{phrase}."
    return [
        (
            "pipe",
            f"{older} | Dana | Pat Lee | Diary set.\n{newer} | Dana | Pat Lee | {body}\n",
        ),
        (
            "dash",
            f"Pat Lee - {older} - Dana - Diary set.\nPat Lee - {newer} - Dana - {body}\n",
        ),
        (
            "message",
            f"Date: {older} Client: Pat Lee Message: Diary set.\n"
            f"Date: {newer} Client: Pat Lee Message: {body}\n",
        ),
        (
            "block",
            f"{older}\nPat Lee (Dana)\nDiary set.\n\n{newer}\nPat Lee (Dana)\n{body}\n",
        ),
    ]


def split_sheet(first: str, last: str, contact: str) -> str:
    return (
        "Client ID,Given name,Surname,Reach by,Wk 1,Wk 2,1st check,2nd check\n"
        f"P1,{first},{last},{contact},present,present,8,12\n"
    )


class HardCaseTests(unittest.TestCase):
    def test_same_full_name_keeps_each_persons_own_contact(self) -> None:
        attendance = (
            "Client ID,Given name,Surname,Reach by,Wk 1,Wk 2,1st check,2nd check\n"
            "A1,Alex,Roy,call,present,present,8,10\n"
            "A2,Alex,Roy,text,present,present,8,10\n"
        )
        notes = "13 Oct. 2026 | Dana | Alex Roy | Don't reach out.\n"
        diaries = pages(["Alex Roy,1,yes", "Alex Roy,2,yes"])
        report = run(attendance, diaries, notes)
        by_id = {client.client_id: client for client in report.clients}
        self.assertEqual(report.total_clients, 2)
        self.assertEqual(by_id["A1"].way_to_reach, "call")
        self.assertEqual(by_id["A2"].way_to_reach, "text")
        self.assertTrue(any("Ambiguous" in warning for warning in report.warnings))

    def test_another_clients_name_inside_the_note_does_not_move_the_instruction(self) -> None:
        attendance = sheet(
            [
                "P1,Pat Lee,call,present,present,8,10",
                "S1,Sam Cole,paper,present,present,8,10",
            ]
        )
        notes = (
            "the 13th of October 2026 | Dana | Pat Lee | "
            "Sam Cole prefers a text. Phone call only.\n"
        )
        report = run(attendance, pages(["Pat Lee,1,yes", "Sam Cole,1,yes"]), notes)
        by_id = {client.client_id: client for client in report.clients}
        self.assertEqual(by_id["P1"].way_to_reach, "call")
        self.assertEqual(by_id["S1"].way_to_reach, "paper")

    def test_quoted_last_first_name_and_reversed_numbered_checks(self) -> None:
        attendance = (
            "Client ID,Learner,Reach by,Week 1,Week 2,2nd check,1st check\n"
            'P1,"Lee, Pat",text,present,present,16,9\n'
        )
        notes = "Date: 13 Oct. 2026 Client: Lee, Pat Message: Phone call only.\n"
        report = run(attendance, pages(["Lee, Pat,1,yes"]), notes)
        self.assertEqual(report.clients[0].way_to_reach, "call")
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.completed_both, 1)
        self.assertEqual(report.improved, 1)

    def test_week_words_and_a_curly_apostrophe(self) -> None:
        notes = "13 Oct. 2026 | Dana | Pat Lee | Don’t reach out.\n"
        diaries = "Client,Week,Handed in\nPat Lee,one,forgot\nPat Lee,two,forgot\n"
        report = run(one("call"), diaries, notes)
        self.assertEqual(report.clients[0].status, "stalled")
        self.assertEqual(report.clients[0].way_to_reach, "do not contact")
        self.assertEqual(report.clients[0].why, "Missed two diaries")


def _contact(attendance_contact: str, notes: str, expected: str):
    def test(self) -> None:
        report = run(one(attendance_contact), pages(["Pat Lee,1,yes"]), notes)
        client = report.clients[0]
        self.assertEqual(client.status, "on track")
        self.assertEqual(client.way_to_reach, expected)
        self.assertIn(client.status, {"on track", "stalled"})
        self.assertIn(client.way_to_reach, {"call", "text", "paper", "do not contact"})

    return test


def _split(first: str, last: str, spoken: str, contact: str, notes: str, expected: str):
    def test(self) -> None:
        full = f"{first} {last}"
        report = run(split_sheet(first, last, contact), pages([f"{full},1,yes"]), notes)
        self.assertEqual(report.total_clients, 1)
        self.assertEqual(report.clients[0].client_id, "P1")
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, expected)
        summary = report.summary_path.read_text(encoding="utf-8")
        self.assertNotIn(first, summary)
        self.assertNotIn(last, summary)

    return test


def _channel(when: str, raw: str, expected: str):
    def test(self) -> None:
        notes = f"{when}\nPat Lee (Dana)\nSeen in Halifax. Diary set.\n"
        report = run(one(raw), pages(["Pat Lee,1,yes"]), notes)
        self.assertEqual(report.clients[0].way_to_reach, expected)
        self.assertEqual(report.clients[0].status, "on track")

    return test


def _forgot(value: str, older: str, newer: str):
    def test(self) -> None:
        notes = (
            f"Date: {older} Client: Pat Lee Message: Diary set.\n"
            f"Date: {newer} Client: Pat Lee Message: Seen in Ottawa.\n"
        )
        report = run(one("call"), pages([f"Pat Lee,1,{value}", f"Pat Lee,2,{value}"]), notes)
        self.assertEqual(report.clients[0].status, "stalled")
        self.assertEqual(report.clients[0].way_to_reach, "call")

    return test


def _score(first: str, second: str, completed: int, improved: int):
    def test(self) -> None:
        attendance = (
            "Client ID,Learner,Reach by,Wk 1,Wk 2,1st check,2nd check\n"
            f"P1,Pat Lee,call,present,present,{first},{second}\n"
        )
        report = run(attendance, pages(["Pat Lee,1,yes"]), noted("Diary set."))
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
            "Date: 13 Oct. 2026 Client: Pat Lee Message: Phone call only.\n",
            attendance_name=filename,
        )
        self.assertEqual(report.agency_name, expected_name)
        self.assertEqual(report.total_clients, 1)
        self.assertEqual(report.clients[0].way_to_reach, "call")
        summary = report.summary_path.read_text(encoding="utf-8")
        self.assertIn("Number of Clients Who Started: 1", summary)
        self.assertIn(DEFINITION, summary)
        self.assertIn(HALFWAY, summary)
        self.assertNotIn("Pat", summary)

    return test


def _fifteen(layout: str):
    def test(self) -> None:
        header = "Client ID,Given name,Surname,Reach by,Wk 1,Wk 2,1st check,2nd check"
        rows = []
        diary_rows = []
        notes = ["13 Oct. 2026 | Dana | Alex Roy | Don't reach out.\n"]
        for item in FIFTEEN:
            client_id, first, last, contact, left, right, low, high, diary_a, diary_b, phrase, _status, _reach = item
            rows.append(",".join([client_id, first, last, contact, left, right, low, high]))
            full = f"{first} {last}"
            diary_rows.extend([f"{full},1,{diary_a}", f"{full},2,{diary_b}"])
            if last == "O'Brien":
                spoken = "O'Brien"
            elif last == "MacDonald":
                spoken = "Mac Donald"
            else:
                spoken = full
            body = phrase if phrase.endswith(".") else f"{phrase}."
            when = "20 Oct. 2026"
            if layout == "message":
                notes.append(f"Date: {when} Client: {spoken} Message: {body}\n")
            elif layout == "dash":
                notes.append(f"{spoken} - {when} - Dana - {body}\n")
            elif layout == "block":
                notes.append(f"\n{when}\n{spoken} (Dana)\n{body}\n")
            else:
                notes.append(f"{when} | Dana | {spoken} | {body}\n")
        report = run(
            header + "\n" + "\n".join(rows) + "\n",
            pages(diary_rows),
            "".join(notes),
            attendance_name="hard-case-attendance.csv",
        )
        self.assertEqual(report.agency_name, "Hard Case")
        self.assertEqual(report.total_clients, 15)
        by_id = {client.client_id: client for client in report.clients}
        missed = []
        for item in FIFTEEN:
            client_id, status, reach = item[0], item[11], item[12]
            got = by_id[client_id]
            if (got.status, got.way_to_reach) != (status, reach):
                missed.append((client_id, got.status, got.way_to_reach, status, reach))
            if reach == "do not contact":
                self.assertEqual(got.way_to_reach, "do not contact")
        self.assertEqual(missed, [])
        summary = report.summary_path.read_text(encoding="utf-8")
        self.assertIn("Number of Clients Who Started: 15", summary)
        self.assertIn(DEFINITION, summary)
        self.assertIn(HALFWAY, summary)
        for item in FIFTEEN:
            self.assertNotIn(item[1], summary)
            self.assertNotIn(item[2], summary)

    return test


def _halt(good: int, bad: int, expect_halt: bool):
    def test(self) -> None:
        folder = Path(tempfile.mkdtemp())
        (folder / "edge-attendance.csv").write_text(
            "Client ID,Given name,Surname,Reach by,Wk 1,Wk 2,1st check,2nd check\n"
            "P1,Pat,Lee,call,present,present,8,10\n",
            encoding="utf-8",
        )
        (folder / "edge-diaries.csv").write_text(pages(["Pat Lee,1,yes"]), encoding="utf-8")
        lines = [f"13 Oct. 2026 | Dana | Pat Lee | Diary set {index}.\n" for index in range(good)]
        lines.extend(f"no date and no person here {index}\n" for index in range(bad))
        (folder / "edge-notes.txt").write_text("".join(lines), encoding="utf-8")
        if expect_halt:
            with self.assertRaises(NotesUnreadableError):
                process_folder(folder, output_dir=folder / "out")
            self.assertFalse((folder / "out" / "results.csv").exists())
            self.assertFalse((folder / "out" / "summary.md").exists())
        else:
            report = process_folder(folder, output_dir=folder / "out")
            self.assertTrue(report.results_path.exists())
            self.assertEqual(report.clients[0].client_id, "P1")

    return test


def _status(attendance: str, diaries: str, notes: str, status: str, reach: str):
    def test(self) -> None:
        report = run(attendance, diaries, notes)
        client = report.clients[0]
        self.assertEqual(client.status, status)
        self.assertEqual(client.way_to_reach, reach)

    return test


STATUS = [
    (
        "Client ID,Learner,Reach by,Wk 1,Wk 2,1st check,2nd check\nP1,Pat Lee,call,missed,missed,8,9\n",
        pages(["Pat Lee,1,yes"]),
        "Date: 13 Oct. 2026 Client: Pat Lee Message: Diary set.\n",
        "stalled",
        "call",
    ),
    (
        "Client ID,Learner,Reach by,Week one,Week two,1st check,2nd check\nP1,Pat Lee,call,present,present,8,14\n",
        pages(["Pat Lee,1,yes"]),
        "the 13th of October 2026 | Dana | Pat Lee | Phone call only.\n",
        "on track",
        "call",
    ),
    (one("call", "absent,present"), pages(["Pat Lee,1,no"]), "13 Oct. 2026 | Dana | Pat Lee | Diary set.\n", "on track", "call"),
    (one("call"), pages(["Pat Lee,one,forgot", "Pat Lee,two,forgot"]), "13 Oct. 2026 | Dana | Pat Lee | Household emergency.\n", "stalled", "call"),
    (one("call"), pages(["Pat Lee,one,forgot", "Pat Lee,two,forgot"]), "13 Oct. 2026 | Dana | Pat Lee | I did not set the diary.\n20 Oct. 2026 | Dana | Pat Lee | Not typed yet.\n", "on track", "call"),
    (one("text"), pages(["Pat Lee,1,yes"]), "Pat Lee - 13 Oct. 2026 - Dana - Write only.\n", "on track", "paper"),
    (one("paper"), pages(["Pat Lee,1,yes"]), "Pat Lee - 13 Oct. 2026 - Dana - Text message only.\n", "on track", "text"),
    (one("call"), pages(["Pat Lee,1,not typed yet", "Pat Lee,2,not typed yet"]), "13 Oct. 2026 | Dana | Pat Lee | Diary set.\n", "on track", "call"),
    (one("call", "NS,NS"), pages(["Pat Lee,1,yes"]), "Oct. 13, 2026 | Dana | Pat Lee | Seen in Moncton.\n", "stalled", "call"),
    (one("email"), pages(["Pat Lee,1,yes"]), "the 13th of October 2026 | Dana | Pat Lee | Diary set.\n", "on track", "paper"),
    (one("none"), pages(["Pat Lee,1,yes"]), "13 Oct. 2026 | Dana | Pat Lee | Diary set.\n", "on track", "do not contact"),
    (one("call"), pages(["Pat Lee,1,", "Pat Lee,2,"]), "13 Oct. 2026 | Dana | Pat Lee | Diary set.\n", "on track", "call"),
    (one("call"), pages(["Pat Lee,1,yes"]), "13 Oct. 2026\nPat Lee (Dana)\nNo calls - no texts - no emails.\n", "on track", "do not contact"),
    (one("text"), pages(["Pat Lee,1,yes"]), "13 Oct. 2026\nPat Lee (Dana)\nDo not contact - phone call only.\n", "on track", "call"),
    (one("call", "late,showed up"), pages(["Pat Lee,1,yes"]), "Date: Oct. 20, 2026 Client: Pat Lee Update: Diary set.\n", "on track", "call"),
    (one("call"), pages(["Pat Lee,1,left it at home", "Pat Lee,2,left it at home"]), "13 Oct. 2026 | Dana | Pat Lee | Away for work.\n20 Oct. 2026 | Dana | Pat Lee | Away for work.\n", "on track", "call"),
    (one("call"), pages(["Pat Lee,1,yes"]), "Date: 13 Oct. 2026 Name: Pat Lee Comment: Text message only.\n", "on track", "text"),
    (one("paper"), pages(["Pat Lee,1,yes"]), "Date: 13 Oct. 2026 Client: Pat Lee Entry: Don't reach out.\n", "on track", "do not contact"),
    (one("call", "A.,A."), pages(["Pat Lee,1,yes"]), "13 Oct. 2026 | Dana | P. Lee | Diary set.\n", "stalled", "call"),
    (one("call"), pages(["Pat Lee,1,yes"]), "13 Oct. 2026 | Dana | Lee, Pat | Write only.\n", "on track", "paper"),
]


_index = 0
for expected, fallback, phrase in PHRASES:
    for older, newer in DATES:
        for layout_name, notes in phrase_layouts(older, newer, phrase):
            setattr(HardCaseTests, f"test_h{_index:03d}_{layout_name}", _contact(fallback, notes, expected))
            _index += 1

for earlier, later, expected, fallback in SAME_NOTE:
    for _older, newer in DATES:
        for layout_name in ("pipe", "message"):
            if layout_name == "message":
                notes = f"Date: {newer} Client: Pat Lee Message: {earlier}. {later}.\n"
            else:
                notes = f"{newer} | Dana | Pat Lee | {earlier}. {later}.\n"
            setattr(HardCaseTests, f"test_h{_index:03d}_{layout_name}", _contact(fallback, notes, expected))
            _index += 1

for first, last, spoken in SPLIT:
    for expected, fallback, phrase in SPLIT_PHRASES:
        for layout_name in ("pipe", "message"):
            when = "13 Oct. 2026"
            if layout_name == "message":
                notes = f"Date: {when} Client: {spoken} Message: {phrase}.\n"
            else:
                notes = f"{when} | Dana | {spoken} | {phrase}.\n"
            setattr(
                HardCaseTests,
                f"test_h{_index:03d}_{layout_name}",
                _split(first, last, spoken, fallback, notes, expected),
            )
            _index += 1

for phrase in PARTIALS:
    for older, newer in DATES:
        for layout_name in ("dash", "block"):
            if layout_name == "dash":
                notes = (
                    f"Pat Lee - {older} - Dana - Diary set.\n"
                    f"Pat Lee - {newer} - Dana - {phrase}.\n"
                )
            else:
                notes = f"{older}\nPat Lee (Dana)\nDiary set.\n\n{newer}\nPat Lee (Dana)\n{phrase}.\n"
            setattr(HardCaseTests, f"test_h{_index:03d}_partial", _contact("call", notes, "call"))
            _index += 1

for when in CHANNEL_DATES:
    for raw, expected in CHANNELS:
        setattr(HardCaseTests, f"test_h{_index:03d}_channel", _channel(when, raw, expected))
        _index += 1

for value in FORGOT:
    for older, newer in DATES:
        setattr(HardCaseTests, f"test_h{_index:03d}_forgot", _forgot(value, older, newer))
        _index += 1

for first, second, completed, improved in SCORES:
    setattr(HardCaseTests, f"test_h{_index:03d}_score", _score(first, second, completed, improved))
    _index += 1

for filename, agency in AGENCIES:
    setattr(HardCaseTests, f"test_h{_index:03d}_agency", _agency(filename, agency))
    _index += 1

for attendance, diaries, notes, status, reach in STATUS:
    setattr(HardCaseTests, f"test_h{_index:03d}_status", _status(attendance, diaries, notes, status, reach))
    _index += 1

for layout_name in ("pipe", "dash", "message", "block"):
    setattr(HardCaseTests, f"test_h{_index:03d}_fifteen", _fifteen(layout_name))
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
    setattr(HardCaseTests, f"test_h{_index:03d}_halt", _halt(good, bad, expect_halt))
    _index += 1
