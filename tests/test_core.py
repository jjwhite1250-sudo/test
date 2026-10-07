"""Run the actual Lua 5.1 core, not a Python rewrite of its behavior."""
import json
from pathlib import Path
import sys
import unittest

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from sheets import compile_lua, read_sheets


class CampaignCoreTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.core = self.lua.execute((ROOT / 'src/invasion_core.lua').read_text())
        self.config = self.lua.execute(compile_lua(read_sheets()))
        self.state = self.core.new_state(self.config)

    def choose(self, candidates, coordinates, index=1):
        return self.core.choose_portal(
            self.lua.table_from([self.lua.table_from(c) for c in candidates]),
            lambda key: coordinates.get(key, (-1, -1)), lambda count: index)

    def reserve(self, request='request1', unit='berzerkers', army='army1', size=7):
        return self.core.reserve_reinforcement(self.state, self.config, request, unit, army, size)

    def test_portal_filters_bad_locations_and_deduplicates(self):
        chosen = self.choose([{'key': 'z', 'eligible': True}, {'key': 'a', 'eligible': True},
                              {'key': 'a', 'eligible': True}, {'key': 'ocean', 'eligible': True},
                              {'key': 'excluded', 'eligible': False}],
                             {'z': (10, 20), 'a': (5, 6), 'ocean': (-1, -1), 'excluded': (1, 1)}, 2)
        self.assertEqual(chosen.key, 'z')
        self.assertEqual(chosen.x, 10)

    def test_no_region_is_an_explicit_failure(self):
        self.assertEqual(self.choose([{'key': 'bad', 'eligible': True}], {}), (None, 'no_valid_region'))
        self.assertEqual(self.core.begin_arrival(self.state, None), (False, 'no_valid_region'))
        self.assertFalse(self.state.arrived)

    def test_rng_must_return_a_valid_integer(self):
        with self.assertRaises(Exception):
            self.choose([{'key': 'a', 'eligible': True}], {'a': (1, 2)}, 0)

    def test_arrival_is_confirmed_once(self):
        location = self.choose([{'key': 'a', 'eligible': True}], {'a': (1, 2)})
        self.assertTrue(self.core.begin_arrival(self.state, location))
        self.assertEqual(self.core.begin_arrival(self.state, location), (False, 'pending_arrival'))
        self.assertFalse(self.state.arrived)
        self.assertTrue(self.core.finish_arrival(self.state, True))
        self.assertEqual(self.core.begin_arrival(self.state, location), (False, 'already_arrived'))
        self.assertEqual(self.state.objective_region, 'a')

    def test_failed_spawn_can_retry_without_phantom_arrival(self):
        location = self.choose([{'key': 'a', 'eligible': True}], {'a': (1, 2)})
        self.core.begin_arrival(self.state, location)
        self.assertFalse(self.core.finish_arrival(self.state, False))
        self.assertFalse(self.state.arrived)
        self.assertTrue(self.core.begin_arrival(self.state, location))

    def test_turn_and_victory_rewards_are_distinct_and_idempotent(self):
        self.core.reward(self.state, self.config, '42', 'turn')
        self.core.reward(self.state, self.config, '42', 'victory')
        self.assertEqual(self.state.requisition, 450)
        self.assertEqual(self.core.reward(self.state, self.config, '42', 'victory'), (False, 'already_rewarded'))
        self.assertEqual(self.state.requisition, 450)

    def test_rewards_are_capped(self):
        self.state.requisition = 1990
        self.core.reward(self.state, self.config, '1', 'victory')
        self.assertEqual(self.state.requisition, 2000)

    def test_reinforcement_spends_only_once(self):
        self.assertTrue(self.reserve())
        self.assertEqual(self.state.requisition, 150)
        self.assertEqual(self.reserve(), (False, 'duplicate_request'))
        self.assertTrue(self.core.finish_reinforcement(self.state, self.config, 'request1', True))
        self.assertEqual(self.state.requisition, 150)
        self.assertEqual(self.reserve(), (False, 'duplicate_request'))

    def test_failed_grant_refunds_once(self):
        self.reserve()
        self.core.finish_reinforcement(self.state, self.config, 'request1', False)
        self.assertEqual(self.state.requisition, 300)
        self.assertEqual(self.core.finish_reinforcement(self.state, self.config, 'request1', False),
                         (False, 'no_pending_request'))
        self.assertEqual(self.state.requisition, 300)

    def test_reinforcement_rejects_invalid_unit_full_army_and_insufficient_funds(self):
        self.assertEqual(self.reserve(unit='not_a_unit'), (False, 'unknown_unit'))
        self.assertEqual(self.reserve(size=20), (False, 'army_full'))
        self.state.requisition = 74
        self.assertEqual(self.reserve(unit='cultists'), (False, 'insufficient_requisition'))
        self.assertEqual(self.state.requisition, 74)

    def test_pending_operations_cannot_overfill_the_same_army(self):
        self.assertTrue(self.reserve(size=19))
        self.assertEqual(self.reserve(request='request2', size=19), (False, 'army_operation_pending'))

    def test_rewards_respect_reserved_funds_at_cap(self):
        self.state.requisition = 2000
        self.reserve()
        self.core.reward(self.state, self.config, '1', 'victory')
        self.assertEqual(self.state.requisition, 1850)
        self.core.finish_reinforcement(self.state, self.config, 'request1', False)
        self.assertEqual(self.state.requisition, 2000)

    def test_objective_requires_capture_of_arrival_region(self):
        self.assertFalse(self.core.settlement_captured(self.state, 'a'))
        location = self.choose([{'key': 'a', 'eligible': True}], {'a': (1, 2)})
        self.core.begin_arrival(self.state, location)
        self.core.finish_arrival(self.state, True)
        self.assertFalse(self.core.settlement_captured(self.state, 'b'))
        self.assertTrue(self.core.settlement_captured(self.state, 'a'))
        self.assertTrue(self.state.objective_completed)

    def test_serialized_state_retains_arrival_and_reward_ids(self):
        def as_dict(table):
            return {key: as_dict(value) if hasattr(value, 'items') else value for key, value in table.items()}

        location = self.choose([{'key': 'a', 'eligible': True}], {'a': (1, 2)})
        self.core.begin_arrival(self.state, location)
        self.core.finish_arrival(self.state, True)
        self.core.reward(self.state, self.config, 'battle1', 'victory')
        saved = json.loads(json.dumps(as_dict(self.state)))
        fresh_lua = LuaRuntime(unpack_returned_tuples=True)
        fresh_core = fresh_lua.execute((ROOT / 'src/invasion_core.lua').read_text())
        config = fresh_lua.execute(compile_lua(read_sheets()))
        restored = fresh_lua.table_from(saved, recursive=True)
        self.assertEqual(fresh_core.begin_arrival(restored, None), (False, 'already_arrived'))
        self.assertEqual(fresh_core.reward(restored, config, 'battle1', 'victory'), (False, 'already_rewarded'))
        self.assertEqual(restored.requisition, 400)


if __name__ == '__main__':
    unittest.main()
