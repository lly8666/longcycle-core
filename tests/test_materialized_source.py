from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from longcycle.adapters.sources.materialized import MaterializedDocumentSource
from longcycle.application.source_registration import build_materialized_source_definition
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import DiscoveryItem
from longcycle.ports.source import FetchContext


def source():
    return build_materialized_source_definition(
        name="SEC EDGAR materialized filings",
        publisher_domain="sec.gov",
        kind=SourceKind.REGULATOR,
        quality_grade=QualityGrade.A,
    )


@pytest.mark.asyncio
async def test_materialized_source_preserves_publisher_identity_and_exact_bytes(
    tmp_path: Path,
) -> None:
    content = b"<html><body>source truth</body></html>"
    digest = hashlib.sha256(content).hexdigest()
    material = tmp_path / "sec" / "filing.htm"
    material.parent.mkdir()
    material.write_bytes(content)

    definition = source()
    plugin = MaterializedDocumentSource(definition, material_root=tmp_path)
    item = DiscoveryItem(
        source_id=definition.id,
        external_id="0000000000-00-000001",
        url="https://www.sec.gov/Archives/example/filing.htm",
        discovered_at=datetime(2019, 5, 7, 20, 30, tzinfo=UTC),
        metadata={
            "material_path": "sec/filing.htm",
            "material_expected_sha256": digest,
            "material_content_type": "text/html",
        },
    )

    payload = await plugin.fetch(item, FetchContext(source=definition))

    assert payload.content == content
    assert payload.sha256 == digest
    assert payload.canonical_url == item.url
    assert payload.content_type == "text/html"
    assert payload.headers["x-longcycle-transport"] == "materialized_file"
    assert definition.publisher_domain == "sec.gov"
    assert definition.syndication_cluster == "publisher-domain:sec.gov"


@pytest.mark.asyncio
async def test_materialized_source_rejects_digest_mismatch(tmp_path: Path) -> None:
    material = tmp_path / "filing.htm"
    material.write_bytes(b"actual")
    definition = source()
    plugin = MaterializedDocumentSource(definition, material_root=tmp_path)
    item = DiscoveryItem(
        source_id=definition.id,
        url="https://www.sec.gov/Archives/example/filing.htm",
        metadata={
            "material_path": "filing.htm",
            "material_expected_sha256": hashlib.sha256(b"different").hexdigest(),
            "material_content_type": "text/html",
        },
    )

    with pytest.raises(ValueError, match="digest mismatch"):
        await plugin.fetch(item, FetchContext(source=definition))


@pytest.mark.asyncio
async def test_materialized_source_rejects_parent_traversal(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.htm"
    outside.write_bytes(b"outside")
    definition = source()
    plugin = MaterializedDocumentSource(definition, material_root=tmp_path)
    item = DiscoveryItem(
        source_id=definition.id,
        url="https://www.sec.gov/Archives/example/filing.htm",
        metadata={
            "material_path": "../outside.htm",
            "material_expected_sha256": hashlib.sha256(b"outside").hexdigest(),
            "material_content_type": "text/html",
        },
    )

    with pytest.raises(ValueError, match="relative to material root"):
        await plugin.fetch(item, FetchContext(source=definition))


@pytest.mark.asyncio
async def test_materialized_source_rejects_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-symlink.htm"
    outside.write_bytes(b"outside")
    link = tmp_path / "link.htm"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    definition = source()
    plugin = MaterializedDocumentSource(definition, material_root=tmp_path)
    item = DiscoveryItem(
        source_id=definition.id,
        url="https://www.sec.gov/Archives/example/filing.htm",
        metadata={
            "material_path": "link.htm",
            "material_expected_sha256": hashlib.sha256(b"outside").hexdigest(),
            "material_content_type": "text/html",
        },
    )

    with pytest.raises(ValueError, match="escapes material root"):
        await plugin.fetch(item, FetchContext(source=definition))


@pytest.mark.asyncio
async def test_materialized_source_enforces_maximum_bytes(tmp_path: Path) -> None:
    content = b"12345"
    material = tmp_path / "filing.htm"
    material.write_bytes(content)
    definition = source()
    plugin = MaterializedDocumentSource(definition, material_root=tmp_path)
    item = DiscoveryItem(
        source_id=definition.id,
        url="https://www.sec.gov/Archives/example/filing.htm",
        metadata={
            "material_path": "filing.htm",
            "material_expected_sha256": hashlib.sha256(content).hexdigest(),
            "material_content_type": "text/html",
        },
    )

    with pytest.raises(ValueError, match="exceeds 4 bytes"):
        await plugin.fetch(item, FetchContext(source=definition, maximum_bytes=4))
