from __future__ import annotations

import unittest

from faultline.eval import score_diagnosis, summarize_scores


class EvalTests(unittest.TestCase):
    def test_scores_correct_verified_prediction(self) -> None:
        case = {"case_id": "payment", "ground_truth": {"root_service": "payment"}}
        diagnosis = {
            "conclusion": {
                "root_service": "payment",
                "confidence": "medium",
                "verification": {"verified": True},
            }
        }

        score = score_diagnosis(case, diagnosis)

        self.assertTrue(score["correct"])
        self.assertTrue(score["verified"])
        self.assertFalse(score["abstained"])

    def test_scores_abstention(self) -> None:
        case = {"case_id": "payment", "ground_truth": {"root_service": "payment"}}
        diagnosis = {
            "conclusion": {
                "root_service": None,
                "confidence": "abstain",
                "verification": {"verified": False},
            }
        }

        score = score_diagnosis(case, diagnosis)

        self.assertFalse(score["correct"])
        self.assertTrue(score["abstained"])

    def test_summarizes_accuracy_on_attempted(self) -> None:
        summary = summarize_scores(
            [
                {"correct": True, "abstained": False, "verified": True},
                {"correct": False, "abstained": False, "verified": False},
                {"correct": False, "abstained": True, "verified": False},
            ]
        )

        self.assertEqual(summary["cases"], 3)
        self.assertEqual(summary["attempted"], 2)
        self.assertEqual(summary["abstained"], 1)
        self.assertEqual(summary["accuracy_on_attempted"], 0.5)


if __name__ == "__main__":
    unittest.main()
