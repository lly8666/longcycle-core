from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ROOT / ".github" / "workflows" / "ci.yml",
    ROOT / ".github" / "workflows" / "architecture-baseline.yml",
)


def test_required_custom_statuses_target_real_pr_head() -> None:
    for workflow in WORKFLOWS:
        text = workflow.read_text(encoding="utf-8")
        assert "STATUS_SHA: ${{ github.event.pull_request.head.sha || github.sha }}" in text
        assert 'statuses/$STATUS_SHA' in text
        assert 'statuses/$GITHUB_SHA' not in text


def test_worker_fast_fetches_only_the_active_baseline_tag() -> None:
    text = (ROOT / ".github" / "workflows" / "architecture-baseline.yml").read_text(
        encoding="utf-8"
    )
    assert 'BASELINE_TAG="$(python -c' in text
    assert 'git check-ref-format "refs/tags/$BASELINE_TAG"' in text
    assert '"+refs/tags/$BASELINE_TAG:refs/tags/$BASELINE_TAG"' in text


def test_worker_fast_runs_generic_remote_continuity_audit() -> None:
    text = (ROOT / ".github" / "workflows" / "architecture-baseline.yml").read_text(
        encoding="utf-8"
    )
    assert "- name: Remote worker continuity is CLEAN" in text
    assert 'WORKSTREAM_ID="${GITHUB_REF_NAME#workstream/}"' in text
    assert (
        'python scripts/audit_workstream_continuity.py "$WORKSTREAM_ID" '
        '--remote origin --main-branch main'
    ) in text
    assert "banking-domain-v1" not in text
    assert "shipping-domain-v1" not in text
