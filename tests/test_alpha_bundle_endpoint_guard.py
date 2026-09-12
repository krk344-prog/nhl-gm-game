from __future__ import annotations

import unittest

from scripts.verify_alpha_artifact import VerificationError, _reject_forbidden_bundle_endpoints


class AlphaBundleEndpointGuardTests(unittest.TestCase):
    def test_allows_configured_private_lan_endpoint(self):
        _reject_forbidden_bundle_endpoints(
            b"standalone-js-bundle:http://192.168.1.25:8000/api/v1"
        )

    def test_rejects_stale_loopback_endpoint_even_when_reachable_endpoint_is_present(self):
        bundle = (
            b"standalone-js-bundle:http://192.168.1.25:8000/api/v1;"
            b"fallback=http://127.0.0.1:8000/api/v1"
        )

        with self.assertRaisesRegex(
            VerificationError,
            "stale loopback or unspecified endpoint",
        ):
            _reject_forbidden_bundle_endpoints(bundle)


if __name__ == "__main__":
    unittest.main()
