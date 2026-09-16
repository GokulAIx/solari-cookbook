import unittest

from app.experiment import SCENARIOS, classify_result


class ClassificationTests(unittest.TestCase):
    def test_supported_scenarios_are_explicit(self) -> None:
        self.assertEqual(
            SCENARIOS,
            {"none", "ui_mutation", "network_failure", "session_expiration"},
        )

    def test_control_success(self) -> None:
        self.assertEqual(
            classify_result(claimed_success=True, verified=True, scenario="none"),
            "SUCCESS",
        )

    def test_chaos_recovery(self) -> None:
        self.assertEqual(
            classify_result(claimed_success=True, verified=True, scenario="ui_mutation"),
            "RECOVERED",
        )

    def test_false_success(self) -> None:
        self.assertEqual(
            classify_result(claimed_success=True, verified=False, scenario="none"),
            "FALSE SUCCESS",
        )

    def test_failure_and_uncertainty(self) -> None:
        self.assertEqual(
            classify_result(claimed_success=False, verified=False, scenario="none"),
            "FAILURE",
        )
        self.assertEqual(
            classify_result(claimed_success=False, verified=True, scenario="none"),
            "UNCERTAIN",
        )


if __name__ == "__main__":
    unittest.main()