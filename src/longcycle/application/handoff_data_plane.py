from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AssetRole = Literal[
    "research_evidence_capsule",
    "offline_runtime",
    "research_pack",
    "cold_archive_pack",
]


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
    transport: Literal["google_drive"]
    google_drive_file_id: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_summary: str = Field(min_length=1)
    components: tuple[HandoffAssetComponent, ...] = ()
    restore_instruction: str = Field(min_length=1)


class HandoffDataPlaneManifest(BaseModel):
    """Binary handoff state that is too large for Git but must remain reproducible."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["longcycle-handoff-data-plane/v1"]
    transport_mode: Literal["sandbox_google_drive_manual_relay"]
    google_drive_folder_id: str = Field(min_length=1)
    capacity_policy: str = Field(min_length=1)
    postgres_policy: str = Field(min_length=1)
    duckdb_policy: str = Field(min_length=1)
    missing_required_asset_action: Literal["stop_and_report_integrity_blocker"]
    supersession_policy: str = Field(min_length=1)
    assets: tuple[HandoffBinaryAsset, ...]

    @model_validator(mode="after")
    def asset_contract_is_complete(self) -> HandoffDataPlaneManifest:
        if not self.assets:
            raise ValueError("handoff data plane requires at least one binary asset")
        ids = [asset.asset_id for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("handoff data-plane asset ids must be unique")
        if not any(asset.required_for_current_task for asset in self.assets):
            raise ValueError("current handoff must identify at least one required binary asset")
        return self
