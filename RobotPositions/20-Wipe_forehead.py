''' NAO si asciuga la fronte per la stanchezza (Wipe Forehead) '''

import math
import sys
import time

try:
    from naoqi import ALProxy
except ImportError:
    ALProxy = None


def _arm_angles(shoulder_pitch, shoulder_roll, elbow_yaw, elbow_roll, wrist_yaw=0.0, hand=0.0):
    return [
        math.radians(shoulder_pitch),
        math.radians(shoulder_roll),
        math.radians(elbow_yaw),
        math.radians(elbow_roll),
        math.radians(wrist_yaw),
        hand
    ]


def main(robot_ip, port):
    if ALProxy is None:
        print("[MOCK] Esecuzione Wipe Forehead su %s:%s (naoqi non installato)" % (robot_ip, port))
        time.sleep(5.0)
        return

    try:
        motionProxy = ALProxy("ALMotion", robot_ip, port)
    except Exception as e:
        print("Errore creazione ALMotion: %s" % e)
        return

    try:
        ttsProxy = ALProxy("ALTextToSpeech", robot_ip, port)
        ttsProxy.say("Che fatica questo ballo!")
    except Exception:
        pass

    names = "RArm"
    reach_forehead = _arm_angles(-10.0, -25.0, 40.0, 85.0, -40.0, 0.0)
    wipe_across = _arm_angles(-15.0, -20.0, 50.0, 88.0, 20.0, 0.0)
    neutral = _arm_angles(78.0, -16.6, 68.3, 49.2, 0.0, 0.0)

    # Porta la mano alla fronte
    motionProxy.angleInterpolation(names, reach_forehead, 1.5, True)

    # Passa la mano sulla fronte
    motionProxy.angleInterpolation(names, wipe_across, 1.2, True)
    time.sleep(0.5)

    # Ritorna in posizione neutra
    motionProxy.angleInterpolation(names, neutral, 1.5, True)


if __name__ == "__main__":
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9559
    main(robot_ip, port)

