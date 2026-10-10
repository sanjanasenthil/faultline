from __future__ import annotations

import unittest

from faultline.agent import diagnose
from faultline.scrubber import assert_no_leakage


class AgentTests(unittest.TestCase):
    def test_selects_service_with_corroborated_metric_and_trace_evidence(self) -> None:
        bundle = {
            "alert": {"service": "frontend", "symptom": "checkout_errors"},
            "anomalies": {
                "service_errors": {
                    "data": {
                        "result": [
                            {"metric": {"service_name": "frontend"}, "value": [1, "500"]},
                            {"metric": {"service_name": "payment"}, "value": [1, "25"]},
                        ]
                    }
                }
            },
            "trace_summary": {
                "span_calls_by_service": {
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "service_name": "payment",
                                    "span_name": "oteldemo.PaymentService/Charge",
                                    "status_code": "STATUS_CODE_ERROR",
                                },
                                "value": [1, "25"],
                            }
                        ]
                    }
                }
            },
            "logs": {"hits": {"hits": []}},
            "changes": {"changes": []},
        }

        result = diagnose(bundle)

        self.assertEqual(result["conclusion"]["root_service"], "payment")
        self.assertEqual(result["conclusion"]["confidence"], "medium")
        self.assertIn("metrics", result["conclusion"]["evidence"]["signal_types"])
        self.assertIn("traces", result["conclusion"]["evidence"]["signal_types"])
        self.assertTrue(result["conclusion"]["verification"]["verified"])
        assert_no_leakage(result)

    def test_abstains_without_evidence(self) -> None:
        result = diagnose({"alert": {"service": "frontend", "symptom": "unknown"}})

        self.assertIsNone(result["conclusion"]["root_service"])
        self.assertEqual(result["conclusion"]["confidence"], "abstain")
        self.assertFalse(result["conclusion"]["verification"]["verified"])
        assert_no_leakage(result)

    def test_prefers_downstream_root_over_noisy_edge_symptom(self) -> None:
        bundle = {
            "alert": {"service": "frontend", "symptom": "checkout_errors"},
            "anomalies": {
                "service_errors": {
                    "data": {
                        "result": [
                            {"metric": {"service_name": "load-generator"}, "value": [1, "1000"]},
                            {"metric": {"service_name": "frontend-proxy"}, "value": [1, "800"]},
                            {"metric": {"service_name": "checkout"}, "value": [1, "12"]},
                        ]
                    }
                }
            },
            "trace_summary": {
                "span_calls_by_service": {
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "service_name": "checkout",
                                    "span_name": "oteldemo.CheckoutService/PlaceOrder",
                                    "status_code": "STATUS_CODE_ERROR",
                                },
                                "value": [1, "12"],
                            },
                            {
                                "metric": {
                                    "service_name": "load-generator",
                                    "span_name": "POST",
                                    "status_code": "STATUS_CODE_ERROR",
                                },
                                "value": [1, "500"],
                            },
                        ]
                    }
                }
            },
            "logs": {"hits": {"hits": []}},
            "changes": {"changes": []},
        }

        result = diagnose(bundle)

        self.assertEqual(result["conclusion"]["root_service"], "checkout")
        self.assertEqual(result["conclusion"]["confidence"], "medium")
        self.assertTrue(result["conclusion"]["verification"]["verified"])
        assert_no_leakage(result)

    def test_prefers_stronger_verified_downstream_candidate(self) -> None:
        bundle = {
            "alert": {"service": "frontend", "symptom": "checkout_errors"},
            "anomalies": {
                "service_errors": {
                    "data": {
                        "result": [
                            {"metric": {"service_name": "checkout"}, "value": [1, "36"]},
                            {"metric": {"service_name": "product-catalog"}, "value": [1, "1"]},
                        ]
                    }
                }
            },
            "trace_summary": {
                "span_calls_by_service": {
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "service_name": "checkout",
                                    "span_name": "POST",
                                    "status_code": "STATUS_CODE_ERROR",
                                },
                                "value": [1, "32"],
                            },
                            {
                                "metric": {
                                    "service_name": "product-catalog",
                                    "span_name": "oteldemo.ProductCatalogService/GetProduct",
                                    "status_code": "STATUS_CODE_ERROR",
                                },
                                "value": [1, "1"],
                            },
                        ]
                    }
                }
            },
            "logs": {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "resource": {"service.name": "product-catalog"},
                                "severity": {"text": "INFO"},
                                "body": "Product Found",
                            }
                        }
                    ]
                }
            },
            "changes": {"changes": []},
        }

        result = diagnose(bundle)

        self.assertEqual(result["conclusion"]["root_service"], "checkout")
        self.assertTrue(result["conclusion"]["verification"]["verified"])
        assert_no_leakage(result)


if __name__ == "__main__":
    unittest.main()
