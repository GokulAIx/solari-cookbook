import tempfile
import unittest
from pathlib import Path

from app.storage import get_report, save_report


class StorageTests(unittest.TestCase):
    def test_report_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "runs.db")
            report = {
                "scenario": "ui_mutation",
                "classification": "RECOVERED",
                "events": [],
            }
            run_id = save_report(report, database)
            loaded = get_report(run_id, database)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["classification"], "RECOVERED")

    def test_missing_database_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "missing.db")
            self.assertIsNone(get_report("missing", database))


if __name__ == "__main__":
    unittest.main()
