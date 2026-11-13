from __future__ import annotations

import csv
import io
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Iterable


class NotesUnreadableError(RuntimeError):
    """Raised when notes are missing or cannot be read reliably."""


class InputDiscoveryError(RuntimeError):
    """Raised when the input folder does not contain one clear data set."""


@dataclass
class Note:
    note_date: date | None
    person_text: str
    counsellor_text: str
    body: str


@dataclass
class DiaryEntry:
    week: int | None
    entry_date: date | None
    handed_in: str
    person_text: str
    counsellor_text: str


@dataclass
class Client:
    client_id: str
    name: str
    counsellor: str
    attendance_contact: str
    sessions: list[str]
    scores: list[str]
    notes: list[Note] = field(default_factory=list)
    diaries: list[DiaryEntry] = field(default_factory=list)


@dataclass
class ClientResult:
    client_id: str
    status: str
    way_to_reach: str
    why: str


@dataclass
class ReportResult:
    agency_name: str
    total_clients: int
    completed_both: int
    improved: int
    clients: list[ClientResult]
    warnings: list[str]
    results_path: Path
    summary_path: Path


@dataclass
class InputFiles:
    attendance: Path
    diaries: Path | None
    notes: Path


ALIASES = {
    "beth": "elizabeth",
    "bill": "william",
    "gord": "gordon",
    "liz": "elizabeth",
    "ray": "raymond",
    "ron": "ronald",
    "terry": "terrence",
    "theo": "theodore",
    "tony": "anthony",
}

PRESENT_VALUES = {
    "p",
    "present",
    "late",
    "attended",
    "yes",
    "y",
    "here",
    "completed",
    "showed",
    "showed up",
    "late arrival",
}
ABSENT_VALUES = {
    "a",
    "absent",
    "no show",
    "noshow",
    "n s",
    "missed",
    "did not attend",
    "didnt attend",
    "not present",
    "ns",
}
DIARY_NO_VALUES = {
    "no",
    "n",
    "not handed in",
    "not submitted",
    "not returned",
    "missing",
    "not done",
    "incomplete",
    "wasn t handed in",
    "wasn t returned",
    "didn t hand in",
    "didn t return",
    "forgot",
    "forgot it",
    "did not bring",
    "didn t bring",
    "didn t bring it",
    "left it at home",
    "left the diary at home",
    "not brought",
    "not brought in",
}
DIARY_YES_VALUES = {
    "yes",
    "y",
    "handed in",
    "returned",
    "done",
    "complete",
    "completed",
}

STOP_CONTACT_PATTERNS = (
    r"\bdo not contact\b",
    r"\bdon t contact\b",
    r"\bno contact\b",
    r"\bno outreach\b",
    r"\bnot to (?:contact|reach out)\b",
    r"\bnot to reach out\b",
    r"\bnot to be contacted\b",
    r"\bno calls?\b.*\bno texts?\b.*\bno mail\b",
    r"\bno texts?\b.*\bno calls?\b.*\bno mail\b",
    r"\bdo not reach out\b",
    r"\bdo not (?:calls?|phones?)\b.*\bdo not texts?\b.*\bdo not (?:send )?(?:mail|letters?|post)\b",
    r"\bno (?:phone )?calls?\b.*\bno texts?(?: messages?)?\b.*\bno (?:mail|letters?|post)\b",
    r"\bno phones?\b.*\bno texts?\b.*\bno (?:mail|letters?|post)\b",
    r"\bdo not get in touch\b",
    r"\bdon t get in touch\b",
    r"\bnot to get in touch\b",
    r"\bno further contact\b",
    r"\bstop contacting\b",
    r"\bdeclined all contact\b",
    r"\bdo not (?:call|phone) or text or (?:mail|post|write|letter)\b",
    r"\bdo not (?:call|phone)\b.*\bdo not text\b.*\b(?:write|mail|letter|post)\b",
    r"\bno calling\b.*\bno texting\b.*\bno (?:mailing|mail|letters?|post|e ?mails?)\b",
    r"\bdon t reach out\b",
    r"\bno further outreach\b",
    r"\bnot to be reached\b",
    r"\bdo not reach (?:her|him|them)\b",
)

DIARY_EXCUSE_PATTERNS = (
    r"\bdid not set\b",
    r"\bdidn t set\b",
    r"\bwasn t set\b",
    r"\bnot set\b",
    r"\bhw not set\b",
    r"\bno homework (?:went|was sent)\b",
    r"\bdiary (?:is |still )?on hold\b",
    r"\bon hold\b",
    r"\baway for work\b",
    r"\bmoving house\b",
    r"\bhomework not assigned\b",
    r"\bdid not give (?:the |out )?diary\b",
    r"\bsession ran over\b",
    r"\bwent long\b",
    r"\bran (?:out of time|long)\b",
    r"\bnot typed yet\b",
    r"\bnot yet typed\b",
    r"\bhasn t been typed\b",
)

ATTENDANCE_EXCUSE_PATTERNS = (
    r"\baway for work\b",
    r"\baway with notice\b",
    r"\bmoving (?:house|x?2 wks|this week)\b",
    r"\btold us ahead\b",
)


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold().replace("&", " and ")
    return " ".join(re.findall(r"[a-z0-9]+", text))


def compact(value: object) -> str:
    return normalize(value).replace(" ", "")


def fuzzy_ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize(left), normalize(right)).ratio()


def header_is_client_id(header: str) -> bool:
    return bool(
        re.search(r"(?i)\bclients?\b", header)
        and re.search(r"(?i)#|\b(?:no|num|number|id)\b", header)
    )


def choose_column(
    headers: Iterable[str],
    candidates: Iterable[str],
    *,
    required: bool = False,
    minimum: float = 0.62,
    skip_client_ids: bool = False,
) -> str | None:
    header_list = [h for h in headers if h is not None]
    if skip_client_ids:
        kept = [header for header in header_list if not header_is_client_id(header)]
        if kept:
            header_list = kept
    candidate_list = list(candidates)
    best: tuple[float, str] | None = None
    for header in header_list:
        normalized_header = normalize(header)
        for candidate in candidate_list:
            normalized_candidate = normalize(candidate)
            if normalized_header == normalized_candidate:
                score = 1.0
            elif normalized_candidate in normalized_header.split():
                score = 0.93
            elif len(normalized_candidate) >= 4 and (
                normalized_candidate in normalized_header
                or normalized_header in normalized_candidate
            ):
                score = 0.88
            else:
                score = fuzzy_ratio(normalized_header, normalized_candidate)
            if best is None or score > best[0]:
                best = (score, header)
    if best and best[0] >= minimum:
        return best[1]
    if required:
        raise InputDiscoveryError(
            f"Could not find a column matching any of: {', '.join(candidate_list)}"
        )
    return None


def read_csv_file(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "utf-16"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                sample = handle.read(4096)
                handle.seek(0)
                counts = {",": sample.count(","), ";": sample.count(";"), "\t": sample.count("\t")}
                delimiter = max(counts, key=counts.get)
                lines = handle.read().splitlines()
                handle.seek(0)
                start = 0
                while start < len(lines) - 1:
                    width = len(next(csv.reader([lines[start]], delimiter=delimiter)))
                    if width > 1:
                        break
                    later_is_table = any(
                        len(next(csv.reader([line], delimiter=delimiter))) > 1
                        for line in lines[start + 1 :]
                    )
                    if not later_is_table:
                        break
                    start += 1
                reader = csv.DictReader(lines[start:], delimiter=delimiter)
                headers = list(reader.fieldnames or [])
                rows = [
                    {str(key): (value or "").strip() for key, value in row.items() if key is not None}
                    for row in reader
                    if any((value or "").strip() for value in row.values())
                ]
            if not headers:
                raise InputDiscoveryError(f"{path.name} has no header row.")
            return headers, rows
        except UnicodeError as exc:
            last_error = exc
    raise InputDiscoveryError(f"Could not read {path.name}: {last_error}")


def csv_kind(headers: list[str]) -> tuple[int, int]:
    normalized = [normalize(header) for header in headers]
    attendance = 0
    diary = 0
    if sum(
        bool(re.search(r"\b(?:session|mtg|meeting|visit|class|week|wk|s)\s*\d+\b", item))
        or bool(re.search(r"\b(?:week|session|visit|class)\s+(?:one|two|three|four)\b", item))
        for item in normalized
    ) >= 2:
        attendance += 5
    if sum(
        any(
            token in item
            for token in (
                "money check",
                "assessment",
                "baseline score",
                "midpoint score",
                "follow up score",
                "outcome score",
            )
        )
        or bool(re.fullmatch(r"check [a-z0-9]+", item))
        or bool(re.fullmatch(r"\d+(?:st|nd|rd|th)?(?: money)? check", item))
        for item in normalized
    ) >= 2:
        attendance += 4
    if any(
        token in item
        for item in normalized
        for token in ("preferred contact", "preferred route", "reach by", "contact method")
    ):
        attendance += 2
    if any(
        item in {"client id", "participant id", "member id", "case id", "no", "number"}
        for item in normalized
    ):
        attendance += 2
    if any(item in {"client", "participant", "member", "learner", "full name", "name"} for item in normalized):
        attendance += 1

    if any(
        item in {"week", "week no", "week number", "diary week", "homework week", "date"}
        for item in normalized
    ):
        diary += 4
    if any(
        item in {"in", "in?", "handed in"}
        or any(
            token in item
            for token in (
                "handed in",
                "returned",
                "submitted",
                "diary complete",
                "homework complete",
                "days done",
                "days filled",
                "amount noted",
                "dollars",
            )
        )
        for item in normalized
    ):
        diary += 4
    return attendance, diary


def discover_files(folder: Path, agency_hint: str | None = None) -> InputFiles:
    if not folder.exists() or not folder.is_dir():
        raise InputDiscoveryError(f"Input folder does not exist: {folder}")

    all_files = [path for path in folder.rglob("*") if path.is_file() and not path.name.startswith(".")]
    csv_paths = [
        path
        for path in all_files
        if path.suffix.casefold() == ".csv"
        if path.name.casefold() != "results.csv" and not path.name.startswith(".")
    ]
    txt_paths = [path for path in all_files if path.suffix.casefold() == ".txt"]
    if agency_hint:
        hint = compact(agency_hint)
        hinted_csv = [path for path in csv_paths if hint in compact(path.stem)]
        hinted_txt = [path for path in txt_paths if hint in compact(path.stem)]
        if hinted_csv:
            csv_paths = hinted_csv
        if hinted_txt:
            txt_paths = hinted_txt

    attendance_candidates: list[tuple[int, Path]] = []
    diary_candidates: list[tuple[int, Path]] = []
    for path in csv_paths:
        try:
            headers, _ = read_csv_file(path)
        except InputDiscoveryError:
            continue
        attendance_score, diary_score = csv_kind(headers)
        if attendance_score >= 5 and attendance_score > diary_score:
            name_bonus = 3 if "attend" in normalize(path.stem) else 0
            attendance_candidates.append((attendance_score + name_bonus, path))
        if diary_score >= 5 and diary_score > attendance_score:
            name_bonus = 3 if "diar" in normalize(path.stem) else 0
            diary_candidates.append((diary_score + name_bonus, path))

    if not attendance_candidates:
        raise InputDiscoveryError("Could not identify an attendance CSV.")
    attendance_candidates.sort(key=lambda item: (-item[0], str(item[1])))
    if (
        len(attendance_candidates) > 1
        and attendance_candidates[0][0] == attendance_candidates[1][0]
        and not agency_hint
    ):
        names = ", ".join(path.name for _, path in attendance_candidates[:3])
        raise InputDiscoveryError(
            f"More than one attendance file matched ({names}). Use --agency to select one."
        )
    attendance = attendance_candidates[0][1]

    if not txt_paths:
        raise NotesUnreadableError("Notes file is missing.")

    attendance_prefix = agency_prefix(attendance.stem)
    if diary_candidates:
        diary_candidates.sort(
            key=lambda item: (
                -(item[0] + (4 if attendance_prefix and attendance_prefix in normalize(item[1].stem) else 0)),
                str(item[1]),
            )
        )
        if (
            len(diary_candidates) > 1
            and diary_candidates[0][0] == diary_candidates[1][0]
            and not agency_hint
        ):
            names = ", ".join(path.name for _, path in diary_candidates[:3])
            raise InputDiscoveryError(
                f"More than one diary file matched ({names})."
            )
        diaries = diary_candidates[0][1]
    else:
        raise InputDiscoveryError("Could not identify a diaries CSV.")

    def notes_score(path: Path) -> int:
        score = 5 if "note" in normalize(path.stem) else 0
        if attendance_prefix and attendance_prefix in normalize(path.stem):
            score += 4
        try:
            sample = read_notes_text(path)
        except NotesUnreadableError:
            return score
        lines = [line for line in sample.splitlines() if line.strip()]
        score += min(
            8,
            sum(bool(re.search(DATE_TOKEN, line, flags=re.IGNORECASE)) for line in lines),
        )
        score += min(4, sum(":" in line or "|" in line for line in lines))
        return score

    notes_ranked = sorted(txt_paths, key=lambda path: (-notes_score(path), str(path)))
    notes = notes_ranked[0]
    return InputFiles(attendance=attendance, diaries=diaries, notes=notes)


def agency_prefix(stem: str) -> str:
    text = normalize(stem)
    removable = {
        "attendance",
        "attend",
        "register",
        "roster",
        "clients",
        "client",
        "data",
        "sheet",
        "records",
        "export",
        "input",
        "inputs",
        "report",
        "diaries",
        "diary",
        "counsellor",
        "counselor",
        "notes",
    }
    return " ".join(word for word in text.split() if word not in removable)


def derive_agency_name(
    attendance_path: Path,
    folder: Path,
    fallback: str | None = None,
) -> str:
    prefix = agency_prefix(attendance_path.stem)
    if not prefix:
        source_folder = (
            attendance_path.parent
            if attendance_path.parent.resolve() != folder.resolve()
            else folder
        )
        prefix = normalize(source_folder.name)
    if prefix in {"input", "inputs", "upload", "uploads", "data"} and fallback:
        prefix = agency_prefix(Path(fallback).stem)
    if not prefix:
        raise InputDiscoveryError("Could not derive the agency name.")
    return " ".join(word.capitalize() for word in prefix.split())


def numbered_columns(headers: list[str], kind: str) -> list[str]:
    found: list[tuple[int, int, str]] = []
    for position, header in enumerate(headers):
        value = normalize(header)
        if kind == "session":
            patterns = (
                r"^(?:s|session|mtg|meeting|visit|class|week|wk)\s*(\d+)$",
                r"^(?:week|session|visit|class|mtg)\s+(one|two|three|four)$",
                r"^(?:attendance)\s*(\d+)$",
            )
        else:
            patterns = (
                r"^(?:money\s*)?check\s*(?:s|session)?\s*(\d+|[a-z])$",
                r"^(?:score|assessment)\s*(?:s|session)?\s*(\d+|[a-z])$",
                r"^money check (?:s|session)\s*(\d+)$",
                r"^(baseline|initial|first)(?: money check)? score$",
                r"^(midpoint|mid point|halfway|second)(?: money check)? score$",
                r"^(final|follow up|third)(?: money check)? score$",
                r"^(first|second|third) check$",
                r"^check (one|two|three)$",
                r"^(?:money )?check (one|two|three)$",
                r"^(\d+)(?:st|nd|rd|th)?(?: money)? check$",
            )
        for pattern in patterns:
            match = re.match(pattern, value)
            if match:
                token = match.group(1)
                semantic_order = {
                    "baseline": 1,
                    "initial": 1,
                    "first": 1,
                    "midpoint": 4,
                    "mid point": 4,
                    "halfway": 4,
                    "second": 4,
                    "final": 6,
                    "follow up": 6,
                    "third": 6,
                    "one": 1,
                    "two": 2,
                    "three": 3,
                    "four": 4,
                }
                order = (
                    int(token)
                    if token.isdigit()
                    else semantic_order.get(token, 100 + ord(token[0]))
                )
                found.append((order, position, header))
                break
    found.sort()
    return [header for _, _, header in found]


def load_clients(attendance_path: Path) -> tuple[list[Client], list[str]]:
    headers, rows = read_csv_file(attendance_path)
    id_column = next((header for header in headers if header_is_client_id(header)), None)
    if id_column is None:
        id_column = choose_column(
            headers,
            (
                "client_id",
                "client id",
                "participant id",
                "member id",
                "case id",
                "case number",
                "case no",
                "record id",
                "id",
                "no.",
                "number",
            ),
            required=True,
            minimum=0.68,
        )
    name_column = choose_column(
        headers,
        ("full_name", "full name", "client", "participant", "member", "learner", "name", "who"),
        required=True,
        skip_client_ids=True,
    )
    last_name_column = choose_column(
        headers, ("last name", "surname", "family name", "family"), minimum=0.93
    )
    counsellor_column = choose_column(
        headers, ("counsellor", "counselor", "staff", "worker", "advisor", "coach")
    )
    contact_column = choose_column(
        headers,
        (
            "preferred_contact",
            "preferred contact",
            "preferred route",
            "reach by",
            "how to reach",
            "preferred channel",
            "contact method",
            "contact",
        ),
    )
    session_columns = numbered_columns(headers, "session")
    score_columns = numbered_columns(headers, "score")

    if not session_columns:
        raise InputDiscoveryError("The attendance file has no recognizable session columns.")
    if len(score_columns) < 2:
        raise InputDiscoveryError(
            "The attendance file has fewer than two recognizable Money Check columns."
        )

    clients: list[Client] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        name = row.get(name_column or "", "").strip()
        given = set(normalize(name_column or "").split())
        if (
            last_name_column
            and last_name_column != name_column
            and given & {"first", "given", "forename"}
        ):
            name = " ".join(
                part
                for part in (name, row.get(last_name_column, "").strip())
                if part
            )
        if not name:
            raise InputDiscoveryError(f"Attendance row {index + 1} has no client name.")
        client_id = row.get(id_column or "", "").strip()
        if not client_id:
            raise InputDiscoveryError(f"Attendance row {index + 1} has no client ID.")
        if client_id in seen_ids:
            raise InputDiscoveryError(f"Duplicate client ID in attendance file: {client_id}")
        seen_ids.add(client_id)
        clients.append(
            Client(
                client_id=client_id,
                name=name,
                counsellor=row.get(counsellor_column or "", "").strip(),
                attendance_contact=row.get(contact_column or "", "").strip(),
                sessions=[row.get(column, "").strip() for column in session_columns],
                scores=[row.get(column, "").strip() for column in score_columns],
            )
        )
    if not clients:
        raise InputDiscoveryError("The attendance file contains no clients.")
    return clients, score_columns


def read_notes_text(path: Path) -> str:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "utf-16"):
        try:
            text = path.read_text(encoding=encoding)
        except UnicodeError as exc:
            last_error = exc
            continue
        printable = sum(ch.isprintable() or ch in "\r\n\t" for ch in text)
        if text.strip() and printable / max(len(text), 1) >= 0.85:
            return text
    if last_error is not None:
        raise NotesUnreadableError(f"Notes could not be decoded: {last_error}")
    raise NotesUnreadableError("Notes look like gibberish.")


DATE_TOKEN = (
    r"(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"
    r"|\d{1,2}[-/.]\d{1,2}[-/.]\d{4}"
    r"|(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?\s+of\s+[A-Za-z]{3,9}\.?\s+\d{4}"
    r"|(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\.?\s+\d{4}"
    r"|\d{1,2}[-/.][A-Za-z]{3,9}\.?[-/.]\d{4}"
    r"|[A-Za-z]{3,9}\.?\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s+\d{4})"
)


NUMERIC_DATE = re.compile(r"\b(\d{1,2})([/.-])(\d{1,2})\2(\d{4})\b")


def date_order_is_month_first(text: str) -> bool:
    """Use month-first only when this file proves it.

    A value such as 03/15/2026 can only be March 15. A value such as
    15/03/2026 can only be 15 March. If both clues appear, or neither
    does, ambiguous values stay day-first: 03/11/2026 is 3 November.
    """
    month_only = False
    day_only = False
    for match in NUMERIC_DATE.finditer(text):
        first = int(match.group(1))
        second = int(match.group(3))
        if first > 12 and second <= 12:
            day_only = True
        elif second > 12 and first <= 12:
            month_only = True
    return month_only and not day_only


def parse_date(value: str, *, month_first: bool = False) -> date | None:
    cleaned = value.strip().strip("[]()").replace(",", " ")
    cleaned = re.sub(r"\b([A-Za-z]{3,9})\.", r"\1", cleaned)
    cleaned = re.sub(r"^(?:the)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bof\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.split())
    day_first_formats = ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y")
    month_first_formats = ("%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y")
    numeric_formats = (
        month_first_formats + day_first_formats
        if month_first
        else day_first_formats + month_first_formats
    )
    for format_string in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        *numeric_formats,
        "%d %b %Y",
        "%d %B %Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d/%b/%Y",
        "%d/%B/%Y",
        "%d.%b.%Y",
        "%d.%B.%Y",
        "%b %d %Y",
        "%B %d %Y",
    ):
        try:
            return datetime.strptime(cleaned, format_string).date()
        except ValueError:
            pass
    return None


def parse_note_line(line: str, *, month_first: bool = False) -> Note | None:
    stripped = line.strip()
    if not stripped:
        return None

    labelled_date = re.search(rf"\bdate\s*[:=]\s*(?P<date>{DATE_TOKEN})", stripped, flags=re.IGNORECASE)
    labelled_person = re.search(
        r"\b(?:client|person|name)\s*[:=]\s*(?P<person>.+?)"
        r"(?=\s+\b(?:date|note|details?|messages?|updates?|comments?|entr(?:y|ies)|remarks?|staff|counsellor|counselor|worker)\b\s*[:=]|$)",
        stripped,
        flags=re.IGNORECASE,
    )
    labelled_body = re.search(
        r"\b(?:note|details?|messages?|updates?|comments?|entr(?:y|ies)|remarks?)\s*[:=]\s*(?P<body>.+)$",
        stripped,
        flags=re.IGNORECASE,
    )
    if labelled_date and labelled_person and labelled_body:
        labelled_counsellor = re.search(
            r"\b(?:staff|counsellor|counselor)\s*[:=]\s*(?P<counsellor>[^|;]+)",
            stripped,
            flags=re.IGNORECASE,
        )
        return Note(
            note_date=parse_date(labelled_date.group("date"), month_first=month_first),
            person_text=labelled_person.group("person").strip(),
            counsellor_text=(
                labelled_counsellor.group("counsellor").strip() if labelled_counsellor else ""
            ),
            body=labelled_body.group("body").strip(),
        )

    labelled = re.match(
        rf"^.*?\bdate\s*[:=]\s*(?P<date>{DATE_TOKEN}).*?"
        r"\b(?:client|person|name)\s*[:=]\s*(?P<person>[^|;]+).*?"
        r"(?:\b(?:staff|counsellor|counselor)\s*[:=]\s*(?P<counsellor>[^|;]+).*?)?"
        r"\b(?:note|details?|messages?|updates?|comments?|entr(?:y|ies)|remarks?)\s*[:=]\s*(?P<body>.+)$",
        stripped,
        flags=re.IGNORECASE,
    )
    if labelled:
        return Note(
            note_date=parse_date(labelled.group("date"), month_first=month_first),
            person_text=labelled.group("person").strip(),
            counsellor_text=(labelled.group("counsellor") or "").strip(),
            body=labelled.group("body").strip(),
        )

    cole = re.match(
        rf"^\[(?P<date>{DATE_TOKEN})\]\s*"
        r"(?P<counsellor>[^|:]+?)\s*\|\s*(?P<person>[^:]+?)\s*:\s*(?P<body>.+)$",
        stripped,
        flags=re.IGNORECASE,
    )
    if cole:
        return Note(
            note_date=parse_date(cole.group("date"), month_first=month_first),
            person_text=cole.group("person").strip(),
            counsellor_text=cole.group("counsellor").strip(),
            body=cole.group("body").strip(),
        )

    bayfield = re.match(
        rf"^(?P<person>[^(:]+?)\s*\((?P<date>{DATE_TOKEN})"
        r"(?:\s*,\s*(?P<counsellor>[^)]+))?\)\s*:\s*(?P<body>.+)$",
        stripped,
        flags=re.IGNORECASE,
    )
    if bayfield:
        return Note(
            note_date=parse_date(bayfield.group("date"), month_first=month_first),
            person_text=bayfield.group("person").strip(),
            counsellor_text=(bayfield.group("counsellor") or "").strip(),
            body=bayfield.group("body").strip(),
        )

    spaced_dash = re.match(
        rf"^(?P<person>.+?)\s+[—–-]\s+(?P<date>{DATE_TOKEN})\s+[—–-]\s+"
        r"(?:(?P<counsellor>[^—–\-|:]{1,40}?)\s+[—–-]\s+)?(?P<body>.+)$",
        stripped,
        flags=re.IGNORECASE,
    )
    if spaced_dash and parse_date(spaced_dash.group("date"), month_first=month_first):
        return Note(
            note_date=parse_date(spaced_dash.group("date"), month_first=month_first),
            person_text=spaced_dash.group("person").strip(),
            counsellor_text=(spaced_dash.group("counsellor") or "").strip(),
            body=spaced_dash.group("body").strip(),
        )

    if stripped.count("|") >= 2:
        parts = [part.strip() for part in stripped.split("|")]
        parsed_date = parse_date(parts[0], month_first=month_first)
        if parsed_date and len(parts) >= 4:
            return Note(
                note_date=parsed_date,
                person_text=parts[2],
                counsellor_text=parts[1],
                body=" | ".join(parts[3:]).strip(),
            )
        if parsed_date and len(parts) == 3:
            return Note(
                note_date=parsed_date,
                person_text=parts[1],
                counsellor_text="",
                body=parts[2],
            )

    dash_parts = [part.strip() for part in re.split(r"\s+[—–-]\s+", stripped) if part.strip()]
    if len(dash_parts) >= 3:
        parsed_date = parse_date(dash_parts[0], month_first=month_first)
        if parsed_date and len(dash_parts) >= 4:
            return Note(
                note_date=parsed_date,
                person_text=dash_parts[2],
                counsellor_text=dash_parts[1],
                body=" - ".join(dash_parts[3:]),
            )
        if parsed_date and len(dash_parts) == 3:
            return Note(
                note_date=parsed_date,
                person_text=dash_parts[1],
                counsellor_text="",
                body=dash_parts[2],
            )

    date_first_three = re.match(
        rf"^(?P<date>{DATE_TOKEN})\s*\|\s*"
        r"(?P<person>[^|:]+?)\s*:\s*(?P<body>.+)$",
        stripped,
        flags=re.IGNORECASE,
    )
    if date_first_three:
        return Note(
            note_date=parse_date(date_first_three.group("date"), month_first=month_first),
            person_text=date_first_three.group("person").strip(),
            counsellor_text="",
            body=date_first_three.group("body").strip(),
        )

    generic = re.match(
        r"^(?P<person>[A-Za-z][A-Za-z .'-]{0,60})\s*[:|]\s*(?P<body>.+)$",
        stripped,
    )
    if generic:
        return Note(
            note_date=None,
            person_text=generic.group("person").strip(),
            counsellor_text="",
            body=generic.group("body").strip(),
        )
    return None


def canonical_first(name: str) -> str:
    first = normalize(name).split()[0] if normalize(name) else ""
    return ALIASES.get(first, first)


def counsellor_matches(left: str, right: str) -> bool:
    if not left or not right:
        return True
    left_parts = normalize(left).split()
    right_parts = normalize(right).split()
    if set(left_parts) & set(right_parts):
        return True
    for short, full in ((left_parts, right_parts), (right_parts, left_parts)):
        if len(short) == 1 and len(short[0]) == 1 and any(part.startswith(short[0]) for part in full):
            return True
    return fuzzy_ratio(left, right) >= 0.65


NAME_CREDENTIALS = {"pt", "dpt", "rmt", "phd", "md", "rn", "ot", "lmt", "cpa", "msw", "rsw"}
NAME_TITLES = {"dr", "mr", "mrs", "ms", "miss", "mx"}
NAME_GENERATIONS = {"jr", "sr", "junior", "senior"}


def strip_titles_and_credentials(value: str) -> str:
    """Drop 'Dr.' and ', PT' so an initial can still match the attendance name.

    A comma that introduces a real given name, as in 'Lee, Pat', stays in place.
    """
    text = value.strip()
    if "," in text:
        left, _, right = text.partition(",")
        right_tokens = normalize(right).split()
        while right_tokens and right_tokens[-1] in NAME_GENERATIONS:
            right_tokens.pop()
        if right_tokens and all(token in NAME_CREDENTIALS for token in right_tokens):
            text = left.strip()
        else:
            text = f"{left.strip()}, {' '.join(right_tokens)}".strip().rstrip(",")
    if "," in text:
        return text
    tokens = normalize(text).split()
    while tokens and tokens[0] in NAME_TITLES:
        tokens.pop(0)
    while tokens and (tokens[-1] in NAME_CREDENTIALS or tokens[-1] in NAME_GENERATIONS):
        tokens.pop()
    return " ".join(tokens)


def reorder_personal_name(value: str) -> str:
    if "," in value:
        last, _, rest = value.partition(",")
        if rest.strip() and last.strip():
            return f"{rest.strip()} {last.strip()}"
    return value


def personal_tokens(value: str) -> list[str]:
    text = normalize(reorder_personal_name(strip_titles_and_credentials(value)))
    text = re.sub(r"\b([od]) ([a-z]{2,})", r"\1\2", text)
    text = re.sub(r"\b(mac|mc) ([a-z]{2,})", r"\1\2", text)
    return text.split()


def name_match_score(observed: str, canonical: str) -> float:
    observed_parts = personal_tokens(observed)
    canonical_parts = personal_tokens(canonical)
    if not observed_parts or not canonical_parts:
        return 0.0
    observed_first = ALIASES.get(observed_parts[0], observed_parts[0])
    canonical_first_name = ALIASES.get(canonical_parts[0], canonical_parts[0])
    initial_targets = {canonical_parts[0], canonical_first_name}
    if observed_first == canonical_first_name or observed_parts[0] == canonical_parts[0]:
        score = 0.78
    elif len(observed_parts[0]) == 1 and any(
        name.startswith(observed_parts[0]) for name in initial_targets
    ):
        score = 0.68
    elif fuzzy_ratio(observed_first, canonical_first_name) >= 0.78:
        score = 0.63
    else:
        return 0.0
    if normalize(observed) == normalize(canonical):
        return 1.0
    if len(observed_parts) > 1 and len(canonical_parts) > 1:
        observed_last = observed_parts[-1]
        canonical_last = canonical_parts[-1]
        if observed_last == canonical_last:
            score += 0.25
        elif len(observed_last) == 1 and canonical_last.startswith(observed_last):
            score += 0.2
        elif fuzzy_ratio(observed_last, canonical_last) >= 0.78:
            score += 0.16
        else:
            score -= 0.25
    return max(0.0, min(score, 1.0))


def absorb_parenthetical(person: str, counsellor: str) -> tuple[str, str]:
    match = re.fullmatch(r"(.+?)\s*\(([^)]+)\)", person.strip())
    if match is None:
        return person, counsellor
    name = match.group(1).strip()
    if counsellor:
        return name, counsellor
    return name, match.group(2).strip()


def match_client(
    person_text: str,
    counsellor_text: str,
    clients: list[Client],
) -> tuple[Client | None, bool]:
    person_text, counsellor_text = absorb_parenthetical(person_text, counsellor_text)
    token = compact(person_text)
    if token:
        id_hits = [client for client in clients if compact(client.client_id) == token]
        if len(id_hits) == 1:
            return id_hits[0], False
        if len(id_hits) > 1:
            return None, True

    scored: list[tuple[float, Client]] = []
    for client in clients:
        if not counsellor_matches(counsellor_text, client.counsellor):
            continue
        score = name_match_score(person_text, client.name)
        if score >= 0.68:
            scored.append((score, client))
    scored.sort(key=lambda item: (-item[0], item[1].client_id))
    if not scored:
        parts = personal_tokens(person_text)
        if len(parts) == 1 and parts[0]:
            last_hits = [
                client
                for client in clients
                if personal_tokens(client.name)[-1:] == parts
                and counsellor_matches(counsellor_text, client.counsellor)
            ]
            if len(last_hits) == 1:
                return last_hits[0], False
            if len(last_hits) > 1:
                return None, True
        return None, False
    if len(scored) > 1 and abs(scored[0][0] - scored[1][0]) < 0.08:
        return None, True
    return scored[0][1], False


def attach_notes(clients: list[Client], notes_path: Path, warnings: list[str]) -> list[date]:
    text = read_notes_text(notes_path)
    month_first = date_order_is_month_first(text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]

    def joined_block(block: str) -> str:
        return " | ".join(line.strip() for line in block.splitlines() if line.strip())

    def block_is_one_note(block: str) -> bool:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            return False
        if any(parse_note_line(line, month_first=month_first) is not None for line in lines):
            return False
        return parse_note_line(joined_block(block), month_first=month_first) is not None

    if len(blocks) > 1:
        records = [joined_block(block) if "\n" in block else block for block in blocks]
        record_label = "record"
    elif blocks and block_is_one_note(blocks[0]):
        records = [joined_block(blocks[0])]
        record_label = "record"
    else:
        records = [line.strip() for line in text.splitlines() if line.strip()]
        record_label = "line"
    if not records:
        raise NotesUnreadableError("Notes are empty.")

    parsed_count = 0
    matched_count = 0
    dated_count = 0
    dates: set[date] = set()
    for line_number, line in enumerate(records, start=1):
        note = parse_note_line(line, month_first=month_first)
        if note is None:
            warnings.append(f"Notes {record_label} {line_number} could not be parsed.")
            continue
        parsed_count += 1
        if note.note_date:
            dated_count += 1
        client, ambiguous = match_client(note.person_text, note.counsellor_text, clients)
        if ambiguous:
            warnings.append(
                f"Ambiguous client in notes line {line_number}: {note.person_text!r}."
            )
            matched_count += 1
            if note.note_date:
                dates.add(note.note_date)
            continue
        if client is None:
            warnings.append(
                f"No attendance match for notes line {line_number}: {note.person_text!r}."
            )
            continue
        client.notes.append(note)
        matched_count += 1
        if note.note_date:
            dates.add(note.note_date)

    readable_ratio = parsed_count / len(records)
    matched_ratio = matched_count / len(records)
    dated_ratio = dated_count / len(records)
    if readable_ratio < 0.5 or matched_ratio < 0.5 or dated_ratio < 0.5:
        raise NotesUnreadableError(
            f"Only {matched_count} of {len(records)} notes records could be understood."
        )
    for client in clients:
        client.notes.sort(key=lambda note: note.note_date or date.min)
    return sorted(dates)


def attach_diaries(
    clients: list[Client],
    diaries_path: Path | None,
    warnings: list[str],
) -> None:
    if diaries_path is None:
        warnings.append("No diary CSV was found.")
        return
    headers, rows = read_csv_file(diaries_path)
    person_column = choose_column(
        headers, ("client", "participant", "learner", "who", "name", "full name"), required=True
    )
    last_name_column = choose_column(
        headers, ("last name", "surname", "family name", "family"), minimum=0.93
    )
    counsellor_column = choose_column(
        headers, ("counsellor", "counselor", "staff", "worker", "advisor", "coach")
    )
    week_column = choose_column(headers, ("week", "week no", "week number"))
    date_column = choose_column(
        headers, ("date", "diary date", "week date", "session date"), minimum=0.72
    )
    handed_column = choose_column(
        headers,
        (
            "handed in",
            "returned",
            "in?",
            "in",
            "submitted",
            "diary complete",
            "homework complete",
            "completed",
            "done",
        ),
        required=True,
    )
    month_first = date_order_is_month_first(
        "\n".join(row.get(date_column or "", "") for row in rows)
    )

    for row_number, row in enumerate(rows, start=2):
        person = row.get(person_column or "", "").strip()
        given = set(normalize(person_column or "").split())
        if (
            last_name_column
            and last_name_column != person_column
            and given & {"first", "given", "forename"}
        ):
            person = " ".join(
                part
                for part in (person, row.get(last_name_column, "").strip())
                if part
            )
        counsellor = row.get(counsellor_column or "", "").strip()
        client, ambiguous = match_client(person, counsellor, clients)
        if ambiguous:
            warnings.append(f"Ambiguous client in diaries row {row_number}: {person!r}.")
            continue
        if client is None:
            warnings.append(f"No attendance match for diaries row {row_number}: {person!r}.")
            continue
        week_text = normalize(row.get(week_column or "", ""))
        week_match = re.search(r"\d+", week_text)
        week_words = {"one": 1, "two": 2, "three": 3, "four": 4}
        if week_match:
            week = int(week_match.group())
        else:
            week = week_words.get(week_text)
        client.diaries.append(
            DiaryEntry(
                week=week,
                entry_date=parse_date(row.get(date_column or "", ""), month_first=month_first),
                handed_in=row.get(handed_column or "", "").strip(),
                person_text=person,
                counsellor_text=counsellor,
            )
        )


def contains_pattern(text: str, patterns: Iterable[str]) -> bool:
    normalized = normalize(text)
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)


def note_date_for_week(week: int | None, note_dates: list[date]) -> date | None:
    if week is None or week < 1 or week > len(note_dates):
        return None
    return note_dates[week - 1]


def schedule_dates(clients: list[Client], note_dates: list[date]) -> list[date]:
    counts: dict[date, int] = {}
    for client in clients:
        for note_date in {note.note_date for note in client.notes if note.note_date}:
            counts[note_date] = counts.get(note_date, 0) + 1
    common = sorted(day for day, count in counts.items() if count >= 2)
    return common or note_dates


def aligned_dates(client: Client, index: int, schedule: list[date]) -> list[date]:
    targets: list[date] = []
    if 0 <= index < len(schedule):
        targets.append(schedule[index])
    client_dates = sorted({note.note_date for note in client.notes if note.note_date})
    if 0 <= index < len(client_dates) and client_dates[index] not in targets:
        primary = targets[0] if targets else None
        has_note_on_primary = any(note.note_date == primary for note in client.notes)
        if primary is None or not has_note_on_primary:
            targets.append(client_dates[index])
    return targets


def notes_for_date(client: Client, target: date | None) -> list[Note]:
    if target is None:
        return []
    return [note for note in client.notes if note.note_date == target]


def persistent_excuse(client: Client, target: date | None, patterns: Iterable[str]) -> bool:
    if target is None:
        return any(contains_pattern(note.body, patterns) for note in client.notes)
    for note in client.notes:
        if note.note_date and note.note_date <= target and contains_pattern(note.body, patterns):
            if "on hold" in normalize(note.body) or "away" in normalize(note.body):
                return True
    return False


def diary_excuse(client: Client, diary: DiaryEntry, note_dates: list[date]) -> tuple[bool, str]:
    if diary.entry_date:
        targets = [diary.entry_date]
    else:
        targets = aligned_dates(client, (diary.week or 1) - 1, note_dates)
    for target in targets:
        for note in notes_for_date(client, target):
            if contains_pattern(note.body, DIARY_EXCUSE_PATTERNS):
                body = normalize(note.body)
                if "on hold" in body:
                    return True, "Diary on hold"
                if "away" in body:
                    return True, "Away with notice"
                return True, "Diary was not set"
        if persistent_excuse(client, target, (r"\bon hold\b", r"\baway for work\b")):
            if any("away" in normalize(note.body) for note in client.notes):
                return True, "Away with notice"
            return True, "Diary on hold"
    return False, ""


def attendance_excuse(client: Client, session_index: int, note_dates: list[date]) -> tuple[bool, str]:
    for target in aligned_dates(client, session_index, note_dates):
        for note in notes_for_date(client, target):
            if contains_pattern(note.body, ATTENDANCE_EXCUSE_PATTERNS):
                return True, "Away with notice"

        for note in client.notes:
            if not note.note_date or note.note_date > target:
                continue
            body = normalize(note.body)
            if contains_pattern(body, ATTENDANCE_EXCUSE_PATTERNS):
                if note.note_date + timedelta(days=21) >= target:
                    return True, "Away with notice"
            month_day = f"{target.strftime('%b')} {target.day}"
            if month_day and normalize(month_day) in body:
                return True, "Away with notice"
    return False, ""


def classify_status(client: Client, note_dates: list[date]) -> tuple[str, str]:
    missed_sessions: list[int] = []
    excused_reasons: list[str] = []
    for index, raw_value in enumerate(client.sessions):
        value = normalize(raw_value)
        if value not in ABSENT_VALUES:
            continue
        excused, reason = attendance_excuse(client, index, note_dates)
        if excused:
            excused_reasons.append(reason)
        else:
            missed_sessions.append(index + 1)

    if len(missed_sessions) >= 2:
        first_two = missed_sessions[:2]
        return "stalled", f"Missed sessions {first_two[0]} and {first_two[1]}"

    missed_diaries = 0
    for diary in client.diaries:
        value = normalize(diary.handed_in)
        if not value or value in DIARY_YES_VALUES or value not in DIARY_NO_VALUES:
            continue
        excused, reason = diary_excuse(client, diary, note_dates)
        if excused:
            excused_reasons.append(reason)
        else:
            missed_diaries += 1

    if missed_diaries >= 2:
        return "stalled", "Missed two diaries"
    if "Away with notice" in excused_reasons:
        return "on track", "Away with notice"
    if "Diary on hold" in excused_reasons:
        return "on track", "Diary on hold"
    if "Diary was not set" in excused_reasons:
        return "on track", "Diary was not set"
    return "on track", "Attendance and diaries current"


def normalized_contact(value: str) -> str:
    contact = normalize(value)
    if contact in {"sms", "text", "text message", "mobile", "whatsapp", "imessage", "message"}:
        return "text"
    if contact in {"call", "phone", "telephone"}:
        return "call"
    if contact in {"paper", "letter", "mail", "post", "email", "e mail"}:
        return "paper"
    if contact in {"do not contact", "none", "no contact"}:
        return "do not contact"
    return "paper"


def channel_is_banned(text: str, channel: str) -> bool:
    if channel == "call":
        return bool(
            re.search(r"\b(?:no|don t|do not) (?:phone )?calls?\b", text)
            or re.search(r"\b(?:no|don t|do not) phones?\b", text)
            or re.search(r"\bno calling\b", text)
        )
    if channel == "text":
        return bool(
            re.search(r"\b(?:no|don t|do not) texts?(?: messages?)?\b", text)
            or re.search(r"\b(?:no|don t|do not) texting\b", text)
        )
    return bool(
        re.search(r"\b(?:no|don t|do not) (?:e ?mails?|mail|letters?|post)\b", text)
        or re.search(r"\b(?:no|don t|do not) write\b", text)
        or re.search(r"\bno mailing\b", text)
    )


def absolute_no_contact(body: str) -> bool:
    text = normalize(body)
    if contains_pattern(text, STOP_CONTACT_PATTERNS):
        return True
    return all(channel_is_banned(text, channel) for channel in ("call", "text", "paper"))


def instruction_in_text(text: str) -> str | None:
    if absolute_no_contact(text):
        return "do not contact"
    if re.search(r"\bplease text\b", text) or re.search(r"\b(?:ok|okay) to text\b", text):
        return "text"
    if re.search(r"\btext messages? only\b", text):
        return "text"
    if re.search(
        r"\b(?:whatsapp|sms|imessage|texting|texts?) (?:is |are )?(?:fine|ok|okay|preferred|only)\b",
        text,
    ):
        return "text"
    if re.search(r"\bplease (?:call|phone)\b", text) or re.search(
        r"\b(?:ok|okay) to (?:call|phone)\b", text
    ):
        return "call"
    if re.search(r"\bphone calls? only\b", text) or re.search(r"\bwrite only\b", text):
        return "call" if re.search(r"\bphone calls? only\b", text) else "paper"
    if re.search(r"\bgive (?:her|him|them) a call\b", text):
        return "call"
    if re.search(
        r"\b(?:calls?|phones?|calling) (?:is |are )?(?:fine|ok|okay|preferred|only)\b",
        text,
    ):
        return "call"
    if re.search(
        r"\b(?:e ?mails?) (?:is |are )?(?:fine|ok|okay|preferred|only)\b",
        text,
    ):
        return "paper"
    if re.search(r"\b(?:call|calling|phone|phoned)\b", text):
        if re.search(
            r"\b(?:call(?:ing)? (?:in the )?evenings?|wants? a call|phone(?:d)? not texted)\b",
            text,
        ):
            return "call"
    if re.search(
        r"\b(?:paper(?: notes?)?|letter|mail|post) (?:is |are )?(?:only|fine|ok|okay|preferred)\b",
        text,
    ):
        return "paper"
    if re.search(r"\bprefers? (?:a |an )?(?:texts?|sms|whatsapp)\b", text):
        return "text"
    if re.search(r"\bprefers? (?:a |an )?(?:calls?|phones?)\b", text):
        return "call"
    if re.search(r"\bprefers? (?:an? )?(?:e ?mails?|letters?|paper|post)\b", text):
        return "paper"
    return None


def instruction_from_piece(piece: str) -> str | None:
    clauses = [part.strip() for part in re.split(r"\s+[—–-]\s+", piece) if part.strip()]
    found = [
        instruction
        for clause in clauses
        for instruction in (instruction_in_text(normalize(clause)),)
        if instruction
    ]
    if found:
        return found[-1]
    return instruction_in_text(normalize(piece))


def note_contact_instruction(body: str) -> str | None:
    sentences = [part.strip() for part in re.split(r"[.;\n]+", str(body)) if part.strip()]
    found = [
        instruction
        for sentence in (sentences or [str(body)])
        for instruction in (instruction_from_piece(sentence),)
        if instruction
    ]
    if found:
        return found[-1]
    return instruction_in_text(normalize(body))


def classify_contact(client: Client) -> str:
    ordered = sorted(
        enumerate(client.notes),
        key=lambda item: (item[1].note_date or date.min, item[0]),
        reverse=True,
    )
    for _, note in ordered:
        instruction = note_contact_instruction(note.body)
        if instruction:
            return instruction
    return normalized_contact(client.attendance_contact)


def safe_number(value: str) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", value)
    if match is None:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def money_check_counts(clients: list[Client]) -> tuple[int, int]:
    completed = 0
    improved = 0
    for client in clients:
        if len(client.scores) < 2:
            continue
        first = safe_number(client.scores[0])
        second = safe_number(client.scores[1])
        if first is None or second is None:
            continue
        completed += 1
        if second > first:
            improved += 1
    return completed, improved


def build_results_csv(results: list[ClientResult]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=["client_id", "status", "way_to_reach", "why"], lineterminator="\n"
    )
    writer.writeheader()
    for result in results:
        writer.writerow(
            {
                "client_id": result.client_id,
                "status": result.status,
                "way_to_reach": result.way_to_reach,
                "why": result.why,
            }
        )
    return stream.getvalue()


def build_summary(
    agency_name: str, total_clients: int, completed_both: int, improved: int
) -> str:
    return (
        f"- Agency Name: {agency_name}\n"
        f"- Total Clients: {total_clients}\n"
        f"- Number of Clients Who Started: {total_clients}\n"
        f"- Completed Both Money Checks: {completed_both}\n"
        f"- Improved: {improved}\n"
        '- Definition of Improved: "A client who completed both Money Checks and increased '
        'their score from the first to the second."\n'
        '- Note: "This is a halfway view. Final scores are not yet available."\n'
    )


def publish_outputs(
    output_folder: Path,
    csv_content: str,
    summary_content: str,
) -> tuple[Path, Path]:
    output_folder.mkdir(parents=True, exist_ok=True)
    results_path = output_folder / "results.csv"
    summary_path = output_folder / "summary.md"
    targets = (results_path, summary_path)
    backups = {path: path.read_bytes() if path.exists() else None for path in targets}

    with tempfile.TemporaryDirectory(prefix=".steady-money-", dir=output_folder) as temporary:
        stage = Path(temporary)
        staged_results = stage / "results.csv"
        staged_summary = stage / "summary.md"
        staged_results.write_text(csv_content, encoding="utf-8", newline="")
        staged_summary.write_text(summary_content, encoding="utf-8")
        try:
            os.replace(staged_results, results_path)
            os.replace(staged_summary, summary_path)
        except OSError:
            for target, previous in backups.items():
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(previous)
            raise
    return results_path, summary_path


def process_folder(
    folder: str | Path,
    *,
    output_dir: str | Path | None = None,
    agency_hint: str | None = None,
    agency_name_fallback: str | None = None,
    announce: Callable[[str], None] | None = None,
) -> ReportResult:
    input_folder = Path(folder).resolve()
    output_folder = Path(output_dir).resolve() if output_dir else input_folder
    inputs = discover_files(input_folder, agency_hint=agency_hint)
    clients, _ = load_clients(inputs.attendance)
    agency_name = derive_agency_name(
        inputs.attendance,
        input_folder,
        fallback=agency_name_fallback,
    )

    if announce:
        announce(f"Agency Name: {agency_name}")
        announce(f"Total Clients: {len(clients)}")

    warnings: list[str] = []
    note_dates = schedule_dates(clients, attach_notes(clients, inputs.notes, warnings))
    attach_diaries(clients, inputs.diaries, warnings)

    client_results: list[ClientResult] = []
    for client in clients:
        status, why = classify_status(client, note_dates)
        contact = classify_contact(client)
        client_results.append(
            ClientResult(
                client_id=client.client_id,
                status=status,
                way_to_reach=contact,
                why=why,
            )
        )

    completed_both, improved = money_check_counts(clients)
    csv_content = build_results_csv(client_results)
    summary_content = build_summary(
        agency_name, len(clients), completed_both, improved
    )

    results_path, summary_path = publish_outputs(
        output_folder,
        csv_content,
        summary_content,
    )

    return ReportResult(
        agency_name=agency_name,
        total_clients=len(clients),
        completed_both=completed_both,
        improved=improved,
        clients=client_results,
        warnings=warnings,
        results_path=results_path,
        summary_path=summary_path,
    )
