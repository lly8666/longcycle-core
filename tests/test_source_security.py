from __future__ import annotations

import unittest

from longcycle.adapters.sources.http import _assert_public_host, canonicalize_http_url


class SourceSecurityTest(unittest.TestCase):
    def test_url_canonicalization(self) -> None:
        self.assertEqual(canonicalize_http_url("HTTPS://Example.COM:443/a?q=1#fragment"), "https://example.com/a?q=1")

    def test_localhost_is_rejected_before_fetch(self) -> None:
        with self.assertRaises(ValueError):
            _assert_public_host("http://localhost/admin")
