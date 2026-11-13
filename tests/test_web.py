from __future__ import annotations

import io
import re
import unittest
from pathlib import Path

from app import app


ROOT = Path(__file__).resolve().parents[1]


def sample_upload(prefix: str) -> dict[str, tuple[io.BytesIO, str]]:
    return {
        "attendance": (
            io.BytesIO((ROOT / f"{prefix}-attendance.csv").read_bytes()),
            f"{prefix}-attendance.csv",
        ),
        "diaries": (
            io.BytesIO((ROOT / f"{prefix}-diaries.csv").read_bytes()),
            f"{prefix}-diaries.csv",
        ),
        "notes": (
            io.BytesIO((ROOT / f"{prefix}-counsellor-notes.txt").read_bytes()),
            f"{prefix}-counsellor-notes.txt",
        ),
    }


class FlaskAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_upload_page_has_required_form(self) -> None:
        response = self.client.get("/")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Steady Money - Impact Reporter", page)
        self.assertIn('name="attendance"', page)
        self.assertIn('name="diaries"', page)
        self.assertIn('name="notes"', page)
        self.assertIn("Process Data", page)

    def test_bayfield_web_results_and_downloads(self) -> None:
        response = self.client.post(
            "/process",
            data=sample_upload("bayfield"),
            content_type="multipart/form-data",
        )
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("<h1>Agency Name: Bayfield</h1>", page)
        self.assertIn("<strong>Total Clients: 6</strong>", page)
        self.assertIn("Number of Clients Who Started: 6", page)
        self.assertIn("This is a halfway view.", page)
        self.assertLess(page.index("Agency Summary"), page.index("Client List"))
        self.assertRegex(
            page,
            r"<td>B12</td>\s*<td>on track</td>\s*<td>paper</td>",
        )
        self.assertRegex(
            page,
            r"<td>B15</td>\s*<td>stalled</td>\s*<td>do not contact</td>",
        )

        token = re.search(r"/download/([a-f0-9]+)/results\.csv", page)
        self.assertIsNotNone(token)
        results_response = self.client.get(f"/download/{token.group(1)}/results.csv")
        summary_response = self.client.get(f"/download/{token.group(1)}/summary.md")
        self.assertEqual(results_response.status_code, 200)
        self.assertEqual(
            results_response.get_data(as_text=True).splitlines()[0],
            "client_id,status,way_to_reach,why",
        )
        self.assertIn("- Agency Name: Bayfield", summary_response.get_data(as_text=True))

    def test_cole_street_web_acceptance_cases(self) -> None:
        response = self.client.post(
            "/process",
            data=sample_upload("cole-street"),
            content_type="multipart/form-data",
        )
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        expected_rows = (
            ("C-1100", "stalled", "text"),
            ("C-1111", "on track", "text"),
            ("C-1127", "stalled", "do not contact"),
            ("C-1133", "on track", "do not contact"),
        )
        for client_id, status, contact in expected_rows:
            self.assertRegex(
                page,
                rf"<td>{client_id}</td>\s*<td>{status}</td>\s*<td>{contact}</td>",
            )

    def test_bad_notes_show_exact_error_without_downloads(self) -> None:
        uploads = sample_upload("bayfield")
        uploads["notes"] = (
            io.BytesIO(b"\x00\x01\x02 unreadable"),
            "bayfield-notes.txt",
        )

        response = self.client.post(
            "/process",
            data=uploads,
            content_type="multipart/form-data",
        )
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 400)
        self.assertIn("ERROR: Cannot read notes. Halting.", page)
        self.assertNotIn("Download results.csv", page)
        self.assertNotIn("Download summary.md", page)


if __name__ == "__main__":
    unittest.main()
