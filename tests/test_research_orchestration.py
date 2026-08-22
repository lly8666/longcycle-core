from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from pydantic import ValidationError

from longcycle.application.research_orchestration import (
    ResearchOrchestrationSpec,
    ResearchSourcePackSpec,
    execution_phases,
    immutable_path_digest,
    materialize_evidence_spec,
    verify_and_extract_source_pack,
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class ResearchOrchestrationContractTest(unittest.TestCase):
    def _write_evidence_spec(self, root: Path, *, expected_value: str = "Legacy Name") -> Path:
        path = root / "evidence.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "longcycle-grounded-evidence-spec/v2",
                    "task_id": "SYNTHETIC-EVIDENCE",
                    "sources": [{"key": "synthetic", "transport": "materialized"}],
                    "documents": [
                        {
                            "key": "doc-a",
                            "source_key": "synthetic",
                            "material_path": "doc-a.txt",
                            "content_type": "text/plain",
                            "expected_sha256": _sha(b"alpha"),
                        },
                        {
                            "key": "doc-b",
                            "source_key": "synthetic",
                            "material_path": "nested/doc-b.txt",
                            "content_type": "text/plain",
                            "expected_sha256": _sha(b"beta"),
                        },
                    ],
                    "fragments": [
                        {
                            "fragment_key": "structured-value",
                            "document_key": "doc-a",
                            "expected_value": expected_value,
                            "claim_context": {"claim_role": "synthetic"},
                        }
                    ],
                    "acceptance": {
                        "required_documents": 2,
                        "required_fragments": 1,
                        "facts_created": 0,
                        "judgments_created": 0,
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def _write_repair(self, root: Path, *, from_value: str = "Legacy Name") -> Path:
        path = root / "repair.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "longcycle-grounded-evidence-spec-repair/v1",
                    "task_id": "SYNTHETIC-EVIDENCE",
                    "base_spec_path": "evidence.json",
                    "repair_reason": "Synthetic exact-value correction after authoritative probe.",
                    "probe": {"observed_value": "Current Name"},
                    "repairs": [
                        {
                            "fragment_key": "structured-value",
                            "field": "expected_value",
                            "from": from_value,
                            "to": "Current Name",
                            "epistemic_effect": "Only the exact expected structured value changes.",
                        }
                    ],
                    "acceptance_unchanged": {
                        "required_documents": 2,
                        "required_fragments": 1,
                        "facts_created": 0,
                        "judgments_created": 0,
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def _write_source_pack(self, root: Path, *, beta: bytes = b"beta") -> Path:
        pack = root / "source-pack.zip"
        with zipfile.ZipFile(pack, "w") as archive:
            archive.writestr("doc-a.txt", b"alpha")
            archive.writestr("nested/doc-b.txt", beta)
            archive.writestr("extra-not-needed.txt", b"still pinned by the outer pack digest")
        return pack

    def test_source_pack_hash_and_required_material_hashes_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_path = self._write_evidence_spec(root)
            evidence_spec = json.loads(evidence_path.read_text(encoding="utf-8"))
            pack = self._write_source_pack(root)
            source_pack = ResearchSourcePackSpec(
                transport="github_release",
                release_tag="synthetic-release",
                file_name=pack.name,
                sha256=_sha(pack.read_bytes()),
            )
            verified = verify_and_extract_source_pack(
                source_pack_path=pack,
                source_pack_spec=source_pack,
                evidence_spec=evidence_spec,
                material_root=root / "material",
            )
            self.assertEqual([item.material_path for item in verified], ["doc-a.txt", "nested/doc-b.txt"])
            self.assertEqual((root / "material" / "doc-a.txt").read_bytes(), b"alpha")
            self.assertEqual((root / "material" / "nested" / "doc-b.txt").read_bytes(), b"beta")

            bad_outer = source_pack.model_copy(update={"sha256": "0" * 64})
            with self.assertRaisesRegex(ValueError, "source pack digest mismatch"):
                verify_and_extract_source_pack(
                    source_pack_path=pack,
                    source_pack_spec=bad_outer,
                    evidence_spec=evidence_spec,
                    material_root=root / "bad-outer",
                )

            bad_pack = self._write_source_pack(root, beta=b"tampered")
            bad_pack_spec = source_pack.model_copy(update={"sha256": _sha(bad_pack.read_bytes())})
            with self.assertRaisesRegex(ValueError, "material digest mismatch"):
                verify_and_extract_source_pack(
                    source_pack_path=bad_pack,
                    source_pack_spec=bad_pack_spec,
                    evidence_spec=evidence_spec,
                    material_root=root / "bad-material",
                )

    def test_explicit_repair_overlay_preserves_acceptance_and_checks_from_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_evidence_spec(root)
            self._write_repair(root)
            prepared_spec, prepared = materialize_evidence_spec(
                repo_root=root,
                evidence_spec_path="evidence.json",
                repair_paths=("repair.json",),
                destination=root / "work" / "prepared.json",
            )
            fragment = prepared_spec["fragments"][0]
            self.assertEqual(fragment["expected_value"], "Current Name")
            self.assertEqual(prepared.repair_count, 1)
            self.assertEqual(
                prepared_spec["acceptance"],
                {
                    "required_documents": 2,
                    "required_fragments": 1,
                    "facts_created": 0,
                    "judgments_created": 0,
                },
            )

            self._write_repair(root, from_value="Wrong Prior Value")
            with self.assertRaisesRegex(ValueError, "repair from-value mismatch"):
                materialize_evidence_spec(
                    repo_root=root,
                    evidence_spec_path="evidence.json",
                    repair_paths=("repair.json",),
                    destination=root / "work" / "should-not-pass.json",
                )

    def test_repair_contract_cannot_patch_claim_context_or_other_semantics(self) -> None:
        with self.assertRaises(ValidationError):
            ResearchOrchestrationSpec.model_validate(
                {
                    "schema_version": "longcycle-research-orchestration/v1",
                    "task_id": "bad",
                    "source_pack": {
                        "transport": "github_release",
                        "release_tag": "x",
                        "file_name": "x.zip",
                        "sha256": "0" * 64,
                    },
                    "evidence_spec_path": "evidence.json",
                    "unexpected_semantic_patch": True,
                }
            )

    def test_optional_reality_phase_is_data_driven_not_campaign_specific(self) -> None:
        base = {
            "schema_version": "longcycle-research-orchestration/v1",
            "task_id": "synthetic",
            "source_pack": {
                "transport": "github_release",
                "release_tag": "synthetic-release",
                "file_name": "source-pack.zip",
                "sha256": "0" * 64,
            },
            "evidence_spec_path": "evidence.json",
        }
        evidence_only = ResearchOrchestrationSpec.model_validate(base)
        self.assertEqual(execution_phases(evidence_only), ("grounded_evidence",))

        with_reality = ResearchOrchestrationSpec.model_validate(
            {**base, "reality_spec_path": "reality.json"}
        )
        self.assertEqual(
            execution_phases(with_reality),
            ("grounded_evidence", "reality_projection"),
        )

    def test_immutable_path_digest_changes_on_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blind = root / "blind"
            blind.mkdir()
            lead = blind / "passes.jsonl"
            lead.write_text('{"lead":1}\n', encoding="utf-8")
            before = immutable_path_digest(root, "blind")
            lead.write_text('{"lead":2}\n', encoding="utf-8")
            after = immutable_path_digest(root, "blind")
            self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
