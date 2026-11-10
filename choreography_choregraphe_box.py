"""
choreography_choregraphe_box.py - Codice per il Box Python di Choregraphe.
Copia e incolla questo codice all'interno di un 'Python Box' in Choregraphe
per vedere NAO eseguire l'intera coreografia di 2 minuti nel visualizzatore 3D!
"""

import math
import time

try:
    from naoqi import ALProxy
except ImportError:
    pass


class MyClass(GeneratedClass):
    def __init__(self):
        GeneratedClass.__init__(self)

    def onLoad(self):
        pass

    def onUnload(self):
        pass

    def onInput_onStart(self):
        # 1. Inizializzazione Proxy
        try:
            motionProxy = ALProxy("ALMotion")
            postureProxy = ALProxy("ALRobotPosture")
            ttsProxy = ALProxy("ALTextToSpeech")
        except Exception:
            motionProxy = ALProxy("ALMotion", "127.0.0.1", 9559)
            postureProxy = ALProxy("ALRobotPosture", "127.0.0.1", 9559)
            ttsProxy = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)

        def arm_angles(pitch, roll, eyaw, eroll, wyaw=0.0, hand=0.0):
            return [
                math.radians(pitch),
                math.radians(roll),
                math.radians(eyaw),
                math.radians(eroll),
                math.radians(wyaw),
                hand
            ]

        # ----------------------------------------------------------------------
        # PASSO 1: StandInit (0.0s -> 4.0s)
        # ----------------------------------------------------------------------
        try:
            ttsProxy.post.say("Musica maestro!")
        except Exception:
            pass
        postureProxy.goToPosture("StandInit", 0.6)
        time.sleep(1.0)

        # ----------------------------------------------------------------------
        # PASSO 2: Birthday Dance (Braccia danzanti) (4.0s -> 19.0s)
        # ----------------------------------------------------------------------
        # Danza festosa con movimenti alternati e ritmati delle braccia
        for _ in range(3):
            # Braccia aperte in alto
            motionProxy.post.angleInterpolation("LArm", arm_angles(20, 45, -60, -80, 0, 0.8), 1.2, True)
            motionProxy.angleInterpolation("RArm", arm_angles(20, -45, 60, 80, 0, 0.8), 1.2, True)
            time.sleep(0.3)
            # Braccia ondeggianti a sinistra
            motionProxy.post.angleInterpolation("LArm", arm_angles(40, 20, -80, -30, -30, 0.5), 1.0, True)
            motionProxy.angleInterpolation("RArm", arm_angles(20, -10, 40, 60, 30, 0.5), 1.0, True)
            time.sleep(0.3)
            # Braccia ondeggianti a destra
            motionProxy.post.angleInterpolation("LArm", arm_angles(20, 10, -40, -60, -30, 0.5), 1.0, True)
            motionProxy.angleInterpolation("RArm", arm_angles(40, -20, 80, 30, 30, 0.5), 1.0, True)
            time.sleep(0.3)

        # ----------------------------------------------------------------------
        # PASSO 3: Hello (19.0s -> 23.5s) - POSIZIONE OBBLIGATORIA
        # ----------------------------------------------------------------------
        try:
            ttsProxy.post.say("Ciao a tutti!")
        except Exception:
            pass
        wave_up = arm_angles(-25.0, -20.0, 70.0, 65.0, 20.0, 1.0)
        wave_left = arm_angles(-25.0, -20.0, 70.0, 45.0, -20.0, 1.0)
        wave_right = arm_angles(-25.0, -20.0, 70.0, 80.0, 40.0, 1.0)
        motionProxy.angleInterpolation("RArm", wave_up, 1.0, True)
        for _ in range(2):
            motionProxy.angleInterpolation("RArm", wave_left, 0.35, True)
            motionProxy.angleInterpolation("RArm", wave_right, 0.35, True)
        postureProxy.goToPosture("StandInit", 0.6)

        # ----------------------------------------------------------------------
        # PASSO 4: Sing With Me (Chitarra Rock) (23.5s -> 37.5s)
        # ----------------------------------------------------------------------
        # Mano sinistra tiene il manico, mano destra plettra a tempo di rock
        neck_left = arm_angles(10.0, 20.0, -80.0, -60.0, 40.0, 0.5)
        strum_down = arm_angles(60.0, -10.0, 70.0, 85.0, -30.0, 0.8)
        strum_up = arm_angles(40.0, -15.0, 60.0, 65.0, 20.0, 0.8)
        motionProxy.post.angleInterpolation("LArm", neck_left, 1.2, True)
        motionProxy.angleInterpolation("RArm", strum_down, 1.2, True)
        for _ in range(6):
            motionProxy.angleInterpolation("RArm", strum_up, 0.45, True)
            motionProxy.angleInterpolation("RArm", strum_down, 0.45, True)
        postureProxy.goToPosture("StandInit", 0.6)

        # ----------------------------------------------------------------------
        # PASSO 5: Move Forward (37.5s -> 41.5s)
        # ----------------------------------------------------------------------
        try:
            motionProxy.moveTo(0.12, 0.0, 0.0)
        except Exception:
            time.sleep(4.0)

        # ----------------------------------------------------------------------
        # PASSO 6: StandZero (41.5s -> 45.0s) - POSIZIONE OBBLIGATORIA
        # ----------------------------------------------------------------------
        postureProxy.goToPosture("StandZero", 0.6)
        time.sleep(1.5)

        # ----------------------------------------------------------------------
        # PASSO 7: Workout (Ginnastica ritmica) (45.0s -> 57.0s)
        # ----------------------------------------------------------------------
        # Movimento di allenamento su e giù con entrambe le braccia
        for _ in range(3):
            # Push-up in alto
            motionProxy.post.angleInterpolation("LArm", arm_angles(-30, 20, -30, -20, 0, 0), 1.2, True)
            motionProxy.angleInterpolation("RArm", arm_angles(-30, -20, 30, 20, 0, 0), 1.2, True)
            time.sleep(0.4)
            # Bicipiti flessi
            motionProxy.post.angleInterpolation("LArm", arm_angles(30, 15, -70, -85, 0, 0.8), 1.2, True)
            motionProxy.angleInterpolation("RArm", arm_angles(30, -15, 70, 85, 0, 0.8), 1.2, True)
            time.sleep(0.4)
        postureProxy.goToPosture("StandInit", 0.6)

        # ----------------------------------------------------------------------
        # PASSO 8: Move Backward (57.0s -> 61.0s)
        # ----------------------------------------------------------------------
        try:
            motionProxy.moveTo(-0.12, 0.0, 0.0)
        except Exception:
            time.sleep(4.0)

        # ----------------------------------------------------------------------
        # PASSO 9: Sit (61.0s -> 66.0s) - POSIZIONE OBBLIGATORIA
        # ----------------------------------------------------------------------
        postureProxy.goToPosture("Sit", 0.6)
        time.sleep(1.0)

        # ----------------------------------------------------------------------
        # PASSO 10: SitRelax (66.0s -> 70.0s) - POSIZIONE OBBLIGATORIA
        # ----------------------------------------------------------------------
        postureProxy.goToPosture("SitRelax", 0.6)
        time.sleep(1.5)

        # ----------------------------------------------------------------------
        # PASSO 11: Stand (70.0s -> 74.5s) - POSIZIONE OBBLIGATORIA
        # ----------------------------------------------------------------------
        postureProxy.goToPosture("Stand", 0.6)
        time.sleep(1.0)

        # ----------------------------------------------------------------------
        # PASSO 12: Rotation Foot LLeg (74.5s -> 85.5s)
        # ----------------------------------------------------------------------
        # Rotazione espressiva del busto e bilanciamento
        motionProxy.angleInterpolation("Torso", [0, 0, 0, 0, 0, 0.05], 3.0, False)
        time.sleep(2.0)
        postureProxy.goToPosture("StandInit", 0.5)

        # ----------------------------------------------------------------------
        # PASSO 13: Rotation Foot RLeg (85.5s -> 96.5s)
        # ----------------------------------------------------------------------
        motionProxy.angleInterpolation("Torso", [0, 0, 0, 0, 0, -0.05], 3.0, False)
        time.sleep(2.0)
        postureProxy.goToPosture("StandInit", 0.5)

        # ----------------------------------------------------------------------
        # PASSO 14: Wipe Forehead (96.5s -> 101.5s) - POSIZIONE OBBLIGATORIA
        # ----------------------------------------------------------------------
        try:
            ttsProxy.post.say("Che fatica!")
        except Exception:
            pass
        wipe_reach = arm_angles(-10.0, -25.0, 40.0, 85.0, -40.0, 0.0)
        wipe_across = arm_angles(-15.0, -20.0, 50.0, 88.0, 20.0, 0.0)
        motionProxy.angleInterpolation("RArm", wipe_reach, 1.2, True)
        motionProxy.angleInterpolation("RArm", wipe_across, 1.2, True)
        time.sleep(0.5)
        postureProxy.goToPosture("StandInit", 0.6)

        # ----------------------------------------------------------------------
        # PASSO 15: Right Arm Disco (101.5s -> 107.5s)
        # ----------------------------------------------------------------------
        # Rotazione spettacolare del braccio sopra la testa stile disco dance
        r_up = arm_angles(-60.0, -40.0, 80.0, 20.0, 0.0, 0.9)
        r_circle = arm_angles(-40.0, -60.0, 60.0, 50.0, 40.0, 0.9)
        motionProxy.angleInterpolation("RArm", r_up, 1.5, True)
        motionProxy.angleInterpolation("RArm", r_circle, 1.5, True)
        postureProxy.goToPosture("StandInit", 0.6)

        # ----------------------------------------------------------------------
        # PASSO 16: Macho Man Biceps Pose! (107.5s -> 114.5s)
        # ----------------------------------------------------------------------
        # La mossa speciale Macho Man: flette entrambi i bicipiti con orgoglio
        biceps_left = arm_angles(25.0, 10.0, -75.0, -80.0, 0.0, 0.8)
        biceps_right = arm_angles(25.0, -10.0, 75.0, 80.0, 0.0, 0.8)
        motionProxy.post.angleInterpolation("LArm", biceps_left, 1.5, True)
        motionProxy.angleInterpolation("RArm", biceps_right, 1.5, True)
        time.sleep(2.5)  # Tiene la posa per il pubblico!
        postureProxy.goToPosture("StandInit", 0.6)

        # ----------------------------------------------------------------------
        # PASSO 17: Crouch (114.5s -> 119.5s) - POSIZIONE OBIETTIVO (GOAL)
        # ----------------------------------------------------------------------
        # Inchino finale e chiusura
        try:
            ttsProxy.post.say("Grazie a tutti!")
        except Exception:
            pass
        postureProxy.goToPosture("Crouch", 0.6)
        time.sleep(1.0)

        # Fine della coreografia
        self.onStopped()

