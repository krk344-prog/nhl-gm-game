import json
import threading
import unittest
from http.client import HTTPConnection

from src.season_context_api import create_season_context_server


class SeasonContextHttpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_season_context_server()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path):
        connection = HTTPConnection(self.host, self.port, timeout=5)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload
        finally:
            connection.close()

    def test_explicit_season_context_is_available_over_http(self):
        status, payload = self.request(
            "/api/v1/season-context?season_id=2026-27"
        )

        self.assertEqual(status, 200)
        context = payload["season_context"]
        self.assertEqual(context["season_id"], "2026-27")
        self.assertEqual(context["regular_season_games"], 84)
        self.assertEqual(context["upper_limit"], 104_000_000)
        self.assertTrue(context["source_ids"])

    def test_missing_blank_repeated_and_unknown_seasons_return_stable_400(self):
        paths = (
            "/api/v1/season-context",
            "/api/v1/season-context?season_id=",
            "/api/v1/season-context?season_id=2025-26&season_id=2026-27",
            "/api/v1/season-context?season_id=2099-00",
        )

        for path in paths:
            with self.subTest(path=path):
                status, payload = self.request(path)
                self.assertEqual(status, 400)
                self.assertEqual(payload["code"], "invalid_season_context_request")

    def test_existing_health_route_is_unchanged(self):
        status, payload = self.request("/api/v1/health")

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ok", "version": "0.2.0-alpha"})

    def test_unrelated_unknown_route_remains_404(self):
        status, payload = self.request("/api/v1/not-a-route")

        self.assertEqual(status, 404)
        self.assertEqual(payload, {"error": "Route not found"})


if __name__ == "__main__":
    unittest.main()
