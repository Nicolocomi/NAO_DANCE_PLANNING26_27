# Incolla tutto il contenuto di questo file nel box Python di Choregraphe.
# Seleziona una mossa presente in RobotPositions e premi Play.
# Prova sul robot virtuale; leggi il tempo nel Log Viewer.

class MyClass(GeneratedClass):
    def __init__(self):
        GeneratedClass.__init__(self)

    def onLoad(self):
        pass

    def onUnload(self):
        pass

    def onInput_onStart(self):
        import math
        import time
        from naoqi import ALProxy

        ROBOT_IP = "127.0.0.1"
        PORT = 9559
        ACTION = "disco_groove"
        SPEED_FRACTION = 1.0

        dance_joints = [
            "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll",
            "LWristYaw", "LHand", "RShoulderPitch", "RShoulderRoll",
            "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand",
            "HeadYaw", "HeadPitch"
        ]
        dance_phrases = {'disco_groove': [(28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (42, 12, -75, -78, 0, 0.0, 42, -12, 75, 78, 0, 0.0, 0.0, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (52, 8, -80, -35, 0, 0.2, 52, -8, 80, 35, 0, 0.2, 0.0, 0.0), (42, 12, -75, -78, 0, 0.0, 42, -12, 75, 78, 0, 0.0, 0.0, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'side_step_groove': [(38, 38, -65, -45, 0, 0.1, 42, -20, 72, 65, 0, 0.2, -16, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (42, 20, -72, -65, 0, 0.2, 38, -38, 65, 45, 0, 0.1, 16, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (38, 38, -65, -45, 0, 0.1, 42, -20, 72, 65, 0, 0.2, -16, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (42, 20, -72, -65, 0, 0.2, 38, -38, 65, 45, 0, 0.1, 16, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'robot_pulse': [(52, 8, -80, -35, 0, 0.2, 52, -8, 80, 35, 0, 0.2, 0.0, 0.0), (42, 12, -75, -78, 0, 0.0, 42, -12, 75, 78, 0, 0.0, 0.0, 0.0), (52, 8, -80, -35, 0, 0.2, 52, -8, 80, 35, 0, 0.2, 0.0, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (52, 8, -80, -35, 0, 0.2, 52, -8, 80, 35, 0, 0.2, 0.0, 0.0), (42, 12, -75, -78, 0, 0.0, 42, -12, 75, 78, 0, 0.0, 0.0, 0.0), (52, 8, -80, -35, 0, 0.2, 52, -8, 80, 35, 0, 0.2, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'arm_wave_combo': [(18, 30, -65, -65, 0, 0.1, -38, -18, 70, 28, 0, 0.1, -12, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (38, 38, -65, -45, 0, 0.1, 42, -20, 72, 65, 0, 0.2, -16, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (18, 30, -65, -65, 0, 0.1, -38, -18, 70, 28, 0, 0.1, -12, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'party_punches': [(28, 12, -70, -82, 0, 0.0, 58, -35, 60, 42, 0, 0.0, -10, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (58, 35, -60, -42, 0, 0.0, 28, -12, 70, 82, 0, 0.0, 10, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (28, 12, -70, -82, 0, 0.0, 58, -35, 60, 42, 0, 0.0, -10, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0), (58, 35, -60, -42, 0, 0.0, 28, -12, 70, 82, 0, 0.0, 10, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'climax_reach': [(18, 30, -65, -65, 0, 0.1, -38, -18, 70, 28, 0, 0.1, -12, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (28, 12, -70, -82, 0, 0.0, 58, -35, 60, 42, 0, 0.0, -10, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (18, 30, -65, -65, 0, 0.1, -38, -18, 70, 28, 0, 0.1, -12, 0.0), (58, 35, -60, -42, 0, 0.0, 28, -12, 70, 82, 0, 0.0, 10, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'hello_wave': [(78, 16, -68, -49, 0, 0.0, 28, -20, 70, 65, 20, 1.0, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 70, 45, -20, 1.0, -8, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 70, 80, 40, 1.0, 8, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 70, 45, -20, 1.0, -8, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 70, 80, 40, 1.0, 8, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 70, 45, -20, 1.0, -8, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 70, 80, 40, 1.0, 8, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'wipe_forehead': [(78, 16, -68, -49, 0, 0.0, 20, -25, 45, 80, -40, 0.0, -10, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 55, 88, 20, 0.0, 10, 0.0), (78, 16, -68, -49, 0, 0.0, 20, -25, 45, 80, -40, 0.0, -10, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 55, 88, 20, 0.0, 10, 0.0), (78, 16, -68, -49, 0, 0.0, 20, -25, 45, 80, -40, 0.0, -10, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 55, 88, 20, 0.0, 10, 0.0), (78, 16, -68, -49, 0, 0.0, 28, -20, 70, 65, 20, 1.0, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'arm_to_sky': [(78, 16, -68, -49, 0, 0.0, -60, -40, 80, 20, 0, 0.0, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, -60, -40, 80, 20, 0, 0.0, 0.0, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, -60, -40, 80, 20, 0, 0.0, 0.0, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (28, 38, -60, -28, 0, 0.2, 28, -38, 60, 28, 0, 0.2, 0.0, 0.0), (78, 16, -68, -49, 0, 0.0, 78, -16, 68, 49, 0, 0.0, 0.0, 0.0)], 'seated_arm_to_sky': [(78, 16, -68, -49, 0, 0.0, -48, -28, 80, 30, 0, 0.0, 0.0, -5), (64, 18, -68, -45, 0, 0.0, -38, -28, 80, 35, 0, 0.0, 10, -3), (78, 16, -68, -49, 0, 0.0, -48, -28, 80, 30, 0, 0.0, 0.0, -5), (64, 18, -68, -45, 0, 0.0, -38, -28, 80, 35, 0, 0.0, 10, -3), (78, 16, -68, -49, 0, 0.0, -48, -28, 80, 30, 0, 0.0, 0.0, -5), (64, 18, -68, -45, 0, 0.0, -38, -28, 80, 35, 0, 0.0, 10, -3), (78, 16, -68, -49, 0, 0.0, -48, -28, 80, 30, 0, 0.0, 0.0, -5), (78, 16, -68, -49, 0, 0.0, -48, -28, 80, 30, 0, 0.0, 0.0, -5)]}
        phrase_for_action = {
            "Hello": "hello_wave",
            "Wipe Forehead": "wipe_forehead"
        }
        posture_actions = (
            "StandInit", "StandZero", "Sit", "SitRelax", "Stand", "Crouch"
        )
        supported_actions = (
            "StandInit", "Crouch", "Sit", "SitRelax", "Stand", "StandZero",
            "Wipe Forehead", "Hello", "rotation_handgun", "right_arm",
            "arm_to_sky", "seated_arm_to_sky", "disco_groove",
            "side_step_groove", "robot_pulse", "arm_wave_combo",
            "party_punches", "climax_reach", "double_movement",
            "arms_opening", "union_arms", "move_forward", "move_backward",
            "diagonal_left", "diagonal_right", "rotation_foot_Lleg",
            "rotation_foot_Rleg", "sing_with_me", "birthday_dance",
            "sprinkler", "workout"
        )
        arm_sequences = {
            "right_arm": [
                ((78, 16.6, -68.3, -49.2, 4.3, 0.0),
                 (78, -16.6, 68.3, 49.2, 4.3, 0.1), 2.0),
                (None, (-75.7, -79.8, -57.6, 2.2, 87.0, 0.35), 2.0),
                (None, (-79.8, -26.2, -57.6, 2.2, 87.0, 0.35), 1.0),
                (None, (11.0, 5.4, 68.3, 2.2, 88.5, 0.35), 4.0)
            ],
            "double_movement": [
                ((78.0, 39.9, -68.3, -57.2, 4.3, 0.0),
                 (78.0, -39.9, 68.3, 57.2, 95.0, 0.1), 2.0),
                (((77.8, 49.2, -68.5, -9.4, 4.5, 0.0)),
                 (77.7, -39.5, 33.7, 70.0, 95.0, 0.1), 1.2),
                ((77.8, 75.8, -68.5, -2.5, 4.5, 0.0),
                 (15.1, -10.6, 9.5, 70.0, 95.0, 0.1), 0.6),
                ((27.0, 29.8, -72.9, -27.2, 4.5, 0.0),
                 (62.4, -15.7, 51.7, 81.0, 105.0, 0.1), 1.4)
            ],
            "arms_opening": [
                ((78, 16.6, -68.3, -49.2, 4.3, 0.0),
                 (78, -16.6, 68.3, 49.2, 4.3, 0.1), 2.0),
                ((68.8, 14.3, -68.4, -53.9, 4.5, 0.0),
                 (24.9, 8.0, 67.8, 14.7, 79.3, 0.35), 1.2),
                ((66.7, -12.3, -69.0, -53.7, 4.6, 0.0),
                 (24.5, 16.9, 67.4, 14.9, 79.1, 0.35), 0.4),
                ((24.7, 51.8, -45.6, -14.7, -78.9, 0.0),
                 (24.7, -51.8, 45.6, 14.7, 78.9, 0.35), 2.2),
                ((66.4, 26.1, -106.0, -44.2, 4.6, 0.0),
                 (66.4, -26.1, 106.0, 80.0, 85.0, 0.35), 1.5)
            ],
            "union_arms": [
                ((80.2, 24.1, -90.0, -4.4, 0.5, 0.0),
                 (67.7, -26.4, 90.9, 88.5, 59.2, 0.35), 1.0),
                ((58.8, 25.9, -90.6, -25.0, -59.4, 0.0),
                 (58.8, -25.9, 90.6, 25.0, 3.2, 0.35), 2.0),
                ((45.9, -15.3, -90.6, -21.6, -59.4, 0.0),
                 (45.9, 15.3, 90.6, 21.6, 59.4, 0.35), 2.0),
                ((78.0, 16.6, -68.3, -49.2, 4.3, 0.0),
                 (78.0, -16.6, 68.3, 49.2, 4.3, 0.35), 1.5)
            ]
        }
        walking_actions = {
            "move_forward": (0.08, 0.0, 0.0),
            "move_backward": (-0.08, 0.0, 0.0),
            "diagonal_left": (0.03, 0.012, 0.0),
            "diagonal_right": (0.03, -0.012, 0.0)
        }
        behavior_actions = (
            "sing_with_me", "birthday_dance", "sprinkler", "workout"
        )

        if ACTION not in supported_actions:
            raise ValueError("Mossa non configurata: %s" % ACTION)
        motion = ALProxy("ALMotion", ROBOT_IP, PORT)
        phrase_name = phrase_for_action.get(ACTION, ACTION)

        if phrase_name in dance_phrases:
            poses = dance_phrases[phrase_name]
            start = time.time()
            for pose in poses:
                angles = []
                for joint_index, joint_name in enumerate(dance_joints):
                    angle = pose[joint_index]
                    if joint_name not in ("LHand", "RHand"):
                        angle = math.radians(angle)
                    angles.append(angle)
                motion.angleInterpolationWithSpeed(
                    dance_joints, angles, SPEED_FRACTION
                )
            print(
                "%s completato a %.0f%% in %.3f secondi"
                % (ACTION, SPEED_FRACTION * 100, time.time() - start)
            )
        elif ACTION in posture_actions:
            posture = ALProxy("ALRobotPosture", ROBOT_IP, PORT)
            start = time.time()
            posture.goToPosture(ACTION, SPEED_FRACTION)
            print(
                "%s completato a %.0f%% in %.3f secondi"
                % (ACTION, SPEED_FRACTION * 100, time.time() - start)
            )
        elif ACTION in walking_actions:
            start = time.time()
            motion.setMoveArmsEnabled(False, False)
            motion.moveTo(*walking_actions[ACTION])
            print(
                "%s completato con moveTo/configurazione massima in %.3f secondi"
                % (ACTION, time.time() - start)
            )
        elif ACTION in behavior_actions:
            behavior_manager = ALProxy("ALBehaviorManager", ROBOT_IP, PORT)
            if not behavior_manager.isBehaviorInstalled(ACTION):
                raise RuntimeError(
                    "Comportamento '%s' non installato sul robot virtuale." % ACTION
                )
            start = time.time()
            behavior_manager.runBehavior(ACTION)
            print(
                "%s completato a velocita' nativa in %.3f secondi"
                % (ACTION, time.time() - start)
            )
        elif ACTION in ("rotation_foot_Lleg", "rotation_foot_Rleg"):
            import motion as motion_constants
            posture = ALProxy("ALRobotPosture", ROBOT_IP, PORT)
            start = time.time()
            posture.goToPosture("StandInit", SPEED_FRACTION)
            motion.wbEnable(True)
            try:
                if ACTION == "rotation_foot_Rleg":
                    motion.wbFootState("Plane", "RLeg")
                    motion.wbFootState("Fixed", "LLeg")
                    torso_path = [0.0, 0.0, 0.0, 0.0, 0.0, 0.05]
                else:
                    motion.wbFootState("Fixed", "RLeg")
                    motion.wbFootState("Plane", "LLeg")
                    torso_path = [0.0, 0.0, 0.15, 0.0, 0.0, 0.05]
                motion.positionInterpolation(
                    "Torso", motion_constants.FRAME_ROBOT, torso_path,
                    63, 3.0, False
                )
            finally:
                motion.wbEnable(False)
            posture.goToPosture("StandInit", SPEED_FRACTION)
            print(
                "%s completato (traiettoria Torso a 3.0 s) in %.3f secondi"
                % (ACTION, time.time() - start)
            )
        elif ACTION == "rotation_handgun":
            start = time.time()
            left = (78.0, 16.6, -68.3, -49.2, 4.3, 0.0)
            right = (67.7, -26.4, 90.9, 88.5, 80.0, 0.35)
            def arm_values(values):
                return [math.radians(value) for value in values[:5]] + [values[5]]
            tasks = [
                motion.post.angleInterpolationWithSpeed(
                    "LArm", arm_values(left), SPEED_FRACTION
                ),
                motion.post.angleInterpolationWithSpeed(
                    "RArm", arm_values(right), SPEED_FRACTION
                )
            ]
            for task_id in tasks:
                motion.wait(task_id, 0)
            motion.angleInterpolationWithSpeed("RHand", 0.9, SPEED_FRACTION)
            motion.angleInterpolationWithSpeed("RHand", 0.05, SPEED_FRACTION)
            print(
                "%s completato a %.0f%% in %.3f secondi"
                % (ACTION, SPEED_FRACTION * 100, time.time() - start)
            )
        elif ACTION in arm_sequences:
            start = time.time()
            def arm_values(values):
                return [math.radians(value) for value in values[:5]] + [values[5]]
            for left, right, _phase_duration in arm_sequences[ACTION]:
                tasks = []
                if left is not None:
                    tasks.append(motion.post.angleInterpolationWithSpeed(
                        "LArm", arm_values(left), SPEED_FRACTION
                    ))
                if right is not None:
                    tasks.append(motion.post.angleInterpolationWithSpeed(
                        "RArm", arm_values(right), SPEED_FRACTION
                    ))
                for task_id in tasks:
                    motion.wait(task_id, 0)
            print(
                "%s completato a %.0f%% in %.3f secondi"
                % (ACTION, SPEED_FRACTION * 100, time.time() - start)
            )
        else:
            raise ValueError("Mossa non configurata: %s" % ACTION)

        self.onStopped()

    def onInput_onStop(self):
        self.onUnload()
        self.onStopped()
