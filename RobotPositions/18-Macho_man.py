"""NAO strikes a brief, balanced double-biceps pose and returns to neutral."""

import math
import sys
import time

from naoqi import ALProxy


def _arm_angles(shoulder_pitch, shoulder_roll, elbow_yaw, elbow_roll, hand=0.8):
    return [
        math.radians(shoulder_pitch),
        math.radians(shoulder_roll),
        math.radians(elbow_yaw),
        math.radians(elbow_roll),
        math.radians(0.0),
        hand,
    ]


def main(robot_ip, port):
    motion_proxy = ALProxy("ALMotion", robot_ip, port)

    # Raise both forearms symmetrically, then return to the project's neutral arm pose.
    flex_left = _arm_angles(25.0, 10.0, -75.0, -80.0)
    flex_right = _arm_angles(25.0, -10.0, 75.0, 80.0)
    neutral_left = _arm_angles(78.0, 16.6, -68.3, -49.2, 0.0)
    neutral_right = _arm_angles(78.0, -16.6, 68.3, 49.2, 0.0)

    motion_proxy.post.angleInterpolation("LArm", flex_left, 1.5, True)
    motion_proxy.angleInterpolation("RArm", flex_right, 1.5, True)
    time.sleep(1.0)

    motion_proxy.post.angleInterpolation("LArm", neutral_left, 1.2, True)
    motion_proxy.angleInterpolation("RArm", neutral_right, 1.2, True)


if __name__ == "__main__":
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9559
    main(robot_ip, port)
