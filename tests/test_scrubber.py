from __future__ import annotations

import unittest

from faultline.scrubber import assert_no_leakage, scrub


class ScrubberTests(unittest.TestCase):
    def test_removes_flagd_records(self) -> None:
        payload = {
            "hits": [
                {"resource": {"service.name": "flagd"}, "body": "resolved paymentFailure"},
                {"resource": {"service.name": "checkout"}, "body": "checkout failed with upstream error"},
            ]
        }

        cleaned = scrub(payload)

        self.assertEqual(len(cleaned["hits"]), 1)
        self.assertEqual(cleaned["hits"][0]["resource"]["service.name"], "checkout")
        assert_no_leakage(cleaned)

    def test_removes_flag_attributes_and_redacts_strings(self) -> None:
        payload = {
            "span": {
                "name": "checkout",
                "feature_flag.key": "cartFailure",
                "attributes": {
                    "openfeature.provider": "flagd",
                    "http.status_code": 500,
                    "message": "paymentFailure was enabled by faultline.injector",
                },
            }
        }

        cleaned = scrub(payload)

        self.assertNotIn("feature_flag.key", cleaned["span"])
        self.assertNotIn("openfeature.provider", cleaned["span"]["attributes"])
        self.assertEqual(cleaned["span"]["attributes"]["http.status_code"], 500)
        assert_no_leakage(cleaned)

    def test_scrubs_nested_prometheus_metrics(self) -> None:
        payload = {
            "data": {
                "result": [
                    {"metric": {"service_name": "flagd", "span_name": "ResolveBoolean"}, "value": [1, "2"]},
                    {"metric": {"service_name": "frontend", "span_name": "paymentFailure"}, "value": [1, "3"]},
                ]
            }
        }

        cleaned = scrub(payload)

        self.assertEqual(len(cleaned["data"]["result"]), 1)
        self.assertEqual(cleaned["data"]["result"][0]["metric"]["service_name"], "frontend")
        assert_no_leakage(cleaned)

    def test_drops_metric_rows_when_all_labels_are_removed(self) -> None:
        payload = {
            "data": {
                "result": [
                    {"metric": {"feature_flag_key": "paymentFailure"}, "value": [1, "2"]},
                    {"metric": {"service_name": "checkout"}, "value": [1, "3"]},
                ]
            }
        }

        cleaned = scrub(payload)

        self.assertEqual(len(cleaned["data"]["result"]), 1)
        self.assertEqual(cleaned["data"]["result"][0]["metric"]["service_name"], "checkout")
        assert_no_leakage(cleaned)

    def test_redacts_flagservice_route_names(self) -> None:
        payload = {
            "data": {
                "result": [
                    {"metric": {"service_name": "frontend-proxy", "span_name": "router flagservice egress"}, "value": [1, "2"]}
                ]
            }
        }

        cleaned = scrub(payload)

        self.assertEqual(cleaned["data"]["result"][0]["metric"]["span_name"], f"router {'[REDACTED]'} egress")
        assert_no_leakage(cleaned)


if __name__ == "__main__":
    unittest.main()
