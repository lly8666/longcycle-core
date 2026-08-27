from __future__ import annotations

import unittest

from longcycle.application.source_registration import (
    build_http_source_definition,
    normalize_publisher_domain,
)
from longcycle.domain.enums import QualityGrade, SourceKind


class SourceRegistrationTest(unittest.TestCase):
    def test_http_source_identity_is_stable_and_domain_scoped(self) -> None:
        first = build_http_source_definition(
            name="  Tianqi   Lithium  ",
            publisher_domain="EN.TIANQILITHIUM.COM.",
        )
        second = build_http_source_definition(
            name="Tianqi Lithium",
            publisher_domain="en.tianqilithium.com",
        )

        self.assertEqual(first, second)
        self.assertEqual(first.plugin, "http_document")
        self.assertEqual(first.kind, SourceKind.COMPANY)
        self.assertEqual(first.quality_grade, QualityGrade.A)
        self.assertEqual(first.publisher_domain, "en.tianqilithium.com")
        self.assertEqual(first.config["urls"], [])
        self.assertEqual(first.config["allowed_domains"], ["en.tianqilithium.com"])
        self.assertEqual(first.syndication_cluster, "publisher-domain:en.tianqilithium.com")

    def test_registration_preserves_explicit_authority_and_rate_limit(self) -> None:
        source = build_http_source_definition(
            name="Exchange archive",
            publisher_domain="static.cninfo.com.cn",
            kind=SourceKind.EXCHANGE,
            quality_grade=QualityGrade.A,
            rate_limit_per_minute=12,
        )

        self.assertEqual(source.kind, SourceKind.EXCHANGE)
        self.assertEqual(source.rate_limit_per_minute, 12)
        self.assertEqual(source.config["allowed_domains"], ["static.cninfo.com.cn"])

    def test_publisher_identity_can_use_explicit_archival_retrieval_domain(self) -> None:
        direct = build_http_source_definition(
            name="Tianqi Lithium first-party web",
            publisher_domain="en.tianqilithium.com",
        )
        archival = build_http_source_definition(
            name="Tianqi Lithium first-party web",
            publisher_domain="en.tianqilithium.com",
            allowed_domains=("web.archive.org", "EN.TIANQILITHIUM.COM."),
        )

        self.assertEqual(direct.id, archival.id)
        self.assertEqual(archival.publisher_domain, "en.tianqilithium.com")
        self.assertEqual(
            archival.config["allowed_domains"],
            ["web.archive.org", "en.tianqilithium.com"],
        )
        self.assertEqual(archival.syndication_cluster, "publisher-domain:en.tianqilithium.com")

    def test_domain_normalization_fails_closed_on_urls_and_local_names(self) -> None:
        for invalid in (
            "https://en.tianqilithium.com",
            "en.tianqilithium.com/path",
            "localhost",
            "example.com:443",
            "user@example.com",
            "",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    normalize_publisher_domain(invalid)


if __name__ == "__main__":
    unittest.main()
