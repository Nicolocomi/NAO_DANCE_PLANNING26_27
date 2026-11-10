"""
planner.py - Modulo di Planning con A* per la NAO Planning Competition.
Fundamentals of Artificial Intelligence - Università di Bologna (UniBo)

Approccio:
- Sub-goal Planning: il problema globale (120 secondi, 6 posizioni obbligatorie,
  almeno 5 posizioni intermedie distinte) viene scomposto in sottoproblemi di
  transizione tra posizioni obbligatorie consecutive (P_i -> P_{i+1}).
- Ricerca Euristica A*: per ogni segmento, un algoritmo A* trova la sequenza di
  mosse intermedie valida (rispettando pre/post posture ed evitando incompatibilità)
  che avvicina la durata al budget temporale allocato.
- Budgeting Temporale Dinamico: ad ogni passo il tempo rimanente per raggiungere
  i 120s viene ridistribuito sui segmenti successivi, compensando eventuali
  discrepanze e garantendo la convergenza a ~120s.
- Varietà Artistica: il costo g(n) di A* premia con un bonus di novità l'uso di
  mosse intermedie non ancora utilizzate, garantendo il soddisfacimento del vincolo
  delle >= 5 intermedie distinte.
- Esportazione Automatica: genera in automatico il progetto nativo Choregraphe (.pml / behavior.xar)
  così qualsiasi modifica o ripianificazione si riflette istantaneamente nel simulatore 3D.
"""

import heapq
import json
import os
import positions

# ==============================================================================
# 1. SEQUENZA DI DEFAULT DEI WAYPOINT OBBLIGATORI (Slide 12, 13 e 15)
# ==============================================================================
# Inizio: StandInit
# Posizioni obbligatorie: Hello, StandZero, Sit, SitRelax, Stand, Wipe Forehead
# Fine (Goal): Crouch
DEFAULT_WAYPOINTS = [
    "StandInit",
    "Hello",
    "StandZero",
    "Sit",
    "SitRelax",
    "Stand",
    "Wipe Forehead",
    "Crouch"
]

# Pesi relativi per l'allocazione del tempo tra i segmenti:
# - I segmenti in cui NAO è seduto (Sit -> SitRelax, SitRelax -> Stand) hanno peso 0.0
#   (transizione diretta o breve, senza mosse di ballo in piedi).
# - I segmenti in piedi (StandInit -> Hello, Hello -> StandZero, Stand -> Wipe Forehead, ecc.)
#   assorbono il tempo per balli, passi e mosse virtuosistiche.
DEFAULT_SEGMENT_WEIGHTS = [1.0, 1.2, 1.0, 0.0, 0.0, 1.5, 1.0]


# ==============================================================================
# 2. STRUTTURA DEL NODO PER L'ALGORITMO A*
# ==============================================================================
class AStarNode(object):
    """
    Rappresenta un nodo nello spazio degli stati della ricerca A* per un segmento.
    """
    def __init__(self, action, current_duration, path, used_intermediates, f_cost=0.0):
        self.action = action                          # Ultima azione eseguita
        self.current_duration = current_duration      # Secondi trascorsi nel segmento
        self.path = path                              # Lista delle azioni scelte nel segmento
        self.used_intermediates = used_intermediates  # Set di mosse intermedie usate in questo ramo
        self.f_cost = f_cost                          # Valore di valutazione f(n) = g(n) + h(n)

    def __lt__(self, other):
        # Necessario per la priority queue (heapq)
        return self.f_cost < other.f_cost


# ==============================================================================
# 3. ALGORITMO A* PER UN SINGOLO SEGMENTO (P_start -> P_target)
# ==============================================================================
def a_star_segment(start_action, target_action, target_duration, global_used_intermediates):
    """
    Trova una sequenza valida di azioni intermedie da start_action a target_action
    tale che la durata totale del segmento si avvicini il più possibile a target_duration.

    Parametri:
    - start_action: l'azione da cui parte il segmento.
    - target_action: l'azione obbligatoria che conclude il segmento.
    - target_duration: budget di tempo ideale (in secondi) per questo segmento.
    - global_used_intermediates: set delle intermedie già usate nei segmenti precedenti.

    Ritorna:
    - best_path: sequenza di azioni [intermedia_1, intermedia_2, ..., target_action]
    - newly_used: set di nuove posizioni intermedie introdotte da questa sequenza
    """
    target_post_dur = positions.get_duration(target_action)

    # Se il budget richiesto è minimo o nullo e la transizione diretta è valida, procedi subito
    if target_duration <= target_post_dur and positions.is_transition_valid(start_action, target_action):
        return [target_action], set()

    open_set = []
    # Il nodo radice parte dalla posizione iniziale con durata 0 (la durata di start_action
    # è già stata conteggiata nel segmento precedente)
    initial_node = AStarNode(
        action=start_action,
        current_duration=0.0,
        path=[],
        used_intermediates=set(),
        f_cost=0.0
    )
    heapq.heappush(open_set, (0.0, initial_node))

    # Insieme dei candidati intermedi utilizzabili (intermedie base + animazioni .crg)
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

        # Verifica se dallo stato attuale possiamo raggiungere direttamente target_action
        if positions.is_transition_valid(current_node.action, target_action):
            total_seg_duration = current_node.current_duration + target_post_dur
            error = abs(total_seg_duration - target_duration)
            if error < best_error:
                best_error = error
                best_solution = current_node.path + [target_action]
                # Se l'errore rispetto al budget è entro 1 secondo, consideriamo la soluzione ottimale
                if error <= 1.0:
                    break

        # Pruning: se abbiamo già sforato il budget di oltre 4 secondi, non espandiamo oltre
        if current_node.current_duration > target_duration + 4.0:
            continue

        # Pruning di profondità: massimo 4 mosse intermedie per singolo segmento per evitare frammentazione
        if len(current_node.path) >= 4:
            continue

        # Generazione dei successori
        for next_action in candidate_intermediates:
            # Vincolo 1: verifica compatibilità cinematica/postura
            if not positions.is_transition_valid(current_node.action, next_action):
                continue

            # Vincolo 2: evita di ripetere identica la stessa mossa immediatamente
            if current_node.path and current_node.path[-1] == next_action:
                continue

            next_duration = current_node.current_duration + positions.get_duration(next_action)
            next_used = set(current_node.used_intermediates)
            next_used.add(next_action)

            # --- FUNZIONE DI COSTO g(n) ---
            # Penalità per numero di passi + bonus di novità se si usa una mossa mai usata prima
            is_new = (next_action not in global_used_intermediates) and (next_action not in current_node.used_intermediates)
            novelty_bonus = 4.0 if is_new else 0.0
            g_cost = len(current_node.path) * 1.5 - novelty_bonus

            # --- FUNZIONE EURISTICA h(n) ---
            # Stima della discrepanza residua rispetto al target_duration completando con target_action
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

    # Fallback nel caso in cui non si trovi un cammino intermedio: transizione diretta
    if best_solution is None:
        best_solution = [target_action]

    newly_used = {
        act for act in best_solution[:-1]
        if positions.ACTIONS[act]["type"] in ("intermediate", "crg")
    }
    return best_solution, newly_used


# ==============================================================================
# 4. PIANIFICATORE GLOBALE DELLA COREOGRAFIA
# ==============================================================================
def plan_choreography(target_total_time=120.0, waypoints=None, weights=None, min_distinct_intermediates=5):
    """
    Esegue il ciclo iterativo per pianificare l'intera coreografia di ~120s.

    Parametri:
    - target_total_time: durata obiettivo (default: 120.0 secondi = 2 minuti).
    - waypoints: lista ordinata delle posizioni obbligatorie (include StartInit e Crouch).
    - weights: pesi per la distribuzione del tempo nei segmenti.
    - min_distinct_intermediates: numero minimo di intermedie distinte richieste (regola: >= 5).

    Ritorna:
    - plan_steps: lista di dizionari con i dettagli di ogni passo temporale.
    - total_time: durata complessiva pianificata.
    - distinct_intermediates: set delle posizioni intermedie distinte utilizzate.
    """
    if waypoints is None:
        waypoints = DEFAULT_WAYPOINTS
    if weights is None:
        weights = DEFAULT_SEGMENT_WEIGHTS

    assert len(weights) == len(waypoints) - 1, "Il numero di pesi deve coincidere con il numero di transizioni!"

    full_action_sequence = [waypoints[0]]
    global_used_intermediates = set()
    total_running_time = positions.get_duration(waypoints[0])

    num_transitions = len(waypoints) - 1

    # Ciclo iterativo sulle coppie di posizioni obbligatorie successive
    for i in range(num_transitions):
        start_wp = full_action_sequence[-1]
        target_wp = waypoints[i + 1]

        # Calcolo del budget dinamico:
        # Calcoliamo il tempo ancora disponibile e lo ridistribuiamo in proporzione ai pesi rimanenti
        remaining_time = target_total_time - total_running_time
        remaining_weights_sum = sum(weights[j] for j in range(i, num_transitions))

        target_wp_dur = positions.get_duration(target_wp)

        if weights[i] > 0 and remaining_weights_sum > 0:
            # Tempo minimo necessario per le posizioni obbligatorie future
            future_mandatory_min = sum(positions.get_duration(waypoints[k]) for k in range(i + 1, len(waypoints)))
            available_for_intermediates = max(0.0, remaining_time - future_mandatory_min)
            allocated_budget = target_wp_dur + available_for_intermediates * (weights[i] / remaining_weights_sum)
        else:
            allocated_budget = target_wp_dur

        # Esegui la ricerca A* per il segmento corrente
        sub_sequence, newly_used = a_star_segment(
            start_action=start_wp,
            target_action=target_wp,
            target_duration=allocated_budget,
            global_used_intermediates=global_used_intermediates
        )

        global_used_intermediates.update(newly_used)
        full_action_sequence.extend(sub_sequence)

        for act in sub_sequence:
            total_running_time += positions.get_duration(act)

    # Costruzione del piano dettagliato con timestamp
    plan_steps = []
    current_t = 0.0
    for idx, act in enumerate(full_action_sequence):
        act_data = positions.ACTIONS[act]
        dur = act_data["duration"]
        step_info = {
            "step": idx + 1,
            "action": act,
            "type": act_data["type"],
            "posture": act_data["post"],
            "start_time": round(current_t, 2),
            "duration": dur,
            "end_time": round(current_t + dur, 2),
            "file": act_data["file"],
            "description": act_data["description"]
        }
        plan_steps.append(step_info)
        current_t += dur

    # Verifica dei vincoli di regolamento
    is_time_ok = abs(total_running_time - target_total_time) <= 3.0
    is_variety_ok = len(global_used_intermediates) >= min_distinct_intermediates

    return {
        "steps": plan_steps,
        "total_time": round(total_running_time, 2),
        "distinct_intermediates": sorted(list(global_used_intermediates)),
        "is_time_ok": is_time_ok,
        "is_variety_ok": is_variety_ok
    }


# ==============================================================================
# 5. ESPORTATORE AUTOMATICO PER CHOREGRAPHE (.PML / BEHAVIOR.XAR)
# ==============================================================================
def export_choregraphe_project(plan_result, project_dir="NAO_Choreography_Project"):
    """
    Traduce automaticamente il piano calcolato da A* in un progetto nativo Choregraphe
    (.pml con behavior.xar), così da poter visualizzare la coreografia nel simulatore 3D.
    """
    os.makedirs(os.path.join(project_dir, "behavior_1"), exist_ok=True)

    # Genera il codice Python di ciascun passo del piano
    steps_code = []
    for step in plan_result["steps"]:
        act = step["action"]
        desc = step["description"]
        dur = step["duration"]
        t_start = step["start_time"]
        t_end = step["end_time"]
        step_num = step["step"]

        steps_code.append("        # ----------------------------------------------------------------------")
        steps_code.append("        # PASSO %02d: %s (%.1fs -> %.1fs) [durata: %.1fs]" % (step_num, act, t_start, t_end, dur))
        steps_code.append("        # %s" % desc)
        steps_code.append("        # ----------------------------------------------------------------------")

        if act == "StandInit":
            steps_code.append('        try:\n            ttsProxy.post.say("Musica maestro!")\n        except Exception:\n            pass')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)\n        time.sleep(1.0)')
        elif act == "Crouch":
            steps_code.append('        try:\n            ttsProxy.post.say("Grazie a tutti!")\n        except Exception:\n            pass')
            steps_code.append('        postureProxy.goToPosture("Crouch", 0.6)\n        time.sleep(1.0)')
        elif act in ("Sit", "SitRelax", "Stand", "StandZero"):
            steps_code.append('        postureProxy.goToPosture("%s", 0.6)\n        time.sleep(1.0)' % act)
        elif act == "Hello":
            steps_code.append('        try:\n            ttsProxy.post.say("Ciao a tutti!")\n        except Exception:\n            pass')
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
        elif act == "double_movement":
            steps_code.append('        motionProxy.post.angleInterpolation("LArm", arm_angles(40, 20, -70, -60, 0, 0.8), 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", arm_angles(40, -20, 70, 60, 0, 0.8), 1.5, True)\n        time.sleep(0.5)')
            steps_code.append('        motionProxy.post.angleInterpolation("LArm", arm_angles(60, 10, -80, -30, 0, 0.8), 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", arm_angles(60, -10, 80, 30, 0, 0.8), 1.5, True)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "arms_opening":
            steps_code.append('        motionProxy.post.angleInterpolation("LArm", arm_angles(20, 60, -40, -30, 0, 0.8), 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", arm_angles(20, -60, 40, 30, 0, 0.8), 1.5, True)\n        time.sleep(1.0)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        elif act == "union_arms":
            steps_code.append('        motionProxy.post.angleInterpolation("LArm", arm_angles(10, 10, -80, -80, 0, 0.5), 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", arm_angles(10, -10, 80, 80, 0, 0.5), 1.5, True)\n        time.sleep(1.0)')
            steps_code.append('        postureProxy.goToPosture("StandInit", 0.6)')
        else:
            steps_code.append('        time.sleep(%.1f)' % dur)

    all_steps_python = "\n".join(steps_code)

    # Scrittura del file behavior.xar
    xar_template = '''<?xml version="1.0" encoding="UTF-8" ?>
<ChoregrapheProject xmlns="http://www.aldebaran-robotics.com/schema/choregraphe/project.xsd" xar_version="3">
    <Box name="root" id="-1" tooltip="Root box contenente l'intera coreografia pianificata con A*" x="0" y="0">
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

    def onInput_onStart(self):
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

    xar_path = os.path.join(project_dir, "behavior_1", "behavior.xar")
    with open(xar_path, "w") as f:
        f.write(xar_template)

    # Scrittura del file manifest.xml
    manifest_template = '''<?xml version='1.0' encoding='UTF-8'?>
<package version="0.0.1" uuid="nao-dance-planning-2026">
    <names>
        <name lang="en_US">NAO Choreography</name>
        <name lang="it_IT">Coreografia NAO</name>
    </names>
    <descriptions>
        <description lang="en_US">NAO Planning Competition Choreography</description>
    </descriptions>
    <supportedLanguages>
        <language>en_US</language>
        <language>it_IT</language>
    </supportedLanguages>
    <descriptionLanguages>
        <language>en_US</language>
    </descriptionLanguages>
    <contents>
        <behaviorContent path="behavior_1">
            <nature>interactive</nature>
            <permissions />
        </behaviorContent>
    </contents>
</package>
'''
    with open(os.path.join(project_dir, "manifest.xml"), "w") as f:
        f.write(manifest_template)

    # Scrittura del file NAO_Choreography.pml
    pml_template = '''<?xml version="1.0" encoding="UTF-8" ?>
<Package name="NAO_Choreography" format_version="4">
    <Manifest src="manifest.xml" />
    <BehaviorDescriptions>
        <BehaviorDescription name="behavior" src="behavior_1" xar="behavior.xar" />
    </BehaviorDescriptions>
    <DialogDescriptions />
    <AudioDescriptions />
    <EnvironmentDescriptions />
</Package>
'''
    with open(os.path.join(project_dir, "NAO_Choreography.pml"), "w") as f:
        f.write(pml_template)

    return os.path.join(project_dir, "NAO_Choreography.pml")


# ==============================================================================
# 6. STAMPA E REPORT DEL PIANO
# ==============================================================================
def print_plan_summary(plan_result):
    """Stampa a video una tabella chiara e formattata del piano generato."""
    print("=" * 80)
    print("           PIANO DELLA COREOGRAFIA NAO - PIANIFICATORE A*")
    print("=" * 80)
    print("%-5s | %-8s - %-8s | %-22s | %-12s | %-10s" % (
        "Passo", "Inizio", "Fine", "Azione", "Tipo", "Postura"
    ))
    print("-" * 80)

    for s in plan_result["steps"]:
        print("%-5d | %6.1fs - %6.1fs | %-22s | %-12s | %-10s" % (
            s["step"],
            s["start_time"],
            s["end_time"],
            s["action"],
            s["type"],
            s["posture"]
        ))

    print("=" * 80)
    print("RIEPILOGO VINCOLI DELLA COMPETIZIONE:")
    print(" - Durata totale: %.1f secondi (Target: 120.0s) -> %s" % (
        plan_result["total_time"],
        "SODDISFATTO [OK]" if plan_result["is_time_ok"] else "NON SODDISFATTO [FALLITO]"
    ))
    print(" - Mosse intermedie distinte usate: %d (Minimo: 5) -> %s" % (
        len(plan_result["distinct_intermediates"]),
        "SODDISFATTO [OK]" if plan_result["is_variety_ok"] else "NON SODDISFATTO [FALLITO]"
    ))
    print(" - Elenco intermedie: %s" % ", ".join(plan_result["distinct_intermediates"]))
    print("=" * 80)


if __name__ == "__main__":
    # 1. Pianificazione con A*
    result = plan_choreography(target_total_time=120.0)
    print_plan_summary(result)

    # 2. Salvataggio del piano su file JSON per l'esecutore
    with open("choreography_plan.json", "w") as fp:
        json.dump(result, fp, indent=2)
    print("\n[1/2] Piano esportato in 'choreography_plan.json'!")

    # 3. Esportazione automatica nel progetto Choregraphe .pml
    pml_file = export_choregraphe_project(result)
    print("[2/2] Progetto Choregraphe rigenerato con successo in '%s'!" % pml_file)
    print("      Ora puoi aprire il file da Choregraphe con 'File -> Open project...' e cliccare Play!")
