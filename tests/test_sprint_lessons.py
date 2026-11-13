"""Five hundred cases drawn from the Sprint 2 and Sprint 3 file changes.

Sprint 2 kept the same columns and moved the dates forward, but older facts
stayed in the file. Sprint 3 renamed the city, shortened names to initials,
added credentials such as PT and DPT, and left a front-desk trial row in the
sheet. These cases copy those moves onto attendance, diaries, and notes.
"""

from __future__ import annotations

import unittest

from tests.test_more_edges import noted, one, pages, run, sheet


PHRASES = [
    ("do not contact", "call", "Do not get in touch"),
    ("do not contact", "text", "Don't get in touch"),
    ("do not contact", "paper", "No further contact"),
    ("do not contact", "call", "Please stop contacting her"),
    ("do not contact", "text", "She declined all contact"),
    ("do not contact", "call", "Do not call or text or mail"),
    ("do not contact", "paper", "Do not call, do not text, or write"),
    ("do not contact", "call", "No calling, no texting, and no mailing"),
    ("call", "text", "Please phone"),
    ("call", "paper", "Calling is okay"),
    ("call", "text", "Okay to call"),
    ("call", "paper", "Give her a call"),
    ("text", "call", "Please text"),
    ("text", "paper", "Okay to text"),
    ("paper", "call", "Emails only"),
    ("paper", "text", "Paper notes only"),
]

DATES = [
    ("13 Oct 2026", "20 Oct 2026"),
    ("2026-10-13", "2026-10-20"),
    ("13-Oct-2026", "20-Oct-2026"),
    ("October 13th, 2026", "October 20th, 2026"),
]

PAIRS = [
    ("Do not contact. Still in the old export.", "Please text", "text", "call"),
    ("Text is fine. Still in the old export.", "Do not get in touch", "do not contact", "text"),
    ("Please call. Still in the old export.", "Emails only", "paper", "call"),
    ("Letter only. Still in the old export.", "Calling is okay", "call", "paper"),
    ("Do not contact. Still in the old export.", "Okay to call", "call", "text"),
    ("Call is fine. Still in the old export.", "No further contact", "do not contact", "call"),
    ("Paper is preferred. Still in the old export.", "Please text", "text", "paper"),
    ("SMS is fine. Still in the old export.", "Do not call or text or mail", "do not contact", "text"),
]

PEOPLE = [
    ("Heidi Dempsey", "H. Dempsey"),
    ("Ewan MacPhee", "E. MacPhee, PT"),
    ("Moira Ferguson", "Dr. M. Ferguson, DPT"),
    ("Valerie Belanger", "Valérie Bélanger"),
    ("Josee Landry", "Josée Landry"),
    ("Therese Haley", "Thérèse Haley"),
]

NAME_PHRASES = [
    ("do not contact", "call", "Do not get in touch"),
    ("text", "call", "Please text"),
    ("call", "text", "Please phone"),
    ("paper", "call", "Emails only"),
    ("do not contact", "text", "No further contact"),
    ("call", "paper", "Okay to call"),
]

NAME_DATES = [
    ("13 Oct 2026", "20 Oct 2026"),
]

TRIPLES = [
    ("13 Jul 2026", "13 Aug 2026", "13 Oct 2026"),
    ("2026-07-13", "2026-08-13", "2026-10-13"),
    ("13-Jul-2026", "13-Aug-2026", "13-Oct-2026"),
    ("July 13th, 2026", "August 13th, 2026", "October 13th, 2026"),
]

PARTIALS = [
    "No texts",
    "Do not phone him about the bill",
    "Household emergency",
    "Phone bill was high",
    "No mail this week",
    "Seen in Ottawa only",
    "Front desk trial, not a client note for Pat",
    "Still on the old waitlist from July",
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

TYPED = ["Not typed yet.", "Not yet typed.", "Hasn't been typed."]

SCORES = [
    ("8/25", "14/25", 1, 1),
    ("12 out of 25", "12 out of 25", 1, 0),
    ("18 out of 25", "12 out of 25", 1, 0),
    ("n/a", "14", 0, 0),
    ("10", "", 0, 0),
    ("9", "9.5", 1, 1),
    ("15", "15", 1, 0),
    ("7 of 25", "11 of 25", 1, 1),
    ("20", "19", 1, 0),
    ("", "12", 0, 0),
]

AGENCIES = [
    ("halifax-register.csv", "Halifax"),
    ("moncton-roster.csv", "Moncton"),
    ("tidewater-sheet.csv", "Tidewater"),
    ("kettle-attendance.csv", "Kettle"),
    ("harbour-light-register.csv", "Harbour Light"),
    ("north-gate-roster.csv", "North Gate"),
    ("puffin-sheet.csv", "Puffin"),
    ("bedford-basin-attendance.csv", "Bedford Basin"),
]


def phrase_layouts(older: str, newer: str, phrase: str) -> list[tuple[str, str]]:
    body = f"Seen in Halifax. {phrase}."
    return [
        (
            "pipe",
            f"{older} | Dana | Pat Lee | Diary set.\n{newer} | Dana | Pat Lee | {body}\n",
        ),
        (
            "dash",
            f"{older} - Dana - Pat Lee - Diary set.\n{newer} - Dana - Pat Lee - {body}\n",
        ),
        (
            "labelled",
            f"Date: {older} Client: Pat Lee Note: Diary set.\n"
            f"Date: {newer} Client: Pat Lee Note: {body}\n",
        ),
    ]


def old_new_notes(older: str, newer: str, old_body: str, new_body: str, layout: str) -> str:
    latest = f"Seen in Halifax. {new_body}."
    if layout == "pipe":
        return (
            f"{older} | Dana | Pat Lee | {old_body}\n"
            f"{newer} | Dana | Pat Lee | {latest}\n"
        )
    return (
        f"[{older}] Dana | Pat Lee: {old_body}\n"
        f"[{newer}] Dana | Pat Lee: {latest}\n"
    )


def name_notes(spoken: str, older: str, newer: str, phrase: str, layout: str) -> str:
    if layout == "pipe":
        return (
            f"{older} | Dana | {spoken} | Seen in Halifax. Diary set.\n"
            f"{newer} | Dana | {spoken} | {phrase}.\n"
        )
    return (
        f"{spoken} ({older}, Dana): Seen in Halifax. Diary set.\n"
        f"{spoken} ({newer}, Dana): {phrase}.\n"
    )


def triple_notes(first: str, second: str, third: str, layout: str) -> str:
    lines = [
        (first, "Text is fine. Still in the old export."),
        (second, "Do not contact. Still in the old export."),
        (third, "Seen in Halifax. Emails only."),
    ]
    if layout == "pipe":
        return "".join(f"{when} | Dana | Pat Lee | {body}\n" for when, body in lines)
    if layout == "dash":
        return "".join(f"{when} - Dana - Pat Lee - {body}\n" for when, body in lines)
    return "".join(f"Date: {when} Client: Pat Lee Note: {body}\n" for when, body in lines)


class SprintLessonTests(unittest.TestCase):
    def test_trial_row_stays_and_does_not_change_the_others(self) -> None:
        attendance = sheet(
            [
                "T0,Front Desk Trial,call,present,present,8,9",
                "P1,Pat Lee,call,present,present,8,12",
                "S1,Sam Cole,text,present,present,10,11",
            ]
        )
        notes = (
            "13 Oct 2026 | Dana | Front Desk Trial | Do not get in touch. Trial row.\n"
            "13 Oct 2026 | Dana | Pat Lee | Seen in Halifax. Diary set.\n"
            "13 Oct 2026 | Dana | Sam Cole | Seen in Ottawa. Diary set.\n"
        )
        diaries = pages(
            ["Front Desk Trial,1,yes", "Pat Lee,1,yes", "Sam Cole,1,yes"]
        )
        report = run(attendance, diaries, notes, stem="halifax")
        by_id = {client.client_id: client for client in report.clients}
        self.assertEqual(report.total_clients, 3)
        self.assertEqual(by_id["T0"].way_to_reach, "do not contact")
        self.assertEqual(by_id["P1"].way_to_reach, "call")
        self.assertEqual(by_id["P1"].status, "on track")
        self.assertEqual(by_id["S1"].way_to_reach, "text")
        summary = report.summary_path.read_text(encoding="utf-8")
        for banned in ("Pat", "Sam", "Trial", "Lee", "Cole"):
            self.assertNotIn(banned, summary)

    def test_shared_first_name_does_not_spread_a_ban(self) -> None:
        attendance = sheet(
            [
                "L1,Lynn Savoie,call,present,present,8,10",
                "L2,Lynn Smith,text,present,present,8,10",
            ]
        )
        notes = "13 Oct 2026 | Dana | Lynn | Do not get in touch.\n"
        diaries = pages(["Lynn Savoie,1,yes", "Lynn Smith,1,yes"])
        report = run(attendance, diaries, notes)
        by_id = {client.client_id: client for client in report.clients}
        self.assertEqual(by_id["L1"].way_to_reach, "call")
        self.assertEqual(by_id["L2"].way_to_reach, "text")
        self.assertTrue(any("Ambiguous" in warning for warning in report.warnings))

    def test_full_name_updates_only_that_lynn(self) -> None:
        attendance = sheet(
            [
                "L1,Lynn Savoie,call,present,present,8,10",
                "L2,Lynn Smith,call,present,present,8,10",
            ]
        )
        notes = "20 Oct 2026 | Dana | Lynn Savoie | Please text. Seen in Moncton.\n"
        diaries = pages(["Lynn Savoie,1,yes", "Lynn Smith,1,yes"])
        report = run(attendance, diaries, notes)
        by_id = {client.client_id: client for client in report.clients}
        self.assertEqual(by_id["L1"].way_to_reach, "text")
        self.assertEqual(by_id["L2"].way_to_reach, "call")

    def test_case_number_with_hyphen_matches_the_compact_id(self) -> None:
        attendance = sheet(
            [
                "C-10,Pat Lee,call,present,present,8,10",
                "C-11,Sam Cole,paper,present,present,8,10",
            ]
        )
        notes = "13 Oct 2026 | Dana | C10 | Please text.\n"
        diaries = pages(["Pat Lee,1,yes", "Sam Cole,1,yes"])
        report = run(attendance, diaries, notes)
        by_id = {client.client_id: client for client in report.clients}
        self.assertEqual(by_id["C-10"].way_to_reach, "text")
        self.assertEqual(by_id["C-11"].way_to_reach, "paper")

    def test_shared_last_name_does_not_spread_a_ban(self) -> None:
        attendance = sheet(
            [
                "C1,Sam Cole,call,present,present,8,10",
                "C2,Pat Cole,text,present,present,8,10",
            ]
        )
        notes = "13 Oct 2026 | Dana | Cole | Do not get in touch.\n"
        diaries = pages(["Sam Cole,1,yes", "Pat Cole,1,yes"])
        report = run(attendance, diaries, notes)
        by_id = {client.client_id: client for client in report.clients}
        self.assertEqual(by_id["C1"].way_to_reach, "call")
        self.assertEqual(by_id["C2"].way_to_reach, "text")

    def test_one_absence_and_one_diary_miss_stays_on_track(self) -> None:
        report = run(
            one("call", "absent,present"),
            pages(["Pat Lee,1,no"]),
            noted("Seen in Halifax. Diary set."),
        )
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_ran_long_excuses_only_that_week(self) -> None:
        notes = (
            "13 Oct 2026 | Dana | Pat Lee | Session ran long.\n"
            "20 Oct 2026 | Dana | Pat Lee | Seen in Halifax. Diary set.\n"
        )
        report = run(one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), notes)
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, "call")

    def test_hold_does_not_erase_earlier_diary_misses(self) -> None:
        attendance = sheet(
            [
                "P1,Pat Lee,call,present,present,present,8,10",
                "S1,Sam Cole,call,present,present,present,8,10",
            ],
            header="Client ID,Client,Reach by,Mtg 1,Mtg 2,Mtg 3,Check A,Check B",
        )
        notes = (
            "13 Oct 2026 | Dana | Sam Cole | Diary set.\n"
            "20 Oct 2026 | Dana | Sam Cole | Diary set.\n"
            "27 Oct 2026 | Dana | Sam Cole | Diary set.\n"
            "27 Oct 2026 | Dana | Pat Lee | Diary on hold. Seen in Halifax.\n"
        )
        diaries = pages(
            [
                "Pat Lee,1,no",
                "Pat Lee,2,no",
                "Pat Lee,3,no",
                "Sam Cole,1,yes",
                "Sam Cole,2,yes",
                "Sam Cole,3,yes",
            ]
        )
        report = run(attendance, diaries, notes)
        pat = next(client for client in report.clients if client.client_id == "P1")
        self.assertEqual(pat.status, "stalled")
        self.assertEqual(pat.way_to_reach, "call")

    def test_away_on_the_named_days_keeps_both_absences_on_track(self) -> None:
        attendance = sheet(
            [
                "P1,Pat Lee,call,absent,absent,8,10",
                "S1,Sam Cole,text,present,present,8,10",
            ]
        )
        notes = (
            "27 Oct 2026 | Dana | Pat Lee | Away for work.\n"
            "3 Nov 2026 | Dana | Pat Lee | Away for work.\n"
            "27 Oct 2026 | Dana | Sam Cole | Seen in Halifax. Diary set.\n"
            "3 Nov 2026 | Dana | Sam Cole | Diary set.\n"
        )
        diaries = pages(["Pat Lee,1,yes", "Sam Cole,1,yes"])
        report = run(attendance, diaries, notes)
        pat = next(client for client in report.clients if client.client_id == "P1")
        self.assertEqual(pat.status, "on track")
        self.assertEqual(pat.way_to_reach, "call")

    def test_one_stray_date_does_not_move_the_excuse(self) -> None:
        attendance = sheet(
            [
                "P1,Pat Lee,call,present,present,8,10",
                "S1,Sam Cole,call,present,present,8,10",
                "N1,Nia Roy,call,present,present,8,10",
            ]
        )
        notes = (
            "10 Oct 2026 | Dana | Nia Roy | Diary set.\n"
            "13 Oct 2026 | Dana | Pat Lee | Diary set.\n"
            "13 Oct 2026 | Dana | Sam Cole | Diary set.\n"
            "20 Oct 2026 | Dana | Pat Lee | I did not set the diary.\n"
            "20 Oct 2026 | Dana | Sam Cole | Diary set.\n"
        )
        diaries = pages(["Pat Lee,1,no", "Pat Lee,2,no", "Sam Cole,1,yes", "Nia Roy,1,yes"])
        report = run(attendance, diaries, notes)
        pat = next(client for client in report.clients if client.client_id == "P1")
        self.assertEqual(pat.status, "on track")

    def test_month_first_when_the_file_proves_it(self) -> None:
        attendance = sheet(
            [
                "P1,Pat Lee,call,present,present,8,10",
                "S1,Sam Cole,paper,present,present,8,10",
            ]
        )
        notes = (
            "03/11/2026 | Dana | Pat Lee | Do not contact.\n"
            "04/02/2026 | Dana | Pat Lee | Please text.\n"
            "03/15/2026 | Dana | Sam Cole | Diary set.\n"
        )
        diaries = pages(["Pat Lee,1,yes", "Sam Cole,1,yes"])
        report = run(attendance, diaries, notes)
        pat = next(client for client in report.clients if client.client_id == "P1")
        self.assertEqual(pat.way_to_reach, "text")

    def test_both_date_clues_stay_day_first(self) -> None:
        attendance = sheet(
            [
                "P1,Pat Lee,call,present,present,8,10",
                "S1,Sam Cole,paper,present,present,8,10",
            ]
        )
        notes = (
            "03/11/2026 | Dana | Pat Lee | Please text.\n"
            "04/02/2026 | Dana | Pat Lee | Do not contact.\n"
            "03/15/2026 | Dana | Sam Cole | Diary set.\n"
            "15/03/2026 | Dana | Sam Cole | Diary set.\n"
        )
        diaries = pages(["Pat Lee,1,yes", "Sam Cole,1,yes"])
        report = run(attendance, diaries, notes)
        pat = next(client for client in report.clients if client.client_id == "P1")
        self.assertEqual(pat.way_to_reach, "text")


def _contact(attendance_contact: str, notes: str, expected: str):
    def test(self) -> None:
        report = run(one(attendance_contact), pages(["Pat Lee,1,yes"]), notes)
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, expected)

    return test


def _named(attendance_name: str, spoken: str, contact: str, notes: str, expected: str):
    def test(self) -> None:
        attendance = sheet([f"P1,{attendance_name},{contact},present,present,8,12"])
        report = run(attendance, pages([f"{attendance_name},1,yes"]), notes)
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, expected)
        self.assertEqual(report.total_clients, 1)

    return test


def _channel(city: str, raw: str, expected: str):
    def test(self) -> None:
        notes = f"13 Oct 2026 | Dana | Pat Lee | Seen in {city}. Diary set.\n"
        report = run(one(raw), pages(["Pat Lee,1,yes"]), notes)
        self.assertEqual(report.clients[0].way_to_reach, expected)
        self.assertEqual(report.clients[0].status, "on track")

    return test


def _typed(phrase: str, older: str, newer: str):
    def test(self) -> None:
        notes = (
            f"{older} | Dana | Pat Lee | {phrase}\n"
            f"{newer} | Dana | Pat Lee | {phrase} Seen in Halifax.\n"
        )
        report = run(one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), notes)
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.clients[0].way_to_reach, "call")

    return test


def _household(older: str, newer: str):
    def test(self) -> None:
        notes = (
            f"{older} | Dana | Pat Lee | Household emergency. Seen in Halifax.\n"
            f"{newer} | Dana | Pat Lee | Household emergency.\n"
        )
        report = run(one("call"), pages(["Pat Lee,1,no", "Pat Lee,2,no"]), notes)
        self.assertEqual(report.clients[0].status, "stalled")
        self.assertEqual(report.clients[0].way_to_reach, "call")

    return test


def _city_absence(city: str):
    def test(self) -> None:
        report = run(
            one("call", "missed,missed"),
            pages(["Pat Lee,1,yes"]),
            noted(f"Seen in {city}. Diary set."),
        )
        self.assertEqual(report.clients[0].status, "stalled")
        self.assertEqual(report.clients[0].way_to_reach, "call")

    return test


def _score(first: str, second: str, completed: int, improved: int):
    def test(self) -> None:
        attendance = sheet([f"P1,Pat Lee,call,present,present,{first},{second}"])
        report = run(attendance, pages(["Pat Lee,1,yes"]), noted("Seen in Halifax. Diary set."))
        self.assertEqual(report.completed_both, completed)
        self.assertEqual(report.improved, improved)
        self.assertEqual(report.total_clients, 1)

    return test


def _agency(filename: str, expected: str):
    def test(self) -> None:
        report = run(
            one("text"),
            pages(["Pat Lee,1,yes"]),
            noted("Please phone. Seen in Halifax."),
            attendance_name=filename,
        )
        self.assertEqual(report.agency_name, expected)
        self.assertEqual(report.clients[0].way_to_reach, "call")
        self.assertEqual(report.total_clients, 1)

    return test


def _header(attendance: str):
    def test(self) -> None:
        report = run(attendance, pages(["Pat Lee,1,yes"]), noted("Call is fine. Seen in Halifax."))
        self.assertEqual(report.clients[0].client_id, "P1")
        self.assertEqual(report.clients[0].way_to_reach, "call")
        self.assertEqual(report.clients[0].status, "on track")
        self.assertEqual(report.completed_both, 1)
        self.assertEqual(report.improved, 1)

    return test


HEADERS = [
    "Client ID,Learner,Coach,Preferred channel,Visit 1,Visit 2,First check,Second check\n"
    "P1,Pat Lee,Dana,text,present,present,8,14\n",
    "Halifax roll\n"
    "Case No;Learner;Coach;How to reach;Class 1;Class 2;Check A;Check B\n"
    "P1;Pat Lee;Dana;text;present;present;8;14\n",
    "Case Number,Participant,Worker,Preferred Route,Session 1,Session 2,First Score,Second Score\n"
    "P1,Pat Lee,Dana,text,present,present,8,14\n",
    "\ufeffClient #,Learner,Staff,Contact method,Visit 1,Visit 2,Check One,Check Two\n"
    "P1,Pat Lee,Dana,text,present,present,8,14\n",
    "Client ID\tLearner\tReach by\tVisit 1\tVisit 2\tCheck One\tCheck Two\n"
    "P1\tPat Lee\ttext\tpresent\tpresent\t8\t14\n",
    "No.,Client,Reach by,Mtg 1,Mtg 2,Check One,Check Two\n"
    "P1,Pat Lee,text,showed,showed,8,14\n",
]


_index = 0
for expected, attendance_contact, phrase in PHRASES:
    for older, newer in DATES:
        for layout_name, notes in phrase_layouts(older, newer, phrase):
            setattr(
                SprintLessonTests,
                f"test_s{_index:03d}_{layout_name}",
                _contact(attendance_contact, notes, expected),
            )
            _index += 1

for old_body, new_body, expected, fallback in PAIRS:
    for older, newer in DATES:
        for layout_name in ("pipe", "bracket"):
            setattr(
                SprintLessonTests,
                f"test_s{_index:03d}_{layout_name}",
                _contact(fallback, old_new_notes(older, newer, old_body, new_body, layout_name), expected),
            )
            _index += 1

for attendance_name, spoken in PEOPLE:
    for expected, fallback, phrase in NAME_PHRASES:
        for older, newer in NAME_DATES:
            for layout_name in ("pipe", "paren"):
                setattr(
                    SprintLessonTests,
                    f"test_s{_index:03d}_{layout_name}",
                    _named(
                        attendance_name,
                        spoken,
                        fallback,
                        name_notes(spoken, older, newer, phrase, layout_name),
                        expected,
                    ),
                )
                _index += 1

for first, second, third in TRIPLES:
    for layout_name in ("pipe", "dash", "labelled"):
        setattr(
            SprintLessonTests,
            f"test_s{_index:03d}_{layout_name}",
            _contact("call", triple_notes(first, second, third, layout_name), "paper"),
        )
        _index += 1

for phrase in PARTIALS:
    for older, newer in DATES:
        notes = (
            f"{older} | Dana | Pat Lee | Diary set.\n"
            f"{newer} | Dana | Pat Lee | {phrase}. Seen in Halifax.\n"
        )
        setattr(SprintLessonTests, f"test_s{_index:03d}_partial", _contact("call", notes, "call"))
        _index += 1

for city in CITIES:
    for raw, expected in CHANNELS:
        setattr(SprintLessonTests, f"test_s{_index:03d}_channel", _channel(city, raw, expected))
        _index += 1

for phrase in TYPED:
    for older, newer in DATES:
        setattr(SprintLessonTests, f"test_s{_index:03d}_typed", _typed(phrase, older, newer))
        _index += 1

for older, newer in DATES:
    setattr(SprintLessonTests, f"test_s{_index:03d}_household", _household(older, newer))
    _index += 1

for city in CITIES:
    setattr(SprintLessonTests, f"test_s{_index:03d}_city", _city_absence(city))
    _index += 1

for first, second, completed, improved in SCORES:
    setattr(SprintLessonTests, f"test_s{_index:03d}_score", _score(first, second, completed, improved))
    _index += 1

for filename, agency in AGENCIES:
    setattr(SprintLessonTests, f"test_s{_index:03d}_agency", _agency(filename, agency))
    _index += 1

for attendance in HEADERS:
    setattr(SprintLessonTests, f"test_s{_index:03d}_header", _header(attendance))
    _index += 1


if __name__ == "__main__":
    unittest.main()
