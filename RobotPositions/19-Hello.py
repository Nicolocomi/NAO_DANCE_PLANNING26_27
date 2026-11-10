''' NAO esegue il gesto di saluto (Hello) muovendo la mano destra '''

import math
import sys
import time

try:
    from naoqi import ALProxy
except ImportError:
    ALProxy = None


def _arm_angles(shoulder_pitch, shoulder_roll, elbow_yaw, elbow_roll, wrist_yaw=0.0, hand=1.0):
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
        print("[MOCK] Esecuzione Hello su %s:%s (naoqi non installato)" % (robot_ip, port))
        time.sleep(4.5)
        return

    try:
        motionProxy = ALProxy("ALMotion", robot_ip, port)
    except Exception as e:
        print("Errore creazione ALMotion: %s" % e)
        return

    try:
        ttsProxy = ALProxy("ALTextToSpeech", robot_ip, port)
        ttsProxy.say("Ciao a tutti!")
    except Exception:
        pass

    # Solleva il braccio destro per salutare
    names = "RArm"
    wave_up = _arm_angles(-25.0, -20.0, 70.0, 65.0, 20.0, 1.0)
    wave_left = _arm_angles(-25.0, -20.0, 70.0, 45.0, -20.0, 1.0)
    wave_right = _arm_angles(-25.0, -20.0, 70.0, 80.0, 40.0, 1.0)
    neutral = _arm_angles(78.0, -16.6, 68.3, 49.2, 0.0, 0.0)

    motionProxy.angleInterpolation(names, wave_up, 1.2, True)

    # Ondeggia la mano 2 volte
    for _ in range(2):
        motionProxy.angleInterpolation(names, wave_left, 0.4, True)
        motionProxy.angleInterpolation(names, wave_right, 0.4, True)

    # Ritorna in posizione neutra
    motionProxy.angleInterpolation(names, neutral, 1.0, True)


if __name__ == "__main__":
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9559
    main(robot_ip, port)

