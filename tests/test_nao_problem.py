import os
import tempfile
import unittest
from xml.etree import ElementTree

import planner
import positions


class NaoProblemTests(unittest.TestCase):
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
        self.assertTrue(plan["is_variety_ok"])
        self.assertEqual(actions[0], positions.START_POSITION)
        self.assertEqual(actions[-1], positions.GOAL_POSITION)
        self.assertTrue(set(positions.MANDATORY_POSITIONS).issubset(actions))
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
