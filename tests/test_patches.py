from __future__ import annotations

import unittest

from faultline.patches import build_patch_plan


class PatchPlanTests(unittest.TestCase):
    def test_builds_instrumentation_plan_from_log_blind_spot(self) -> None:
        analysis = {
            "run_dir": "results/eval-runs/example",
            "blind_spots": [
                {
                    "case_id": "payment-failure-100-01",
                    "service": "payment",
                    "severity": "medium",
                    "missing_signal_type": "logs",
                    "gap": "payment did not emit searchable error logs",
                    "candidate_patch_targets": ["src/payment/index.js", "src/payment/logger.js"],
                    "validation": "rerun the case and confirm payment has logs evidence",
                    "validation_query": "python3 scripts/telemetry.py search-logs --text payment --size 10",
                }
            ],
        }

        plan = build_patch_plan(analysis)

        self.assertEqual(plan["run_dir"], "results/eval-runs/example")
        self.assertEqual(plan["plans"][0]["kind"], "instrumentation_logs")
        self.assertEqual(plan["plans"][0]["service"], "payment")
        self.assertIn("OpenSearch", plan["plans"][0]["objective"])
        self.assertIn("src/payment/index.js", plan["plans"][0]["target_files"])
        self.assertIn("validation_query", plan["plans"][0])

    def test_builds_agent_ranking_plan_from_ranking_blind_spot(self) -> None:
        analysis = {
            "blind_spots": [
                {
                    "case_id": "payment-failure-100-01",
                    "service": "payment",
                    "predicted_service": "checkout",
                    "severity": "medium",
                    "gap": "payment lost the ranking to checkout",
                    "candidate_patch_targets": ["faultline/agent.py"],
                    "validation": "rerun the case and confirm payment outranks checkout",
                }
            ],
        }

        plan = build_patch_plan(analysis)

        self.assertEqual(plan["plans"][0]["kind"], "agent_ranking")
        self.assertEqual(plan["plans"][0]["target_files"], ["faultline/agent.py"])
        self.assertIn("downstream", " ".join(plan["plans"][0]["steps"]))


if __name__ == "__main__":
    unittest.main()
