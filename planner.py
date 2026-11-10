"""
planner.py - Modulo di AI Planning Music-Driven per la NAO Planning Competition.
Fundamentals of Artificial Intelligence - Università di Bologna (UniBo)

Colonna Sonora Ufficiale: Daft Punk - 'One More Time' (123 BPM, 4/4)
Durata: 120.0 Secondi (Esattamente 2:00 minuti)

Caratteristiche del Planning Musicale:
- Allineamento Metrico (123 BPM): ogni battuta dura ~1.95s; i cambi di sezione avvengono
  su frasi musicali di 8 battute (~15.6s) o 16 battute (~31.2s).
- Riconoscimento delle Sezioni:
    1. Intro (Horns Hook): Risveglio del robot e saluto al pubblico.
    2. Verse 1 ('One more time, we're gonna celebrate'): Inizio del groove e passi avanti.
    3. Chorus 1 ('A celebration alright!'): Drop chitarra elettrica ed esplosione di festa.
    4. Breakdown 1 ('Music's got me feeling...'): La cassa sparisce! Pausa seduta sul tappeto d'archi.
    5. Breakdown 2 (Snare Riser): Rullante in crescendo, il robot si rialza energico.
    6. Mega Drop Climax ('ONE MORE TIME!'): Apice dello show! Workout, bicipiti Macho Man e sudore.
    7. Outro (Fade Out): Inchino finale e chiusura ad esattamente 120 secondi.
- Funzione di Valutazione A* Multi-Obiettivo:
    f(n) = g(n) + h(n)
    con penalità per discrepanza dall'energia della canzone, bonus di novità e aderenza al beat.
"""

import heapq
import json
import os
import positions

# ==============================================================================
# 1. STRUTTURA METRICO-MUSICALE DI "ONE MORE TIME" (DAFT PUNK)
# ==============================================================================
DAFT_PUNK_SONG = {
    "title": "One More Time",
    "artist": "Daft Punk",
    "bpm": 123,
    "seconds_per_bar": 1.951,  # 4/4 a 123 BPM
    "total_target_time": 120.0
}

DAFT_PUNK_SECTIONS = [
    {
        "id": 1,
        "name": "Intro: The Horns Hook",
        "bars": 8,
        "target_duration": 16.0,
        "target_energy": 3,
        "target_mandatory": "Hello",
        "lyric": "Riff sintetico di fiati. NAO si attiva nel groove e saluta il pubblico.",
        "weight": 1.0
    },
    {
        "id": 2,
        "name": "Verse 1: 'One more time, we're gonna celebrate...'",
        "bars": 8,
        "target_duration": 18.0,
        "target_energy": 3,
        "target_mandatory": "StandZero",
        "lyric": "Entra la voce robotica e il basso funky. Danza a tutto corpo e posa scenica.",
        "weight": 1.2
    },
    {
        "id": 3,
        "name": "Chorus 1: First Party Drop",
        "bars": 10,
        "target_duration": 19.5,
        "target_energy": 5,
        "target_mandatory": "Sit",
        "lyric": "Drop del ritornello: assolo di chitarra rock sul campionamento prima del break.",
        "weight": 1.3
    },
    {
        "id": 4,
        "name": "Breakdown: Drums Cut Out ('Music's got me feeling...')",
        "bars": 6,
        "target_duration": 4.0,
        "target_energy": 1,
        "target_mandatory": "SitRelax",
        "lyric": "La cassa si ferma! Atmosfera eterea e sospesa: NAO si rilassa seduto a terra.",
        "weight": 0.0  # Transizione diretta seduta
    },
    {
        "id": 5,
        "name": "Riser: Snare Roll Buildup",
        "bars": 6,
        "target_duration": 4.5,
        "target_energy": 3,
        "target_mandatory": "Stand",
        "lyric": "Rullante in crescendo travolgente: NAO scatta in piedi pronto all'esplosione!",
        "weight": 0.0  # Alzata in piedi
    },
    {
        "id": 6,
        "name": "Mega Drop & Climax: 'ONE MORE TIME!'",
        "bars": 20,
        "target_duration": 39.0,
        "target_energy": 5,
        "target_mandatory": "Wipe Forehead",
        "lyric": "Cassa a palla! Workout sfrenato, footwork, posa bicipiti Macho Man e asciugamento fronte.",
        "weight": 2.8
    },
    {
        "id": 7,
        "name": "Outro: Fade Out & Bow",
        "bars": 8,
        "target_duration": 15.0,
        "target_energy": 2,
        "target_mandatory": "Crouch",
        "lyric": "Il beat sfuma dolcemente: passi d'onore e solenne inchino finale in ginocchio.",
        "weight": 1.0
    }
]


# ==============================================================================
# 2. STRUTTURA DEL NODO PER L'ALGORITMO A*
# ==============================================================================
class AStarNode(object):
    def __init__(self, action, current_duration, path, used_intermediates, f_cost=0.0):
        self.action = action
        self.current_duration = current_duration
        self.path = path
        self.used_intermediates = used_intermediates
        self.f_cost = f_cost

    def __lt__(self, other):
        return self.f_cost < other.f_cost


# ==============================================================================
# 3. ALGORITMO A* PER UN SINGOLO SEGMENTO MUSICALE
# ==============================================================================
def a_star_music_segment(start_action, target_action, target_duration, target_energy, global_used_intermediates):
    """
    Ricerca A* guidata da vincoli musicali (durata della sezione ed energia del brano).
    """
    target_post_dur = positions.get_duration(target_action)

    # Transizione diretta se il budget è coperto solo dall'azione obiettivo
    if target_duration <= target_post_dur and positions.is_transition_valid(start_action, target_action):
        return [target_action], set()

    open_set = []
    initial_node = AStarNode(
        action=start_action,
        current_duration=0.0,
        path=[],
        used_intermediates=set(),
        f_cost=0.0
    )
    heapq.heappush(open_set, (0.0, initial_node))

    candidate_intermediates = [
        act for act, data in positions.ACTIONS.items()
        if data["type"] in ("intermediate", "crg")
    ]

    best_solution = None
    best_error = float("inf")
    visited = set()

    while open_set:
        _, current_node = heapq.heappop(open_set)

        state_signature = (
            current_node.action,
            round(current_node.current_duration, 1),
            tuple(sorted(current_node.path))
        )
        if state_signature in visited:
            continue
        visited.add(state_signature)

        # Se possiamo chiudere il segmento con la mossa obbligatoria target
        if positions.is_transition_valid(current_node.action, target_action):
            total_seg_duration = current_node.current_duration + target_post_dur
            error = abs(total_seg_duration - target_duration)
            if error < best_error:
                best_error = error
                best_solution = current_node.path + [target_action]
                if error <= 1.0:
                    break

        if current_node.current_duration > target_duration + 4.0:
            continue
        if len(current_node.path) >= 4:
            continue

        for next_action in candidate_intermediates:
            if not positions.is_transition_valid(current_node.action, next_action):
                continue
            if current_node.path and current_node.path[-1] == next_action:
                continue

            next_duration = current_node.current_duration + positions.get_duration(next_action)
            next_used = set(current_node.used_intermediates)
            next_used.add(next_action)

            # --- COSTO ENERGETICO: vicinanza all'energia del brano in quel momento ---
            act_energy = positions.get_energy(next_action)
            energy_penalty = abs(act_energy - target_energy) * 1.5

            # --- BONUS NOVITÀ & PENALITÀ RIPETIZIONE ---
            is_new = (next_action not in global_used_intermediates) and (next_action not in current_node.used_intermediates)
            novelty_bonus = 5.0 if is_new else -3.0  # Penalizza il riuso per favorire la varietà

            g_cost = len(current_node.path) * 1.5 + energy_penalty - novelty_bonus

            # --- EURISTICA TEMPORALE ---
            projected_duration = next_duration + target_post_dur
            h_cost = abs(target_duration - projected_duration)

            f_cost = g_cost + h_cost

            successor_node = AStarNode(
                action=next_action,
                current_duration=next_duration,
                path=current_node.path + [next_action],
                used_intermediates=next_used,
                f_cost=f_cost
            )
            heapq.heappush(open_set, (f_cost, successor_node))

    if best_solution is None:
        best_solution = [target_action]

    newly_used = {
        act for act in best_solution[:-1]
        if positions.ACTIONS[act]["type"] in ("intermediate", "crg")
    }
    return best_solution, newly_used


# ==============================================================================
# 4. PIANIFICATORE GLOBALE MUSIC-DRIVEN
# ==============================================================================
def plan_choreography(target_total_time=120.0, song_sections=None, min_distinct_intermediates=5):
    """
    Pianifica l'intera coreografia sincronizzandola con la timeline di Daft Punk - One More Time.
    """
    if song_sections is None:
        song_sections = DAFT_PUNK_SECTIONS

    full_action_sequence = [positions.START_POSITION]
    global_used_intermediates = set()
    total_running_time = positions.get_duration(positions.START_POSITION)

    total_sections = len(song_sections)
    step_metadata = [{
        "section_name": "Inizio",
        "lyric": "NAO in attesa del primo beat."
    }]

    for i in range(total_sections):
        sec = song_sections[i]
        w_start = full_action_sequence[-1]
        w_end = sec["target_mandatory"]

        # Adattamento dinamico del budget temporale
        remaining_time = target_total_time - total_running_time
        remaining_weights = sum(song_sections[j]["weight"] for j in range(i, total_sections))

        if sec["weight"] > 0 and remaining_weights > 0:
            future_mandatory_min = sum(positions.get_duration(song_sections[k]["target_mandatory"]) for k in range(i, total_sections))
            available_for_intermediates = max(0.0, remaining_time - future_mandatory_min)
            allocated_budget = positions.get_duration(w_end) + available_for_intermediates * (sec["weight"] / remaining_weights)
        else:
            allocated_budget = positions.get_duration(w_end)

        sub_sequence, newly_used = a_star_music_segment(
            start_action=w_start,
            target_action=w_end,
            target_duration=allocated_budget,
            target_energy=sec["target_energy"],
            global_used_intermediates=global_used_intermediates
        )

        global_used_intermediates.update(newly_used)
        full_action_sequence.extend(sub_sequence)

        for act in sub_sequence:
            total_running_time += positions.get_duration(act)
            step_metadata.append({
                "section_name": sec["name"],
                "lyric": sec["lyric"]
            })

    # Creazione della timeline dettagliata con accenti musicali
    plan_steps = []
    current_t = 0.0
    for idx, act in enumerate(full_action_sequence):
        act_data = positions.ACTIONS[act]
        dur = act_data["duration"]
        meta = step_metadata[idx]

        step_info = {
            "step": idx + 1,
            "action": act,
            "type": act_data["type"],
            "posture": act_data["post"],
            "energy": act_data.get("energy", 3),
            "start_time": round(current_t, 2),
            "duration": dur,
            "end_time": round(current_t + dur, 2),
            "section": meta["section_name"],
            "lyric_cue": meta["lyric"],
            "file": act_data["file"],
            "description": act_data["description"]
        }
        plan_steps.append(step_info)
        current_t += dur

    is_time_ok = abs(total_running_time - target_total_time) <= 2.0
    is_variety_ok = len(global_used_intermediates) >= min_distinct_intermediates

    return {
        "song": DAFT_PUNK_SONG["title"],
        "artist": DAFT_PUNK_SONG["artist"],
        "bpm": DAFT_PUNK_SONG["bpm"],
        "steps": plan_steps,
        "total_time": round(total_running_time, 2),
        "distinct_intermediates": sorted(list(global_used_intermediates)),
        "is_time_ok": is_time_ok,
        "is_variety_ok": is_variety_ok
    }


# ==============================================================================
# 5. ESPORTATORE AUTOMATICO PER CHOREGRAPHE
# ==============================================================================
def export_choregraphe_project(plan_result, project_dir="NAO_Choreography_Project"):
    os.makedirs(os.path.join(project_dir, "behavior_1"), exist_ok=True)

    steps_code = []
    for step in plan_result["steps"]:
        act = step["action"]
        desc = step["description"]
        dur = step["duration"]
        t_start = step["start_time"]
        t_end = step["end_time"]
        step_num = step["step"]
        sec_name = step.get("section", "")
        lyric = step.get("lyric_cue", "")

        steps_code.append("        # ======================================================================")
        steps_code.append("        # PASSO %02d [%s]: %s (%.1fs -> %.1fs)" % (step_num, sec_name, act, t_start, t_end))
        steps_code.append("        # Evento Musicale: %s" % lyric)
        steps_code.append("        # ======================================================================")

        if act == "StandInit":
            steps_code.append('        try:\n            ttsProxy.post.say("One more time!")\n        except Exception:\n            pass')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)\n        time.sleep(1.0)')
        elif act == "Crouch":
            steps_code.append('        try:\n            ttsProxy.post.say("Merci Daft Punk!")\n        except Exception:\n            pass')
            steps_code.append('        postureProxy.goToPosture("Crouch", 0.6)\n        time.sleep(1.0)')
        elif act in ("Sit", "SitRelax", "Stand", "StandZero"):
            steps_code.append('        postureProxy.goToPosture("%s", 0.6)\n        time.sleep(1.0)' % act)
        elif act == "Hello":
            steps_code.append('        wave_up = arm_angles(-25.0, -20.0, 70.0, 65.0, 20.0, 1.0)')
            steps_code.append('        wave_left = arm_angles(-25.0, -20.0, 70.0, 45.0, -20.0, 1.0)')
            steps_code.append('        wave_right = arm_angles(-25.0, -20.0, 70.0, 80.0, 40.0, 1.0)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", wave_up, 1.0, True)')
            steps_code.append('        for _ in range(2):\n            motionProxy.angleInterpolation("RArm", wave_left, 0.35, True)\n            motionProxy.angleInterpolation("RArm", wave_right, 0.35, True)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "Wipe Forehead":
            steps_code.append('        try:\n            ttsProxy.post.say("Che fatica!")\n        except Exception:\n            pass')
            steps_code.append('        wipe_reach = arm_angles(-10.0, -25.0, 40.0, 85.0, -40.0, 0.0)')
            steps_code.append('        wipe_across = arm_angles(-15.0, -20.0, 50.0, 88.0, 20.0, 0.0)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", wipe_reach, 1.2, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", wipe_across, 1.2, True)\n        time.sleep(0.5)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "macho_man":
            steps_code.append('        biceps_left = arm_angles(25.0, 10.0, -75.0, -80.0, 0.0, 0.8)')
            steps_code.append('        biceps_right = arm_angles(25.0, -10.0, 75.0, 80.0, 0.0, 0.8)')
            steps_code.append('        motionProxy.post.angleInterpolation("LArm", biceps_left, 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", biceps_right, 1.5, True)\n        time.sleep(2.0)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "move_forward":
            steps_code.append('        try:\n            motionProxy.moveTo(0.12, 0.0, 0.0)\n        except Exception:\n            time.sleep(4.0)')
        elif act == "move_backward":
            steps_code.append('        try:\n            motionProxy.moveTo(-0.12, 0.0, 0.0)\n        except Exception:\n            time.sleep(4.0)')
        elif act == "diagonal_left":
            steps_code.append('        try:\n            motionProxy.moveTo(0.10, 0.08, 0.0)\n        except Exception:\n            time.sleep(4.0)')
        elif act == "diagonal_right":
            steps_code.append('        try:\n            motionProxy.moveTo(0.10, -0.08, 0.0)\n        except Exception:\n            time.sleep(4.0)')
        elif act == "sing_with_me":
            steps_code.append('        neck_left = arm_angles(10.0, 20.0, -80.0, -60.0, 40.0, 0.5)')
            steps_code.append('        strum_down = arm_angles(60.0, -10.0, 70.0, 85.0, -30.0, 0.8)')
            steps_code.append('        strum_up = arm_angles(40.0, -15.0, 60.0, 65.0, 20.0, 0.8)')
            steps_code.append('        motionProxy.post.angleInterpolation("LArm", neck_left, 1.2, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", strum_down, 1.2, True)')
            steps_code.append('        for _ in range(6):\n            motionProxy.angleInterpolation("RArm", strum_up, 0.45, True)\n            motionProxy.angleInterpolation("RArm", strum_down, 0.45, True)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "workout":
            steps_code.append('        for _ in range(3):')
            steps_code.append('            motionProxy.post.angleInterpolation("LArm", arm_angles(-30, 20, -30, -20, 0, 0), 1.2, True)')
            steps_code.append('            motionProxy.angleInterpolation("RArm", arm_angles(-30, -20, 30, 20, 0, 0), 1.2, True)\n            time.sleep(0.4)')
            steps_code.append('            motionProxy.post.angleInterpolation("LArm", arm_angles(30, 15, -70, -85, 0, 0.8), 1.2, True)')
            steps_code.append('            motionProxy.angleInterpolation("RArm", arm_angles(30, -15, 70, 85, 0, 0.8), 1.2, True)\n            time.sleep(0.4)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "birthday_dance":
            steps_code.append('        for _ in range(3):')
            steps_code.append('            motionProxy.post.angleInterpolation("LArm", arm_angles(20, 45, -60, -80, 0, 0.8), 1.2, True)')
            steps_code.append('            motionProxy.angleInterpolation("RArm", arm_angles(20, -45, 60, 80, 0, 0.8), 1.2, True)\n            time.sleep(0.3)')
            steps_code.append('            motionProxy.post.angleInterpolation("LArm", arm_angles(40, 20, -80, -30, -30, 0.5), 1.0, True)')
            steps_code.append('            motionProxy.angleInterpolation("RArm", arm_angles(20, -10, 40, 60, 30, 0.5), 1.0, True)\n            time.sleep(0.3)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "rotation_foot_Lleg":
            steps_code.append('        try:\n            motionProxy.angleInterpolation("Torso", [0, 0, 0, 0, 0, 0.05], 3.0, False)\n            time.sleep(2.0)\n        except Exception:\n            time.sleep(5.0)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.5)')
        elif act == "rotation_foot_Rleg":
            steps_code.append('        try:\n            motionProxy.angleInterpolation("Torso", [0, 0, 0, 0, 0, -0.05], 3.0, False)\n            time.sleep(2.0)\n        except Exception:\n            time.sleep(5.0)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.5)')
        elif act == "right_arm":
            steps_code.append('        r_up = arm_angles(-60.0, -40.0, 80.0, 20.0, 0.0, 0.9)')
            steps_code.append('        r_circle = arm_angles(-40.0, -60.0, 60.0, 50.0, 40.0, 0.9)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", r_up, 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", r_circle, 1.5, True)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "union_arms":
            steps_code.append('        motionProxy.post.angleInterpolation("LArm", arm_angles(10, 10, -80, -80, 0, 0.5), 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", arm_angles(10, -10, 80, 80, 0, 0.5), 1.5, True)\n        time.sleep(1.0)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        else:
            steps_code.append('        time.sleep(%.1f)' % dur)

    all_steps_python = "\n".join(steps_code)

    xar_template = '''<?xml version="1.0" encoding="UTF-8" ?>
<ChoregrapheProject xmlns="http://www.aldebaran-robotics.com/schema/choregraphe/project.xsd" xar_version="3">
    <Box name="root" id="-1" tooltip="Coreografia NAO sincronizzata con Daft Punk - One More Time" x="0" y="0">
        <bitmap>media/images/box/root.png</bitmap>
        <script language="4">
            <content>
                <![CDATA[
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

    def onInput_onStop(self):
        self.onUnload()
        self.onStopped()

    def onInput_onStart(self):
        # NOTA: La musica va avviata ESTERNAMENTE (da main.py o manualmente).
        # NON usare subprocess/os dentro Choregraphe: crasha il simulatore.

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

''' + all_steps_python + '''

        self.onStopped()
]]>
            </content>
        </script>
        <Input name="onLoad" type="1" type_size="1" nature="0" inner="1" tooltip="Signal sent when diagram is loaded." id="1" />
        <Input name="onStart" type="1" type_size="1" nature="2" inner="0" tooltip="Box behavior starts when a signal is received on this input." id="2" />
        <Input name="onStop" type="1" type_size="1" nature="3" inner="0" tooltip="Box behavior stops when a signal is received on this input." id="3" />
        <Output name="onStopped" type="1" type_size="1" nature="1" inner="0" tooltip="Signal sent when box behavior is finished." id="4" />
    </Box>
</ChoregrapheProject>
'''

    with open(os.path.join(project_dir, "behavior_1", "behavior.xar"), "w") as f:
        f.write(xar_template)

    return os.path.join(project_dir, "NAO_Choreography.pml")


# ==============================================================================
# 6. STAMPA DELLA TIMELINE MUSICALE
# ==============================================================================
def print_plan_summary(plan_result):
    print("=" * 95)
    print("      NAO DANCE PLANNER - SINCRONIZZAZIONE: DAFT PUNK - 'ONE MORE TIME' (123 BPM)")
    print("=" * 95)
    print("%-4s | %-15s | %-18s | %-5s | %-38s" % (
        "Step", "Timeline", "Azione (Tipo)", "Energ", "Evento / Frase Musicale"
    ))
    print("-" * 95)

    for s in plan_result["steps"]:
        action_label = "%s (%s)" % (s["action"], s["type"][:4])
        energy_stars = "*" * s["energy"]
        time_str = "%5.1fs - %5.1fs" % (s["start_time"], s["end_time"])
        lyric_short = s["lyric_cue"][:38]
        print("%-4d | %-15s | %-18s | %-5s | %-38s" % (
            s["step"],
            time_str,
            action_label,
            energy_stars,
            lyric_short
        ))

    print("=" * 95)
    print("RIEPILOGO VINCOLI & SINCRONIA:")
    print(" - Durata totale: %.1f secondi (Target: 120.0s) -> %s" % (
        plan_result["total_time"],
        "SODDISFATTO [OK]" if plan_result["is_time_ok"] else "FALLITO"
    ))
    print(" - Mosse intermedie distinte usate: %d (Minimo: 5) -> %s" % (
        len(plan_result["distinct_intermediates"]),
        "SODDISFATTO [OK]" if plan_result["is_variety_ok"] else "FALLITO"
    ))
    print(" - Elenco intermedie: %s" % ", ".join(plan_result["distinct_intermediates"]))
    print("=" * 95)


if __name__ == "__main__":
    result = plan_choreography(target_total_time=120.0)
    print_plan_summary(result)

    with open("choreography_plan.json", "w") as fp:
        json.dump(result, fp, indent=2)

    export_choregraphe_project(result)
    print("\nProgetto Choregraphe aggiornato con successo per 'One More Time'!")
