from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AssetRole = Literal[
    "raw_source_acquisition_cache",
    "research_evidence_capsule",
    "typed_replay_capsule",
    "offline_runtime",
    "research_pack",
    "cold_archive_pack",
]
AssetTransport = Literal["github_release", "google_drive"]


class HandoffAssetComponent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    role: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
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
    content_summary: str = Field(min_length=1)
    components: tuple[HandoffAssetComponent, ...] = ()
    restore_instruction: str = Field(min_length=1)

    @model_validator(mode="after")
    def transport_matches_asset_role(self) -> HandoffBinaryAsset:
        if self.transport == "github_release":
            if not self.release_tag:
                raise ValueError("GitHub Release assets require release_tag")
            if self.google_drive_file_id is not None:
                raise ValueError("GitHub Release assets cannot carry a Google Drive file id")
        else:
            if not self.google_drive_file_id:
                raise ValueError("Google Drive assets require google_drive_file_id")
            if self.release_tag is not None:
                raise ValueError("Google Drive assets cannot carry a Release tag")

        if self.role == "raw_source_acquisition_cache":
            if self.transport != "github_release":
                raise ValueError("externally acquired raw source packs must use GitHub Release")
        elif self.transport != "google_drive":
            raise ValueError("Longcycle-generated binary assets must use Google Drive")
        return self


class HandoffDataPlaneManifest(BaseModel):
    """Resume-relevant binary state that is too large for Git but must remain reproducible."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["longcycle-handoff-data-plane/v2"]
    transport_mode: Literal["github_release_sources_google_drive_generated"]
    github_release_policy: str = Field(min_length=1)
    google_drive_folder_id: str = Field(min_length=1)
    google_drive_policy: str = Field(min_length=1)
    postgres_policy: str = Field(min_length=1)
    duckdb_policy: str = Field(min_length=1)
    missing_required_asset_action: Literal["stop_and_report_integrity_blocker"]
    supersession_policy: str = Field(min_length=1)
    assets: tuple[HandoffBinaryAsset, ...]

    @model_validator(mode="after")
    def asset_contract_is_complete(self) -> HandoffDataPlaneManifest:
        ids = [asset.asset_id for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("handoff data-plane asset ids must be unique")
        return self
