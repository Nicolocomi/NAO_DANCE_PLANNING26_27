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
    6. Mega Drop Climax ('ONE MORE TIME!'): Apice dello show! Workout e sudore.
    7. Outro (Fade Out): Inchino finale e chiusura ad esattamente 120 secondi.
- Ricerca A* multi-obiettivo, che bilancia durata, energia, varietà e ripetizioni.
"""

import heapq
import itertools
import json
import os
from bisect import bisect_left
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
        "cue_action": "disco_groove",
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
        "cue_action": "arm_to_sky",
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
        "lyric": "Cassa a palla! Workout sfrenato e asciugamento fronte.",
        "cue_action": "arm_to_sky",
        "required_actions": ["seated_arm_to_sky"],
        "required_action_windows": {"seated_arm_to_sky": [6.8, 7.1]},
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
# 3. RICERCA A* PER UN SINGOLO SEGMENTO MUSICALE
# ==============================================================================
def a_star_music_segment(start_action, target_action, target_duration, target_energy,
                         global_used_intermediates, required_first_action=None,
                         required_actions=(), required_action_windows=None):
    """
    Cerca la sequenza a costo minimo con A*, usando la durata residua come
    euristica ottimistica e rispettando transizioni, ritmo e passi richiesti.
    """
    target_post_dur = positions.get_duration(target_action)

    if (required_first_action is None and not required_actions
            and target_duration <= target_post_dur
            and positions.is_transition_valid(start_action, target_action)):
        return [target_action], set()

    if (required_first_action is not None
            and not positions.is_transition_valid(start_action, required_first_action)):
        raise ValueError("Transizione non valida verso l'azione richiesta: %s" % required_first_action)

    required_actions = tuple(required_actions)
    required_action_windows = required_action_windows or {}
    required_action_bits = {
        action: 1 << index for index, action in enumerate(required_actions)
    }
    complete_required_mask = (1 << len(required_actions)) - 1
    for action in required_actions:
        if action not in positions.ACTIONS:
            raise ValueError("Azione obbligatoria sconosciuta: %s" % action)
    candidates = [
        action for action, data in positions.ACTIONS.items()
        if data.get("dance_phrase")
        and (not data.get("cue_only") or action in required_action_bits)
    ]
    if any(action not in candidates for action in required_actions):
        raise ValueError("Le azioni obbligatorie devono essere mosse candidate per A*.")

    initial_path = (required_first_action,) if required_first_action else ()
    initial_duration_ms = round(
        positions.get_duration(required_first_action) * 1000
    ) if required_first_action else 0
    initial_action = required_first_action or start_action
    action_bits = {action: 1 << index for index, action in enumerate(candidates)}
    used_mask = action_bits.get(required_first_action, 0)
    initial_required_mask = required_action_bits.get(required_first_action, 0)
    initial_cost = 0.0
    if required_first_action:
        initial_cost += abs(
            positions.get_energy(required_first_action) - target_energy
        ) * 0.35

    target_ms = round(target_duration * 1000)
    target_post_ms = round(target_post_dur * 1000)
    candidate_durations_ms = [
        round(positions.get_duration(action) * 1000) for action in candidates
    ]
    max_action_ms = max(candidate_durations_ms)
    upper_elapsed_ms = target_ms - target_post_ms + max_action_ms
    reachable = [False] * (upper_elapsed_ms + 1)
    reachable[0] = True
    for elapsed in range(upper_elapsed_ms + 1):
        if reachable[elapsed]:
            for action_duration in candidate_durations_ms:
                next_elapsed = elapsed + action_duration
                if next_elapsed <= upper_elapsed_ms:
                    reachable[next_elapsed] = True
    reachable_sums = [
        elapsed for elapsed, can_reach in enumerate(reachable) if can_reach
    ]

    def heuristic(elapsed_ms):
        remaining_ms = target_ms - target_post_ms - elapsed_ms
        index = bisect_left(reachable_sums, remaining_ms)
        nearest_error_ms = abs(reachable_sums[min(index, len(reachable_sums) - 1)] - remaining_ms)
        if index:
            nearest_error_ms = min(
                nearest_error_ms, abs(reachable_sums[index - 1] - remaining_ms)
            )
        return nearest_error_ms / 1000.0 * 8.0

    initial_state = (
        initial_action,
        None,
        initial_duration_ms,
        used_mask,
        initial_required_mask,
    )
    serial = itertools.count()
    open_set = [
        (initial_cost + heuristic(initial_duration_ms), initial_cost,
         next(serial), initial_state, initial_path)
    ]
    best_cost_by_state = {initial_state: initial_cost}
    best_solution = None
    best_score = float("inf")

    while open_set:
        estimated_total, path_cost, _, state, path = heapq.heappop(open_set)
        if estimated_total >= best_score:
            break
        if path_cost != best_cost_by_state.get(state):
            continue

        (last_action, previous_action, elapsed_ms, mask, required_mask) = state
        if (required_mask == complete_required_mask
                and positions.is_transition_valid(last_action, target_action)):
            timing_error = abs(target_ms - elapsed_ms - target_post_ms) / 1000.0
            score = path_cost + timing_error * 8.0
            if score < best_score:
                best_score = score
                best_solution = path + (target_action,)

        if elapsed_ms + target_post_ms >= target_ms + max_action_ms:
            continue

        for next_action in candidates:
            if not positions.is_transition_valid(last_action, next_action):
                continue
            if next_action in (last_action, previous_action):
                continue

            next_elapsed_ms = elapsed_ms + round(
                positions.get_duration(next_action) * 1000
            )
            if next_elapsed_ms + target_post_ms > target_ms + max_action_ms:
                continue

            required_bit = required_action_bits.get(next_action, 0)
            if required_bit and required_mask & required_bit:
                continue
            if required_bit and not required_mask & required_bit:
                window = required_action_windows.get(next_action)
                if window:
                    start_seconds = elapsed_ms / 1000.0
                    if not window[0] <= start_seconds <= window[1]:
                        continue

            next_mask = mask | action_bits[next_action]
            repeated = bool(mask & action_bits[next_action])
            edge_cost = abs(
                positions.get_energy(next_action) - target_energy
            ) * 0.35
            if repeated:
                edge_cost += 1.5
            if next_action in global_used_intermediates:
                edge_cost += 0.2
            next_cost = path_cost + edge_cost

            next_required_mask = required_mask | required_bit
            next_state = (
                next_action, last_action, next_elapsed_ms, next_mask, next_required_mask
            )
            if next_cost >= best_cost_by_state.get(next_state, float("inf")):
                continue
            best_cost_by_state[next_state] = next_cost
            next_path = path + (next_action,)
            priority = next_cost + heuristic(next_elapsed_ms)
            heapq.heappush(
                open_set,
                (priority, next_cost, next(serial), next_state, next_path)
            )

    if best_solution is None:
        raise ValueError("Nessuna sequenza valida per il segmento verso %s." % target_action)

    newly_used = {
        act for act in best_solution[:-1]
        if positions.ACTIONS[act]["type"] in ("intermediate", "crg")
    }
    return list(best_solution), newly_used


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
            global_used_intermediates=global_used_intermediates,
            required_first_action=sec.get("cue_action"),
            required_actions=sec.get("required_actions", ()),
            required_action_windows=sec.get("required_action_windows")
        )

        global_used_intermediates.update(newly_used)
        full_action_sequence.extend(sub_sequence)

        for act in sub_sequence:
            total_running_time += positions.get_duration(act)
            step_metadata.append({
                "section_name": sec["name"],
                "lyric": sec["lyric"]
            })

    if not full_action_sequence or full_action_sequence[-1] != positions.GOAL_POSITION:
        raise ValueError("La coreografia deve terminare con la posizione Crouch.")

    goal_start_time = target_total_time - positions.get_duration(positions.GOAL_POSITION)
    if goal_start_time < 0:
        raise ValueError("Durata target insufficiente per raggiungere la posizione Crouch.")

    protected_actions = {
        section["cue_action"]
        for section in song_sections
        if section.get("cue_action")
    }
    time_before_goal = sum(
        positions.get_duration(action) for action in full_action_sequence[:-1]
    )
    while time_before_goal > goal_start_time:
        removable_index = None
        for idx in range(len(full_action_sequence) - 2, 0, -1):
            action = full_action_sequence[idx]
            if action in protected_actions or positions.ACTIONS[action]["type"] not in ("intermediate", "crg"):
                continue
            if positions.is_transition_valid(full_action_sequence[idx - 1], full_action_sequence[idx + 1]):
                removable_index = idx
                break

        if removable_index is None:
            raise ValueError("Impossibile riservare tempo sufficiente per la posizione Crouch.")

        del full_action_sequence[removable_index]
        del step_metadata[removable_index]
        time_before_goal = sum(
            positions.get_duration(action) for action in full_action_sequence[:-1]
        )

    planned_durations = {
        idx: positions.get_duration(action)
        for idx, action in enumerate(full_action_sequence)
    }
    dance_actions = [
        idx for idx, action in enumerate(full_action_sequence[:-1])
        if positions.ACTIONS[action].get("dance_phrase")
    ]
    remaining_slack = goal_start_time - time_before_goal
    max_phrase_duration = 3 * DAFT_PUNK_SONG["seconds_per_bar"]
    while remaining_slack > 0.001 and dance_actions:
        adjustable = [
            idx for idx in dance_actions
            if planned_durations[idx] < max_phrase_duration - 0.001
        ]
        if not adjustable:
            break
        extra_each = remaining_slack / len(adjustable)
        applied = 0.0
        for idx in adjustable:
            old_duration = planned_durations[idx]
            extra = min(extra_each, max_phrase_duration - old_duration)
            planned_durations[idx] = old_duration + extra
            applied += extra
        remaining_slack -= applied

    if remaining_slack > 0.01:
        raise ValueError(
            "La coreografia lascia %.1f secondi vuoti prima del Crouch; "
            "servono altre frasi di danza." % remaining_slack
        )

    global_used_intermediates = {
        action for action in full_action_sequence
        if positions.ACTIONS[action]["type"] in ("intermediate", "crg")
    }

    # Creazione della timeline dettagliata con accenti musicali
    plan_steps = []
    current_t = 0.0
    for idx, act in enumerate(full_action_sequence):
        if idx == len(full_action_sequence) - 1:
            current_t = goal_start_time
        act_data = positions.ACTIONS[act]
        dur = planned_durations[idx]
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
            "file": act_data.get("file", "generated:dance_phrase"),
            "description": act_data["description"]
        }
        plan_steps.append(step_info)
        current_t += dur

    plan_end_time = round(current_t, 2)
    is_time_ok = abs(plan_end_time - target_total_time) <= 0.01
    is_variety_ok = len(global_used_intermediates) >= min_distinct_intermediates

    return {
        "song": DAFT_PUNK_SONG["title"],
        "artist": DAFT_PUNK_SONG["artist"],
        "bpm": DAFT_PUNK_SONG["bpm"],
        "steps": plan_steps,
        "total_time": plan_end_time,
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
        if act != "Crouch":
            steps_code.append("        if choreography_stop.is_set(): return")
            steps_code.append(
                '        if not wait_until(choreography_start + %.2f): return'
                % t_start
            )
        if act == "StandInit":
            steps_code.append(
                '        run_posture_action("StandInit", 0.65, choreography_start + %.2f)'
                % t_end
            )
        elif act == "Crouch":
            steps_code.append(
                '        if not wait_until(choreography_start + crouch_start_time): return'
            )
            steps_code.append('        crouch_ok = run_posture_action("Crouch", 0.6, choreography_start + choreography_target_time)')
            steps_code.append('        if not crouch_ok:')
            steps_code.append('            print("Errore: Crouch non completato entro il limite di 120 secondi.")')
            steps_code.append(
                '        if not wait_until(choreography_start + choreography_target_time): return'
            )
            steps_code.append('        choreography_stop.set()')
        elif act in ("Sit", "SitRelax", "Stand", "StandZero"):
            steps_code.append(
                '        run_posture_action("%s", 0.65, choreography_start + %.2f)'
                % (act, t_end)
            )
        elif positions.ACTIONS[act].get("dance_phrase"):
            steps_code.append(
                '        play_dance_phrase("%s", %.3f, choreography_start + %.2f)'
                % (act, dur, t_end)
            )
        elif act == "Hello":
            steps_code.append(
                '        play_dance_phrase("hello_wave", %.3f, choreography_start + %.2f)'
                % (dur, t_end)
            )
        elif act == "Wipe Forehead":
            steps_code.append(
                '        play_dance_phrase("wipe_forehead", %.3f, choreography_start + %.2f)'
                % (dur, t_end)
            )
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
        elif act == "birthday_dance":
            steps_code.append('        for _ in range(3):')
            steps_code.append('            motionProxy.post.angleInterpolation("LArm", arm_angles(20, 45, -60, -80, 0, 0.8), 1.2, True)')
            steps_code.append('            motionProxy.angleInterpolation("RArm", arm_angles(20, -45, 60, 80, 0, 0.8), 1.2, True)\n            time.sleep(0.3)')
            steps_code.append('            motionProxy.post.angleInterpolation("LArm", arm_angles(40, 20, -80, -30, -30, 0.5), 1.0, True)')
            steps_code.append('            motionProxy.angleInterpolation("RArm", arm_angles(20, -10, 40, 60, 30, 0.5), 1.0, True)\n            time.sleep(0.3)')
        elif act == "rotation_foot_Lleg":
            steps_code.append('        try:\n            motionProxy.angleInterpolation("Torso", [0, 0, 0, 0, 0, 0.05], 3.0, False)\n            time.sleep(2.0)\n        except Exception:\n            time.sleep(5.0)')
        elif act == "rotation_foot_Rleg":
            steps_code.append('        try:\n            motionProxy.angleInterpolation("Torso", [0, 0, 0, 0, 0, -0.05], 3.0, False)\n            time.sleep(2.0)\n        except Exception:\n            time.sleep(5.0)')
        elif act == "right_arm":
            steps_code.append('        r_up = arm_angles(-60.0, -40.0, 80.0, 20.0, 0.0, 0.9)')
            steps_code.append('        r_circle = arm_angles(-40.0, -60.0, 60.0, 50.0, 40.0, 0.9)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", r_up, 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", r_circle, 1.5, True)')
        elif act == "arm_to_sky":
            steps_code.append(
                '        play_dance_phrase("arm_to_sky", %.3f, choreography_start + %.2f)'
                % (dur, t_end)
            )
        elif act == "union_arms":
            steps_code.append('        motionProxy.post.angleInterpolation("LArm", arm_angles(10, 10, -80, -80, 0, 0.5), 1.5, True)')
            steps_code.append('        motionProxy.angleInterpolation("RArm", arm_angles(10, -10, 80, 80, 0, 0.5), 1.5, True)')
        else:
            steps_code.append('        time.sleep(%.1f)' % dur)

    raw_steps_python = "\n".join(steps_code)
    guarded_steps = []
    actuator_prefixes = (
        "motionProxy.", "postureProxy.", "play_dance_phrase(",
        "run_posture_action(", "time.sleep("
    )
    for line in raw_steps_python.splitlines():
        stripped_line = line.lstrip()
        if stripped_line.startswith(actuator_prefixes):
            indentation = line[:len(line) - len(stripped_line)]
            guarded_steps.append(indentation + "if choreography_stop.is_set(): return")
        guarded_steps.append(line)
        if stripped_line.startswith(actuator_prefixes):
            indentation = line[:len(line) - len(stripped_line)]
            guarded_steps.append(indentation + "if choreography_stop.is_set(): return")

    all_steps_python = "\n".join(guarded_steps)

    xar_template = '''<?xml version="1.0" encoding="UTF-8" ?>
<ChoregrapheProject xmlns="http://www.aldebaran-robotics.com/schema/choregraphe/project.xsd" xar_version="3">
    <Box name="root" id="-1" tooltip="Coreografia NAO sincronizzata con Daft Punk - One More Time" x="0" y="0">
        <bitmap>media/images/box/root.png</bitmap>
        <script language="4">
            <content>
                <![CDATA[
import math
import threading
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
        if hasattr(self, "_choreography_stop"):
            self._choreography_stop.set()
        if hasattr(self, "_deadline_cancel"):
            self._deadline_cancel.set()
        if hasattr(self, "_motion_proxy"):
            try:
                self._motion_proxy.killAll()
            except Exception as error:
                print("Impossibile interrompere i movimenti: %s" % error)
        self.onUnload()
        self.onStopped()

    def onInput_onStart(self):
        # NOTA: La musica va avviata ESTERNAMENTE (da main.py o manualmente).
        # NON usare subprocess/os dentro Choregraphe: crasha il simulatore.

        choreography_start = time.time()
        choreography_target_time = __TARGET_TIME__
        crouch_start_time = __CROUCH_START_TIME__
        choreography_stop = threading.Event()
        deadline_expired = threading.Event()
        deadline_cancel = threading.Event()
        motion_proxy_holder = []
        self._choreography_stop = choreography_stop
        self._deadline_cancel = deadline_cancel

        def enforce_deadline():
            while not deadline_cancel.is_set():
                remaining = choreography_start + choreography_target_time - time.time()
                if remaining <= 0:
                    break
                time.sleep(min(0.01, remaining))
            if deadline_cancel.is_set():
                return
            deadline_expired.set()
            choreography_stop.set()
            self.onStopped()
            if motion_proxy_holder:
                try:
                    motion_proxy_holder[0].killAll()
                except Exception as error:
                    print("Impossibile interrompere i movimenti: %s" % error)

        deadline_thread = threading.Thread(target=enforce_deadline)
        deadline_thread.daemon = True
        deadline_thread.start()

        proxy_result = {}
        proxy_error = []
        proxy_ready = threading.Event()

        def connect_proxies():
            try:
                try:
                    motion_proxy = ALProxy("ALMotion")
                    posture_proxy = ALProxy("ALRobotPosture")
                except Exception:
                    motion_proxy = ALProxy("ALMotion", "127.0.0.1", 9559)
                    posture_proxy = ALProxy("ALRobotPosture", "127.0.0.1", 9559)
                proxy_result["motion"] = motion_proxy
                proxy_result["posture"] = posture_proxy
            except Exception as error:
                proxy_error.append(error)
            finally:
                proxy_ready.set()

        proxy_thread = threading.Thread(target=connect_proxies)
        proxy_thread.daemon = True
        proxy_thread.start()
        while not proxy_ready.is_set() and not choreography_stop.is_set():
            remaining = choreography_start + choreography_target_time - time.time()
            if remaining <= 0:
                break
            time.sleep(min(0.01, remaining))
        if not proxy_ready.is_set() or choreography_stop.is_set():
            return
        if proxy_error:
            print("Impossibile connettersi ai proxy NAOqi: %s" % proxy_error[0])
            deadline_cancel.set()
            choreography_stop.set()
            self.onStopped()
            return
        motionProxy = proxy_result["motion"]
        postureProxy = proxy_result["posture"]
        self._motion_proxy = motionProxy
        motion_proxy_holder.append(motionProxy)
        if deadline_expired.is_set():
            try:
                motionProxy.killAll()
            except Exception as error:
                print("Impossibile interrompere i movimenti: %s" % error)
            return

        def arm_angles(pitch, roll, eyaw, eroll, wyaw=0.0, hand=0.0):
            return [
                math.radians(pitch),
                math.radians(roll),
                math.radians(eyaw),
                math.radians(eroll),
                math.radians(wyaw),
                hand
            ]

        DANCE_JOINTS = __DANCE_JOINTS__
        DANCE_PHRASES = __DANCE_PHRASES__

        def wait_until(target_time):
            while not choreography_stop.is_set():
                remaining = target_time - time.time()
                if remaining <= 0:
                    return True
                time.sleep(min(0.05, remaining))
            return False

        def wait_for_task(task_proxy, task_id, deadline, stop_task):
            while task_proxy.isRunning(task_id):
                if choreography_stop.is_set() or time.time() >= deadline:
                    stop_task()
                    return False
                time.sleep(0.03)
            return not choreography_stop.is_set() and time.time() <= deadline

        def run_posture_action(name, speed, deadline):
            if choreography_stop.is_set() or time.time() >= deadline:
                print("Deadline raggiunta prima della transizione a %s." % name)
                return False
            try:
                task_id = postureProxy.post.goToPosture(name, speed)
                completed = wait_for_task(
                    postureProxy, task_id, deadline, motionProxy.killAll
                )
                if not completed:
                    print("Transizione a %s interrotta alla deadline." % name)
                return completed
            except Exception as error:
                print("Errore nella transizione a %s: %s" % (name, error))
                return False

        def play_dance_phrase(name, duration, deadline):
            if choreography_stop.is_set() or time.time() >= deadline:
                print("Deadline raggiunta prima della frase %s." % name)
                return False
            try:
                poses = DANCE_PHRASES[name]
                frame_times = [
                    duration * frame / float(len(poses))
                    for frame in range(1, len(poses) + 1)
                ]
                angle_lists = []
                time_lists = []
                for joint_index, joint_name in enumerate(DANCE_JOINTS):
                    joint_angles = [pose[joint_index] for pose in poses]
                    if joint_name not in ("LHand", "RHand"):
                        joint_angles = [math.radians(angle) for angle in joint_angles]
                    angle_lists.append(joint_angles)
                    time_lists.append(frame_times)
                task_id = motionProxy.post.angleInterpolation(
                    DANCE_JOINTS, angle_lists, time_lists, True
                )
                completed = wait_for_task(
                    motionProxy, task_id, deadline,
                    lambda: motionProxy.stop(task_id)
                )
                if not completed:
                    print("Frase %s interrotta alla deadline." % name)
                return completed
            except Exception as error:
                print("Errore nella frase %s: %s" % (name, error))
                return False

''' + all_steps_python + '''

        deadline_cancel.set()
        if not deadline_expired.is_set():
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

    xar_template = xar_template.replace("__DANCE_JOINTS__", repr(positions.DANCE_JOINTS))
    xar_template = xar_template.replace("__DANCE_PHRASES__", repr(positions.DANCE_PHRASES))
    xar_template = xar_template.replace("__TARGET_TIME__", str(plan_result["total_time"]))
    xar_template = xar_template.replace("__CROUCH_START_TIME__", str(plan_result["steps"][-1]["start_time"]))

    with open(os.path.join(project_dir, "behavior_1", "behavior.xar"), "w") as f:
        f.write(xar_template)

    return os.path.join(project_dir, "NAO_Choreography.pml")


# ==============================================================================
# 6. STAMPA DELLA TIMELINE MUSICALE
# ==============================================================================
def print_plan_summary(plan_result):
    print("=" * 95)
    print("      NAO DANCE PLANNER - GROOVE A BEAT: DAFT PUNK - 'ONE MORE TIME' (123 BPM)")
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
