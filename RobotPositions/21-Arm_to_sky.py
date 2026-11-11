import math
import sys

from naoqi import ALProxy


def main(robot_ip, port):
    motion_proxy = ALProxy("ALMotion", robot_ip, port)

    arm_raised = [
        math.radians(-60.0),
        math.radians(-40.0),
        math.radians(80.0),
        math.radians(20.0),
        math.radians(0.0),
        0.0,
    ]
    motion_proxy.angleInterpolation("RArm", arm_raised, 0.8, True)


if __name__ == "__main__":
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9559
    main(robot_ip, port)
