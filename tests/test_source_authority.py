from __future__ import annotations

import unittest

from longcycle.application.source_authority import (
    parse_source_authority_profiles,
    validate_redistributed_document_provenance,
)
from longcycle.application.source_registration import build_materialized_source_definition


class SourceAuthorityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = build_materialized_source_definition(
            name="Trusted formal announcement repository",
            publisher_domain="prnewswire.com",
        )
        self.profiles = parse_source_authority_profiles(
            [
                {
                    "claim_scope": "legal_disclosure",
                    "authority_class": "authoritative_redistributor",
                    "authority_basis": "verbatim_official_redistribution",
                    "rationale": "Issuer-supplied formal announcement body is preserved verbatim.",
                }
            ]
        )

    def test_exact_redistribution_requires_upstream_announcement_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "upstream_announcement"):
            validate_redistributed_document_provenance(
                source=self.source,
                retrieval_url=(
                    "https://www.prnewswire.com/news-releases/issuer-results-300000000.html"
                ),
                retrieval_provenance={},
                authority_profiles=self.profiles,
            )

    def test_exact_redistribution_accepts_retrieval_and_upstream_identity(self) -> None:
        validate_redistributed_document_provenance(
            source=self.source,
            retrieval_url="https://www.prnewswire.com/news-releases/issuer-results-300000000.html",
            retrieval_provenance={
                "upstream_announcement": {
                    "issuer": "Example Corporation",
                    "system": "SEC EDGAR",
                    "external_id": "0000000000-19-000001",
                    "title": "Example Corporation Announces First Quarter Results",
                }
            },
            authority_profiles=self.profiles,
        )

    def test_redistributor_retrieval_url_must_match_actual_publisher(self) -> None:
        with self.assertRaisesRegex(ValueError, "publisher domain"):
            validate_redistributed_document_provenance(
                source=self.source,
                retrieval_url="https://www.sec.gov/Archives/edgar/data/example.htm",
                retrieval_provenance={
                    "upstream_announcement": {
                        "issuer": "Example Corporation",
                        "system": "SEC EDGAR",
                        "external_id": "0000000000-19-000001",
                        "title": "Example Corporation Announces First Quarter Results",
                    }
                },
                authority_profiles=self.profiles,
            )

    def test_redistributor_requires_verbatim_official_basis(self) -> None:
        profiles = parse_source_authority_profiles(
            [
                {
                    "claim_scope": "legal_disclosure",
                    "authority_class": "authoritative_redistributor",
                    "authority_basis": "editorial_verification",
                    "rationale": "This must not upgrade an editorial rewrite.",
                }
            ]
        )
        with self.assertRaisesRegex(ValueError, "verbatim_official_redistribution"):
            validate_redistributed_document_provenance(
                source=self.source,
                retrieval_url=(
                    "https://www.prnewswire.com/news-releases/issuer-results-300000000.html"
                ),
                retrieval_provenance={
                    "upstream_announcement": {
                        "issuer": "Example Corporation",
                        "system": "SEC EDGAR",
                        "external_id": "0000000000-19-000001",
                        "title": "Example Corporation Announces First Quarter Results",
                    }
                },
                authority_profiles=profiles,
            )


if __name__ == "__main__":
    unittest.main()
