import io
import json
import unittest
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from domain_status import CheckError, NoRedirects, check_domain, classify, registry_url


class DomainStatusTests(unittest.TestCase):
    def record(self, *statuses):
        return {"objectClassName": "domain", "ldhName": "CLEOFIELDS.COM",
                "status": list(statuses)}

    def test_redemption_is_not_available_despite_registrar_notice(self):
        record = self.record("client hold", "client transfer prohibited", "redemption period")
        record["notices"] = [{"description": ["domain not found", "available"]}]
        self.assertEqual(classify("cleofields.com", 200, record)[0], "redemptionPeriod")

    def test_lifecycle_states(self):
        for statuses, expected in [(["pending delete"], "pendingDelete"),
                                   (["client hold"], "clientHold"),
                                   (["active"], "registered"),
                                   ([], "registered"),
                                   (["redemption period", "pending delete"], "redemptionPeriod")]:
            with self.subTest(statuses=statuses):
                self.assertEqual(classify("cleofields.com", 200, self.record(*statuses))[0], expected)

    def test_only_explicit_registry_404_means_unregistered(self):
        self.assertEqual(classify("cleofields.com", 404, {"errorCode": 404}), ("available", []))
        for code, payload in [(404, {}), (200, {"errorCode": 404}),
                              (429, {"errorCode": 429}), (503, {"errorCode": 404}),
                              (404, {"errorCode": 404, "ldhName": "CLEOFIELDS.COM"}),
                              (200, {"description": "domain not found"}), (200, [])]:
            with self.subTest(code=code, payload=payload), self.assertRaises(CheckError):
                classify("cleofields.com", code, payload)

    def test_wrong_domain_and_malformed_status_fail(self):
        for record in [{"objectClassName": "domain", "ldhName": "OTHER.COM"},
                       {**self.record(), "status": "available"}]:
            with self.assertRaises(CheckError):
                classify("cleofields.com", 200, record)

    def test_input_validation(self):
        self.assertEqual(registry_url("CLEOFIELDS.COM.")[0], "cleofields.com")
        self.assertIn("/net/v1/domain/", registry_url("example.net")[1])
        for domain in ["../cleofields.com", "example.org", "x.cleofields.com", "-bad.com", ""]:
            with self.subTest(domain=domain), self.assertRaises(CheckError):
                registry_url(domain)

    def response_error(self, code, body, content_type="application/rdap+json"):
        headers = Message()
        headers["Content-Type"] = content_type
        return HTTPError("https://rdap.verisign.com/com/v1/domain/cleofields.com",
                         code, "test", headers, io.BytesIO(body))

    @patch("domain_status.build_opener")
    def test_registered_response_ignores_registrar_referral(self, opener):
        record = self.record("redemption period")
        record["links"] = [{"rel": "related", "href": "https://registrar.example/not-found"}]
        opener.return_value.open.return_value = self.response_error(200, json.dumps(record).encode())
        self.assertEqual(check_domain("cleofields.com")["state"], "redemptionPeriod")
        opener.return_value.open.assert_called_once()
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://rdap.verisign.com/com/v1/domain/cleofields.com")
        self.assertIsNone(NoRedirects().redirect_request(None, None, 302, "", {}, "https://registrar.example"))

    @patch("domain_status.build_opener")
    def test_http_404_handling(self, opener):
        opener.return_value.open.side_effect = self.response_error(404, b'{"errorCode":404}')
        self.assertEqual(check_domain("cleofields.com")["state"], "available")

    @patch("domain_status.build_opener")
    def test_failures_never_report_available(self, opener):
        for failure in [URLError("DNS unavailable"), TimeoutError("timed out"),
                        self.response_error(404, b"not found", "text/html"),
                        self.response_error(404, b"invalid JSON"),
                        self.response_error(429, b'{"errorCode":429}'),
                        self.response_error(302, b'{"errorCode":404}')]:
            opener.return_value.open.side_effect = failure
            with self.subTest(failure=failure), self.assertRaises(CheckError):
                check_domain("cleofields.com")


if __name__ == "__main__":
    unittest.main()
