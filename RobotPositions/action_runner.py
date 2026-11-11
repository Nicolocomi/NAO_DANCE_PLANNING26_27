# -*- coding: utf-8 -*-
"""Shared NAOqi execution helpers for the standalone action scripts."""

import math
import os
import sys

try:
    from naoqi import ALProxy
except ImportError:
    ALProxy = None


WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import positions


def _motion_proxy(robot_ip, port):
    if ALProxy is None:
        raise RuntimeError("NAOqi non disponibile: eseguire lo script nell'ambiente del robot.")
    return ALProxy("ALMotion", robot_ip, port)


def run_dance_phrase(action_name, robot_ip, port):
    motion_proxy = _motion_proxy(robot_ip, port)
    poses = positions.DANCE_PHRASES[action_name]
    duration = positions.get_duration(action_name)
    frame_times = [
        duration * frame / float(len(poses))
        for frame in range(1, len(poses) + 1)
    ]
    angle_lists = []
    time_lists = []
    for joint_index, joint_name in enumerate(positions.DANCE_JOINTS):
        joint_angles = [pose[joint_index] for pose in poses]
        if joint_name not in ("LHand", "RHand"):
            joint_angles = [math.radians(angle) for angle in joint_angles]
        angle_lists.append(joint_angles)
        time_lists.append(frame_times)

    motion_proxy.angleInterpolation(
        positions.DANCE_JOINTS, angle_lists, time_lists, True
    )


def run_action(action_name, robot_ip, port):
    run_dance_phrase(action_name, robot_ip, port)


def run_from_command_line(action_name):
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9559
    run_action(action_name, robot_ip, port)
