from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ChatAgentPromptContractsTest(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_post_seal_chatgpt_search_is_available_without_becoming_evidence(self) -> None:
        adapter = self._read("docs/development/prompts/github-connect-chat-adapter.md")
        shipping = self._read("docs/development/prompts/shipping-stage-two-source-validation.md")
        implementation = self._read("src/longcycle/application/memory_campaign.py")

        self.assertIn("may use fresh web search", implementation)
        self.assertIn("Seal 后 self-verification / source discovery / Evidence", adapter)
        self.assertIn("Search 可用就直接使用", shipping)
        self.assertNotIn("不得用普通网页浏览、搜索引擎", shipping)
        self.assertIn("搜索 citation 本身不是 Evidence", shipping)

    def test_existing_evidence_states_and_stop_rules_are_reused_without_tightening(
        self,
    ) -> None:
        adapter = self._read("docs/development/prompts/github-connect-chat-adapter.md")
        shipping = self._read("docs/development/prompts/shipping-stage-two-source-validation.md")

        for state in ("locator_verified", "content_verified", "materialized"):
            self.assertIn(state, adapter)
            self.assertIn(state, shipping)
        self.assertIn("Raw byte materialization 不是", adapter)
        self.assertIn("不新增任何固定网页数、来源数、下载数", shipping)
        self.assertIn("not_found != false", shipping)

    def test_missing_search_is_a_capability_blocker_not_a_source_gap(self) -> None:
        adapter = self._read("docs/development/prompts/github-connect-chat-adapter.md")
        shipping = self._read("docs/development/prompts/shipping-stage-two-source-validation.md")

        self.assertIn("CAPABILITY_BLOCKED_EXTERNAL_SOURCE", adapter)
        self.assertIn("工具缺失本身不是 `bounded_source_gap`", adapter)
        self.assertIn("工具缺失本身不得写成 bounded source gap", shipping)

    def test_shipping_rotation_prompt_is_phase_driven(self) -> None:
        prompt = self._read("docs/development/prompts/shipping-fresh-agent.md")

        self.assertNotIn("SHIP-MEM-V2-P001", prompt)
        self.assertIn("按 live cursor 路由阶段", prompt)
        self.assertIn("Seal 后 self-verification / source / Evidence", prompt)
        self.assertIn("不套用 blind 四-probe 配额", prompt)

    def test_prior_gap_is_preserved_while_only_its_completion_effect_is_superseded(
        self,
    ) -> None:
        contract = json.loads(self._read(".longcycle/workstreams/shipping-domain-v1/change-contract.json"))
        acceptance = "\n".join(contract["acceptance"])

        self.assertIn("bounded_source_gap remains immutable", acceptance)
        self.assertIn("pilot-completion effect is superseded", acceptance)
        self.assertIn("same single pilot", acceptance)
        self.assertIn("not a second trajectory", acceptance)


if __name__ == "__main__":
    unittest.main()
