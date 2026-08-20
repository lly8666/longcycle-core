from __future__ import annotations

import unittest

from longcycle.application.memory_topology import (
    TriggerDisposition,
    TriggerObservation,
    evaluate_trigger_promotion,
)


class MemoryTopologyTest(unittest.TestCase):
    def test_bridge_is_promoted_after_two_independent_shards_recall_it(self) -> None:
        decision = evaluate_trigger_promotion(
            (
                TriggerObservation("BRIDGE-INVENTORY", "UP-CHEMICALS", "CH-017", 1.0),
                TriggerObservation("BRIDGE-INVENTORY", "MID-LFP", "LFP-010", 0.9),
            )
        )
        self.assertEqual(decision.disposition, TriggerDisposition.PROMOTE)
        self.assertEqual(decision.distinct_shards, ("MID-LFP", "UP-CHEMICALS"))

    def test_single_shard_does_not_independently_promote_bridge(self) -> None:
        decision = evaluate_trigger_promotion(
            (
                TriggerObservation("BRIDGE-KWH-PER-VEHICLE", "DOWN-NEV", "NEV-004", 0.86),
                TriggerObservation("BRIDGE-KWH-PER-VEHICLE", "DOWN-NEV", "NEV-012", 1.0),
            )
        )
        self.assertEqual(decision.disposition, TriggerDisposition.INSUFFICIENT_INDEPENDENCE)

    def test_repeated_satellite_inside_one_shard_is_candidate_not_auto_promoted(self) -> None:
        decision = evaluate_trigger_promotion(
            (
                TriggerObservation("SAT-PHOSPHORUS-CHEMICALS", "MID-LFP", "LFP-004", 0.96),
                TriggerObservation("SAT-PHOSPHORUS-CHEMICALS", "MID-LFP", "LFP-020", 0.84),
            )
        )
        self.assertEqual(decision.disposition, TriggerDisposition.CANDIDATE)

    def test_existing_tier_a_route_is_not_created_twice(self) -> None:
        decision = evaluate_trigger_promotion(
            (TriggerObservation("DOWN-ESS", "MID-LFP", "LFP-013", 0.97),)
        )
        self.assertEqual(decision.disposition, TriggerDisposition.ALREADY_ROUTED)


if __name__ == "__main__":
    unittest.main()
