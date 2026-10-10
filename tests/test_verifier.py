from __future__ import annotations

import unittest

from faultline.verifier import verify_evidence


class VerifierTests(unittest.TestCase):
    def test_verifies_two_independent_signals(self) -> None:
        result = verify_evidence({"service": "checkout", "signal_types": ["metrics", "traces"]})

        self.assertTrue(result["verified"])
        self.assertEqual(result["service"], "checkout")
        self.assertEqual(result["independent_signal_types"], ["metrics", "traces"])

    def test_rejects_change_only_evidence(self) -> None:
        result = verify_evidence({"service": "checkout", "signal_types": ["changes"]})

        self.assertFalse(result["verified"])
        self.assertEqual(result["independent_signal_types"], [])
        self.assertIn("need 2", result["reason"])

    def test_rejects_single_signal(self) -> None:
        result = verify_evidence({"service": "payment", "signal_types": ["logs"]})

        self.assertFalse(result["verified"])
        self.assertEqual(result["independent_signal_types"], ["logs"])


if __name__ == "__main__":
    unittest.main()
