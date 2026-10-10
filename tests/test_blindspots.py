from __future__ import annotations

import unittest

from faultline.blindspots import detect_blind_spots


class BlindSpotTests(unittest.TestCase):
    def test_recommends_missing_signal_patches_for_seen_service(self) -> None:
        report = {
            "misses": [
                {
                    "case_id": "payment-failure-100-01",
                    "expected_root_service": "payment",
                    "expected_seen": True,
                    "expected_missing_signal_types": ["logs", "traces"],
                }
            ]
        }

        blind_spots = detect_blind_spots(report)

        self.assertEqual([item["missing_signal_type"] for item in blind_spots], ["logs", "traces"])
        self.assertTrue(all(item["service"] == "payment" for item in blind_spots))
        self.assertTrue(all(item["severity"] == "medium" for item in blind_spots))
        self.assertIn("src/payment", blind_spots[0]["candidate_patch_targets"][0])
        self.assertIn("scripts/telemetry.py", blind_spots[0]["validation_query"])

    def test_marks_unseen_expected_service_as_high_severity(self) -> None:
        report = {
            "misses": [
                {
                    "case_id": "cart-failure-100-01",
                    "expected_root_service": "cart",
                    "expected_seen": False,
                    "expected_missing_signal_types": ["logs", "metrics", "traces"],
                }
            ]
        }

        blind_spots = detect_blind_spots(report)

        self.assertEqual(len(blind_spots), 1)
        self.assertEqual(blind_spots[0]["severity"], "high")
        self.assertEqual(blind_spots[0]["service"], "cart")
        self.assertIn("did not appear", blind_spots[0]["gap"])
        self.assertEqual(blind_spots[0]["candidate_patch_targets"], ["src/cart"])

    def test_reports_ranking_ambiguity_when_expected_service_is_verified(self) -> None:
        report = {
            "misses": [
                {
                    "case_id": "payment-failure-100-01",
                    "expected_root_service": "payment",
                    "predicted_root_service": "checkout",
                    "expected_seen": True,
                    "expected_signal_types": ["metrics", "traces"],
                    "expected_missing_signal_types": ["logs"],
                    "expected_score": 87.5,
                    "predicted_score": 138.5,
                }
            ]
        }

        blind_spots = detect_blind_spots(report)

        self.assertEqual(blind_spots[0]["candidate_patch_targets"], ["faultline/agent.py"])
        self.assertEqual(blind_spots[0]["predicted_service"], "checkout")
        self.assertIn("lost the ranking", blind_spots[0]["gap"])


if __name__ == "__main__":
    unittest.main()
