import json
import unittest
from urllib.error import HTTPError

from scripts.upstream_status import audit_upstreams, fetch_repository_status


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class UpstreamStatusTests(unittest.TestCase):
    def test_parses_archived_and_license_metadata(self):
        payload = {
            "html_url": "https://github.com/example/project",
            "archived": True,
            "disabled": False,
            "default_branch": "main",
            "pushed_at": "2024-01-01T00:00:00Z",
            "license": {"spdx_id": "MIT"},
            "visibility": "public",
        }
        captured = {}
        def opener(request, timeout):
            captured["request"] = request
            return FakeResponse(payload)

        result = fetch_repository_status(
            "example/project",
            token="read-only-token",
            opener=opener,
        )
        self.assertEqual(result["status"], "checked")
        self.assertEqual(captured["request"].get_header("Authorization"), "Bearer read-only-token")
        self.assertTrue(result["archived"])
        self.assertEqual(result["license_spdx_id"], "MIT")

    def test_distinguishes_missing_or_private_from_rate_limit(self):
        def not_found(request, timeout):
            raise HTTPError(request.full_url, 404, "Not Found", {}, None)

        def rate_limited(request, timeout):
            error = HTTPError(request.full_url, 403, "rate limited", {}, None)
            error.headers = {"X-RateLimit-Remaining": "0"}
            raise error

        self.assertEqual(
            fetch_repository_status("example/missing", opener=not_found)["status"],
            "not_found_or_private",
        )
        self.assertEqual(
            fetch_repository_status("example/project", opener=rate_limited)["status"],
            "rate_limited",
        )

    def test_defaults_to_small_unauthenticated_batch(self):
        calls = []

        def opener(request, timeout):
            calls.append(request.full_url)
            return FakeResponse({
                "html_url": request.full_url,
                "archived": False,
                "disabled": False,
                "default_branch": "main",
                "pushed_at": None,
                "license": None,
                "visibility": "public",
            })

        report = audit_upstreams(
            root=".",
            token=None,
            limit=1,
            delay=0,
            opener=opener,
            sleeper=lambda _: None,
        )
        self.assertEqual(report["attempted_count"], 1)
        self.assertFalse(report["authenticated"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(report["not_attempted_count"], report["catalog_repository_count"] - 1)


if __name__ == "__main__":
    unittest.main()
