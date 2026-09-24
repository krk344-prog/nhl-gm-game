import unittest

from scripts.select_alpha_api_endpoint import _usable_private_ipv4, select_endpoint


class AlphaEndpointSelectionTest(unittest.TestCase):
    def test_filters_unsafe_and_duplicate_addresses(self):
        self.assertEqual(
            _usable_private_ipv4(
                [
                    "127.0.0.1",
                    "0.0.0.0",
                    "169.254.10.2",
                    "192.168.1.25",
                    "192.168.1.25",
                    "10.0.0.8",
                    "not-an-address",
                    "::1",
                ]
            ),
            ("10.0.0.8", "192.168.1.25"),
        )

    def test_selects_stable_non_loopback_api_urls(self):
        result = select_endpoint(
            ["192.168.1.25", "10.0.0.8"],
            port=8000,
            api_prefix="api/v1/",
        )

        self.assertTrue(result.ready)
        self.assertEqual(result.host_count, 2)
        self.assertEqual(
            result.recommended_api_base_url,
            "http://10.0.0.8:8000/api/v1",
        )
        self.assertEqual(
            result.candidate_api_base_urls,
            (
                "http://10.0.0.8:8000/api/v1",
                "http://192.168.1.25:8000/api/v1",
            ),
        )

    def test_fails_when_only_loopback_or_link_local_addresses_exist(self):
        with self.assertRaisesRegex(RuntimeError, "No non-loopback private IPv4"):
            select_endpoint(["127.0.0.1", "169.254.1.4", "::1"])

    def test_rejects_invalid_port(self):
        with self.assertRaisesRegex(ValueError, "port"):
            select_endpoint(["192.168.1.25"], port=70000)


if __name__ == "__main__":
    unittest.main()
