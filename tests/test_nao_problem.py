import os
import tempfile
import unittest
from xml.etree import ElementTree

import planner
import positions


class NaoProblemTests(unittest.TestCase):
    def test_explicit_incompatibilities_reference_known_actions(self):
        for pair in positions.EXPLICIT_INCOMPATIBILITIES:
            with self.subTest(pair=pair):
                self.assertTrue(all(action in positions.ACTIONS for action in pair))
                self.assertFalse(positions.is_transition_valid(*pair))

    def test_goal_position_is_terminal_for_posture_agnostic_actions(self):
        self.assertFalse(
            positions.is_transition_valid("Crouch", "seated_arm_to_sky")
        )

    def test_seated_arm_to_sky_requires_and_preserves_sitting_posture(self):
        self.assertEqual(
            positions.ACTIONS["seated_arm_to_sky"]["pre"], positions.SITTING
        )
        self.assertEqual(
            positions.ACTIONS["seated_arm_to_sky"]["post"], positions.SITTING
        )
        self.assertTrue(
            positions.is_transition_valid("Sit", "seated_arm_to_sky")
        )
        self.assertFalse(
            positions.is_transition_valid("Stand", "seated_arm_to_sky")
        )

    def test_aima_segment_respects_cue_and_posture_transitions(self):
        segment, _ = planner.a_star_music_segment(
            start_action="StandInit",
            target_action="Hello",
            target_duration=15.0,
            target_energy=3,
            global_used_intermediates={},
            required_first_action="disco_groove",
        )

        self.assertEqual(segment[0], "disco_groove")
        self.assertEqual(segment[-1], "Hello")
        for previous, following in zip(
            ["StandInit"] + segment[:-1], segment
        ):
            self.assertTrue(positions.is_transition_valid(previous, following))

    def test_full_plan_keeps_competition_constraints(self):
        plan = planner.plan_choreography()
        actions = [step["action"] for step in plan["steps"]]

        self.assertTrue(plan["is_time_ok"])
        self.assertAlmostEqual(plan["total_time"], 120.0, places=2)
        self.assertTrue(plan["is_variety_ok"])
        self.assertEqual(actions[0], positions.START_POSITION)
        self.assertEqual(actions[-1], positions.GOAL_POSITION)
        self.assertTrue(set(positions.MANDATORY_POSITIONS).issubset(actions))
        sit_index = actions.index("Sit")
        seated_arm_index = actions.index("seated_arm_to_sky")
        sit_relax_index = actions.index("SitRelax")
        stand_index = actions.index("Stand")
        self.assertLess(sit_index, seated_arm_index)
        self.assertLess(seated_arm_index, sit_relax_index)
        self.assertLess(sit_relax_index, stand_index)
        for previous, following in zip(actions, actions[1:]):
            self.assertTrue(positions.is_transition_valid(previous, following))
        with tempfile.TemporaryDirectory() as output_dir:
            planner.export_choregraphe_project(plan, output_dir)
            behavior_path = os.path.join(
                output_dir, "behavior_1", "behavior.xar"
            )
            ElementTree.parse(behavior_path)


if __name__ == "__main__":
    unittest.main()
