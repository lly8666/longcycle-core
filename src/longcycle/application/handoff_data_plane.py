from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AssetRole = Literal[
    "raw_source_acquisition_cache",
    "legacy_materialized_pdf_source_cache",
    "webpage_source_capture_capsule",
    "research_evidence_capsule",
    "research_lifecycle_capsule",
    "research_outcome_pressure_capsule",
    "typed_replay_capsule",
    "offline_runtime",
    "research_pack",
    "cold_archive_pack",
]
AssetTransport = Literal[
    "github_release",
    "github_release_legacy_materialization",
    "google_drive",
]


class HandoffDatabaseGenerationHead(BaseModel):
    """One main-promoted immutable database generation used by active work."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lane_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,62}$")
    generation_id: str = Field(min_length=1, max_length=128)
    asset_id: str = Field(min_length=1, max_length=128)
    google_drive_file_id: str = Field(min_length=1)
    drive_revision_id: str | None = None
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    schema_revision: str = Field(min_length=1, max_length=128)
    integrated_main_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    predecessor_generation_id: str | None = Field(default=None, max_length=128)
    integration_receipt_ref: str = Field(min_length=1)
    restore_instruction: str = Field(min_length=1)


class HandoffAssetComponent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    role: str = Field(min_length=1)
    size_bytes: int | None = Field(default=None, ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class HandoffBinaryAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_id: str = Field(min_length=1)
    role: AssetRole
    required_for_current_task: bool
    transport: AssetTransport
    release_tag: str | None = None
    google_drive_file_id: str | None = None
    file_name: str = Field(min_length=1)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    materialization_status: str | None = None
    content_summary: str = Field(min_length=1)
    components: tuple[HandoffAssetComponent, ...] = ()
    restore_instruction: str = Field(min_length=1)

    @model_validator(mode="after")
    def transport_matches_asset_role(self) -> HandoffBinaryAsset:
        if self.transport in {"github_release", "github_release_legacy_materialization"}:
            if not self.release_tag:
                raise ValueError("GitHub Release assets require release_tag")
            if self.google_drive_file_id is not None:
                raise ValueError("GitHub Release assets cannot carry a Google Drive file id")
        elif self.transport == "google_drive":
            if not self.google_drive_file_id:
                raise ValueError("Google Drive assets require google_drive_file_id")
            if self.release_tag is not None:
                raise ValueError("Google Drive assets cannot carry a Release tag")

        if self.role == "webpage_source_capture_capsule" and self.transport != "google_drive":
            raise ValueError("webpage capture capsules must use Google Drive")
        if self.role == "legacy_materialized_pdf_source_cache" and self.transport not in {
            "github_release",
            "github_release_legacy_materialization",
        }:
            raise ValueError("legacy materialized PDF caches must remain on their Release transport")
        if self.role == "raw_source_acquisition_cache" and self.transport != "github_release":
            raise ValueError("legacy raw source acquisition caches must remain on GitHub Release")
        if self.role in {
            "research_evidence_capsule",
            "research_lifecycle_capsule",
            "research_outcome_pressure_capsule",
            "typed_replay_capsule",
            "offline_runtime",
            "research_pack",
            "cold_archive_pack",
        } and self.transport != "google_drive":
            raise ValueError("Longcycle-generated binary assets must use Google Drive")
        return self


class HandoffDataPlaneManifest(BaseModel):
    """Resume-relevant source/data state that is too large or unsuitable for Git.

    v4 deliberately separates PDF source identity/content verification from optional raw-byte
    materialization. v5 adds bounded, main-promoted immutable database generation heads so
    parallel workers never treat a shared Drive file as a writable database. Older manifests
    remain readable so durable historical receipts do not require migration churn.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[
        "longcycle-handoff-data-plane/v2",
        "longcycle-handoff-data-plane/v3",
        "longcycle-handoff-data-plane/v4",
        "longcycle-handoff-data-plane/v5",
    ]
    transport_mode: Literal[
        "github_release_sources_google_drive_generated",
        "github_release_pdf_sources_google_drive_webcapsules_generated",
        "google_drive_webcapsules_generated_pdf_locator_deferred_materialization",
        "google_drive_immutable_generations_pdf_locator_deferred_materialization",
    ]
    webpage_capture_policy: str | None = None
    pdf_source_policy: dict[str, Any] | None = None
    github_actions_pdf_policy: str | None = None
    github_release_policy: str = Field(min_length=1)
    google_drive_folder_id: str = Field(min_length=1)
    google_drive_policy: str = Field(min_length=1)
    postgres_policy: str = Field(min_length=1)
    duckdb_policy: str = Field(min_length=1)
    parallel_database_policy: str | None = None
    drive_generation_policy: str | None = None
    drive_upload_recovery_policy: str | None = None
    database_generation_heads: tuple[HandoffDatabaseGenerationHead, ...] = Field(
        default=(), max_length=8
    )
    legacy_release_web_policy: str | None = None
    historical_asset_index_policy: str | None = None
    missing_required_asset_action: str = Field(min_length=1)
    supersession_policy: str = Field(min_length=1)
    assets: tuple[HandoffBinaryAsset, ...]

    @model_validator(mode="after")
    def asset_contract_is_complete(self) -> HandoffDataPlaneManifest:
        ids = [asset.asset_id for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("handoff data-plane asset ids must be unique")

        if self.schema_version == "longcycle-handoff-data-plane/v4":
            if self.transport_mode != (
                "google_drive_webcapsules_generated_pdf_locator_deferred_materialization"
            ):
                raise ValueError("data-plane v4 requires deferred PDF materialization mode")
            if not self.webpage_capture_policy:
                raise ValueError("data-plane v4 requires webpage_capture_policy")
            if not self.pdf_source_policy:
                raise ValueError("data-plane v4 requires pdf_source_policy")
            if not self.github_actions_pdf_policy:
                raise ValueError("data-plane v4 requires github_actions_pdf_policy")
            states = self.pdf_source_policy.get("states")
            if states != ["locator_verified", "content_verified", "materialized"]:
                raise ValueError("data-plane v4 PDF state machine must preserve all three states")
        if self.schema_version == "longcycle-handoff-data-plane/v5":
            if self.transport_mode != (
                "google_drive_immutable_generations_pdf_locator_deferred_materialization"
            ):
                raise ValueError("data-plane v5 requires immutable Drive generation mode")
            if not self.webpage_capture_policy or not self.pdf_source_policy:
                raise ValueError("data-plane v5 requires webpage and PDF source policies")
            if not self.github_actions_pdf_policy:
                raise ValueError("data-plane v5 requires github_actions_pdf_policy")
            states = self.pdf_source_policy.get("states")
            if states != ["locator_verified", "content_verified", "materialized"]:
                raise ValueError("data-plane v5 PDF state machine must preserve all three states")
            if not all(
                (
                    self.parallel_database_policy,
                    self.drive_generation_policy,
                    self.drive_upload_recovery_policy,
                )
            ):
                raise ValueError("data-plane v5 requires parallel database and Drive policies")

        lane_ids = [head.lane_id for head in self.database_generation_heads]
        if len(lane_ids) != len(set(lane_ids)):
            raise ValueError("database generation lanes must be unique")
        generation_ids = [head.generation_id for head in self.database_generation_heads]
        if len(generation_ids) != len(set(generation_ids)):
            raise ValueError("database generation ids must be unique")
        return self
