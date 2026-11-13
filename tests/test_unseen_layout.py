from __future__ import annotations

import csv
import re
import tempfile
import unittest
from pathlib import Path

from steady_money.reporter import process_folder


ROOT = Path(__file__).resolve().parents[1]

ATTENDANCE_VALUES = {
    "present": "showed",
    "p": "showed",
    "late": "late arrival",
    "a": "missed",
    "absent": "missed",
    "no show": "missed",
}
DIARY_VALUES = {"yes": "returned", "no": "not returned"}
PEOPLE = {
    "carol": "C. Ingram",
    "theo": "T. Banks",
    "amina": "A. Yusuf",
    "stan": "S. Rudolph",
    "beth": "B. Oakley",
    "jude": "J. Levy",
}
COUNSELLORS = {"ida": "I. Marsh", "cam": "C. Lowe"}


def rewrite_note(line: str) -> str:
    match = re.match(
        r"^(?P<person>[^(:]+?)\s*\((?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
        r"\s*,\s*(?P<counsellor>[^)]+)\)\s*:\s*(?P<body>.+)$",
        line.strip(),
    )
    if match is None:
        return line
    person = PEOPLE.get(match.group("person").strip().casefold(), match.group("person").strip())
    counsellor = COUNSELLORS.get(
        match.group("counsellor").strip().casefold(),
        match.group("counsellor").strip(),
    )
    month_name = {
        "10": "October",
        "11": "November",
    }[match.group("month")]
    return (
        f"{month_name} {int(match.group('day'))}, {match.group('year')} | "
        f"{counsellor} | {person} | Seen in Halifax. {match.group('body').strip()}"
    )


class UnseenLayoutTests(unittest.TestCase):
    def test_renamed_halifax_style_files_keep_bayfield_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "original"
            mutated = base / "harbour-hill"
            outputs = base / "outputs"
            source.mkdir()
            mutated.mkdir()
            for name in (
                "bayfield-attendance.csv",
                "bayfield-diaries.csv",
                "bayfield-counsellor-notes.txt",
            ):
                (source / name).write_bytes((ROOT / name).read_bytes())

            original = process_folder(source, output_dir=base / "original-output")

            with (source / "bayfield-attendance.csv").open(encoding="utf-8-sig", newline="") as handle:
                attendance = list(csv.DictReader(handle))
            with (mutated / "harbour-hill-roster.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "Case Number",
                        "Participant",
                        "Worker",
                        "Mobile",
                        "Preferred Route",
                        "Session 1",
                        "Session 2",
                        "Session 3",
                        "Session 4",
                        "First Score",
                        "Second Score",
                    ],
                )
                writer.writeheader()
                for row in attendance:
                    writer.writerow(
                        {
                            "Case Number": row["No."],
                            "Participant": row["Client"],
                            "Worker": row["Staff"],
                            "Mobile": row["Mobile"],
                            "Preferred Route": row["Reach by"],
                            "Session 1": ATTENDANCE_VALUES.get(row["Mtg 1"].casefold(), row["Mtg 1"]),
                            "Session 2": ATTENDANCE_VALUES.get(row["Mtg 2"].casefold(), row["Mtg 2"]),
                            "Session 3": ATTENDANCE_VALUES.get(row["Mtg 3"].casefold(), row["Mtg 3"]),
                            "Session 4": ATTENDANCE_VALUES.get(row["Mtg 4"].casefold(), row["Mtg 4"]),
                            "First Score": row["Check A"],
                            "Second Score": row["Check B"],
                        }
                    )

            with (source / "bayfield-diaries.csv").open(encoding="utf-8-sig", newline="") as handle:
                diaries = list(csv.DictReader(handle))
            with (mutated / "harbour-hill-weekly-pages.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["Participant", "Worker", "Week Number", "Returned", "Days Recorded", "Amount"],
                )
                writer.writeheader()
                for row in diaries:
                    writer.writerow(
                        {
                            "Participant": row["Who"],
                            "Worker": row["Staff"],
                            "Week Number": row["Week no"],
                            "Returned": DIARY_VALUES.get(row["In?"].casefold(), row["In?"]),
                            "Days Recorded": row["Days done"],
                            "Amount": row["Dollars"],
                        }
                    )

            notes = (source / "bayfield-counsellor-notes.txt").read_text(encoding="utf-8")
            rewritten = "\n".join(rewrite_note(line) for line in notes.splitlines() if line.strip())
            rewritten += (
                "\nOctober 20, 2026 | C. Lowe | Alex | "
                "Asked us not to reach out: no calls, no texts, no mail.\n"
            )
            (mutated / "harbour-hill-session-log.txt").write_text(rewritten, encoding="utf-8")

            report = process_folder(mutated, output_dir=outputs)
            actual = {row.client_id: (row.status, row.way_to_reach) for row in report.clients}
            expected = {row.client_id: (row.status, row.way_to_reach) for row in original.clients}

            self.assertEqual(report.agency_name, "Harbour Hill")
            self.assertEqual(report.total_clients, original.total_clients)
            self.assertEqual(actual, expected)
            self.assertTrue(any("Alex" in warning for warning in report.warnings))
            self.assertNotIn("Alex", report.summary_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
