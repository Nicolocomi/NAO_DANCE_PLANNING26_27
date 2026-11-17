import os
import re
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

    def test_every_a_star_candidate_has_a_runtime_handler(self):
        problem = planner.NaoProblem(
            start_action="StandInit",
            target_action="Hello",
            target_duration=15.0,
            target_energy=3,
            global_used_intermediates={},
            executable_intermediate_actions=planner.EXECUTABLE_INTERMEDIATE_ACTIONS,
        )
        for action in problem.candidates:
            with self.subTest(action=action):
                self.assertTrue(
                    positions.get_motion_phrase(action)
                    or action in positions.MOVE_TO_ACTIONS
                )

    def test_full_plan_keeps_competition_constraints(self):
        plan = planner.plan_choreography()
        actions = [step["action"] for step in plan["steps"]]

        self.assertEqual(planner.GOAL_RESERVE_SECONDS, 6.0)
        self.assertTrue(plan["is_time_ok"])
        self.assertAlmostEqual(plan["total_time"], 120.0, places=2)
        self.assertTrue(plan["is_variety_ok"])
        self.assertTrue(plan["is_space_ok"])
        self.assertEqual(actions[0], positions.START_POSITION)
        self.assertEqual(actions[-1], positions.GOAL_POSITION)
        self.assertEqual(
            plan["steps"][-1]["start_time"],
            120.0 - planner.GOAL_RESERVE_SECONDS,
        )
        self.assertEqual(plan["steps"][-1]["duration"], planner.GOAL_RESERVE_SECONDS)
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
        for previous, following in zip(plan["steps"], plan["steps"][1:]):
            self.assertAlmostEqual(previous["end_time"], following["start_time"])

        supported_actions = (
            set(positions.MOVE_TO_ACTIONS)
            | {
                action
                for action in actions
                if positions.get_motion_phrase(action) is not None
            }
            | {
                positions.START_POSITION,
                positions.GOAL_POSITION,
                "Sit",
                "SitRelax",
                "Stand",
                "StandZero",
            }
        )
        self.assertTrue(set(actions).issubset(supported_actions))

        for phrase_name, frames in positions.DANCE_PHRASES.items():
            with self.subTest(phrase=phrase_name):
                self.assertEqual(len(frames), 8)
                self.assertTrue(
                    all(left != right for left, right in zip(frames, frames[1:]))
                )

        with tempfile.TemporaryDirectory() as output_dir:
            planner.export_choregraphe_project(plan, output_dir)
            behavior_path = os.path.join(
                output_dir, "behavior_1", "behavior.xar"
            )
            root = ElementTree.parse(behavior_path)
            content = root.find(
                ".//{http://www.aldebaran-robotics.com/schema/choregraphe/project.xsd}content"
            ).text
            compile(content, behavior_path, "exec")
            exported_actions = re.findall(
                r"# PASSO \d+ \[[^\]]+\]: (.+?) \(",
                content,
            )
            self.assertEqual(exported_actions, actions)
            self.assertIn("proxy_ready.wait(15.0)", content)
            self.assertGreater(
                content.index("choreography_start = time.time()"),
                content.index("proxy_ready.wait(15.0)"),
            )
            self.assertIn(
                "choreography_stop_time = choreography_target_time - stop_margin_seconds",
                content,
            )
            self.assertIn(
                'run_posture_action("Crouch", 1.0, choreography_start + choreography_stop_time)',
                content,
            )
            self.assertIn(
                "remaining = choreography_start + choreography_stop_time - time.time()",
                content,
            )
            self.assertIn(
                "stop_margin_seconds = %.1f" % planner.EXECUTION_STOP_MARGIN_SECONDS,
                content,
            )
            self.assertNotIn("time.sleep(dur)", content)

            test_box_path = os.path.join(output_dir, "choregraphe_test_box.py")
            source_test_box = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "RobotPositions",
                "choregraphe_test_box.py",
            )
            with open(source_test_box, "r") as source_file:
                template = source_file.read()
            with open(test_box_path, "w") as test_box_file:
                test_box_file.write(template)
            planner.export_choregraphe_test_box(test_box_path)
            with open(test_box_path, "r") as test_box_file:
                generated_test_box = test_box_file.read()
            compile(generated_test_box, test_box_path, "exec")
            self.assertIn(repr(positions.MOVE_TO_ACTIONS), generated_test_box)
            self.assertNotIn('"__DANCE_PHRASES__"', generated_test_box)
            planner.export_choregraphe_test_box(test_box_path)
            with open(test_box_path, "r") as test_box_file:
                self.assertEqual(generated_test_box, test_box_file.read())


if __name__ == "__main__":
    unittest.main()
