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

import json
import os

import positions
from nao_problem import NaoProblem

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

# Reserve a little extra time beyond the estimated Crouch motion duration.
GOAL_RESERVE_SECONDS = max(6.0, positions.get_duration(positions.GOAL_POSITION))
EXECUTION_STOP_MARGIN_SECONDS = 1.0
MIN_DISTINCT_SPATIAL_ACTIONS = 3

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
        "required_actions": ["seated_arm_to_sky"],
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

# These actions have dedicated, timed handlers in the Choregraphe exporter.
EXECUTABLE_INTERMEDIATE_ACTIONS = set(positions.MOVE_TO_ACTIONS)


# ==============================================================================
# 3. RICERCA A* PER UN SINGOLO SEGMENTO MUSICALE
# ==============================================================================
def a_star_music_segment(start_action, target_action, target_duration, target_energy,
                         global_used_intermediates, required_first_action=None,
                         required_actions=()):
    """Solve one song segment with the AIMA search library."""
    problem = NaoProblem(
        start_action=start_action,
        target_action=target_action,
        target_duration=target_duration,
        target_energy=target_energy,
        global_used_intermediates=global_used_intermediates,
        executable_intermediate_actions=EXECUTABLE_INTERMEDIATE_ACTIONS,
        required_first_action=required_first_action,
        required_actions=required_actions,
    )
    return problem.solve()


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
    global_intermediate_counts = {}
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
            global_used_intermediates=global_intermediate_counts,
            required_first_action=sec.get("cue_action"),
            required_actions=sec.get("required_actions", ()),
        )

        for action, count in newly_used.items():
            global_intermediate_counts[action] = (
                global_intermediate_counts.get(action, 0) + count
            )
        full_action_sequence.extend(sub_sequence)

        for act in sub_sequence:
            total_running_time += positions.get_duration(act)
            step_metadata.append({
                "section_name": sec["name"],
                "lyric": sec["lyric"]
            })

    if not full_action_sequence or full_action_sequence[-1] != positions.GOAL_POSITION:
        raise ValueError("La coreografia deve terminare con la posizione Crouch.")

    goal_start_time = target_total_time - GOAL_RESERVE_SECONDS
    if goal_start_time < 0:
        raise ValueError("Durata target insufficiente per raggiungere la posizione Crouch.")

    protected_actions = set()
    for section in song_sections:
        if section.get("cue_action"):
            protected_actions.add(section["cue_action"])
        protected_actions.update(section.get("required_actions", ()))
    time_before_goal = sum(
        positions.get_duration(action) for action in full_action_sequence[:-1]
    )
    while time_before_goal > goal_start_time:
        removable_index = None
        for idx in range(len(full_action_sequence) - 2, 0, -1):
            action = full_action_sequence[idx]
            if action in protected_actions or positions.ACTIONS[action]["type"] not in ("intermediate", "crg"):
                continue
            remaining_spatial_actions = {
                candidate
                for index, candidate in enumerate(full_action_sequence)
                if index != idx and candidate in positions.MOVE_TO_ACTIONS
            }
            if (
                action in positions.MOVE_TO_ACTIONS
                and len(remaining_spatial_actions) < MIN_DISTINCT_SPATIAL_ACTIONS
            ):
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
    planned_durations[len(full_action_sequence) - 1] = GOAL_RESERVE_SECONDS
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
    intermediate_usage = {}
    for action in full_action_sequence:
        if positions.ACTIONS[action]["type"] in ("intermediate", "crg"):
            intermediate_usage[action] = intermediate_usage.get(action, 0) + 1

    is_time_ok = abs(plan_end_time - target_total_time) <= 2.0
    is_variety_ok = len(intermediate_usage) >= min_distinct_intermediates
    distinct_spatial_actions = sorted(
        action for action in intermediate_usage if action in positions.MOVE_TO_ACTIONS
    )
    is_space_ok = len(distinct_spatial_actions) >= MIN_DISTINCT_SPATIAL_ACTIONS

    return {
        "song": DAFT_PUNK_SONG["title"],
        "artist": DAFT_PUNK_SONG["artist"],
        "bpm": DAFT_PUNK_SONG["bpm"],
        "steps": plan_steps,
        "total_time": plan_end_time,
        "distinct_intermediates": sorted(intermediate_usage),
        "intermediate_usage": dict(sorted(intermediate_usage.items())),
        "distinct_spatial_actions": distinct_spatial_actions,
        "is_time_ok": is_time_ok,
        "is_variety_ok": is_variety_ok,
        "is_space_ok": is_space_ok
    }


# ==============================================================================
# 5. ESPORTATORE AUTOMATICO PER CHOREGRAPHE
# ==============================================================================
def export_choregraphe_project(plan_result, project_dir="NAO_Choreography_Project"):
    os.makedirs(os.path.join(project_dir, "behavior_1"), exist_ok=True)

    steps_code = []
    for step in plan_result["steps"]:
        act = step["action"]
        dur = step["duration"]
        t_start = step["start_time"]
        t_end = step["end_time"]
        step_num = step["step"]
        sec_name = step.get("section", "")
        lyric = step.get("lyric_cue", "")
        previous_step = (
            plan_result["steps"][step_num - 2] if step_num > 1 else None
        )
        previous_posture = (
            previous_step["posture"] if previous_step is not None else None
        )
        filler_phrase = (
            "seated_arm_to_sky"
            if previous_posture == positions.SITTING
            else "disco_groove"
            if previous_posture == positions.STANDING
            else None
        )

        steps_code.append("        # ======================================================================")
        steps_code.append("        # PASSO %02d [%s]: %s (%.1fs -> %.1fs)" % (step_num, sec_name, act, t_start, t_end))
        steps_code.append("        # Evento Musicale: %s" % lyric)
        steps_code.append("        # ======================================================================")
        if act != "Crouch":
            steps_code.append("        if choreography_stop.is_set(): return")
            if filler_phrase:
                steps_code.append(
                    '        if not wait_until(choreography_start + %.2f, "%s" if last_action_completed else None): return'
                    % (t_start, filler_phrase)
                )
            else:
                steps_code.append(
                    '        if not wait_until(choreography_start + %.2f): return'
                    % t_start
                )
        if act == positions.START_POSITION:
            steps_code.append(
                '        last_action_completed = run_posture_action("StandInit", 1.0, choreography_start + %.2f)'
                % t_end
            )
            steps_code.append('        if not last_action_completed: print("StandInit non completato.")')
        elif act == positions.GOAL_POSITION:
            if filler_phrase:
                steps_code.append(
                    '        if not wait_until(choreography_start + crouch_start_time, "%s" if last_action_completed else None): return'
                    % filler_phrase
                )
            else:
                steps_code.append(
                    '        if not wait_until(choreography_start + crouch_start_time): return'
                )
            steps_code.append('        crouch_ok = run_posture_action("Crouch", 1.0, choreography_start + choreography_stop_time)')
            steps_code.append('        if not crouch_ok:')
            steps_code.append('            print("Errore: Crouch non completato entro il limite operativo.")')
            steps_code.append(
                '        if not wait_until(choreography_start + choreography_target_time): return'
            )
            steps_code.append('        choreography_stop.set()')
        elif act in ("Sit", "SitRelax", "Stand", "StandZero"):
            steps_code.append(
                '        last_action_completed = run_posture_action("%s", 1.0, choreography_start + %.2f)'
                % (act, t_end)
            )
            steps_code.append('        if not last_action_completed: print("%s non completata.")' % act)
        elif positions.get_motion_phrase(act):
            phrase_name = positions.get_motion_phrase(act)
            steps_code.append(
                '        last_action_completed = play_dance_phrase("%s", %.3f, choreography_start + %.2f)'
                % (phrase_name, dur, t_end)
            )
            steps_code.append('        if not last_action_completed: print("Azione %s non completata.")' % act)
        elif act in positions.MOVE_TO_ACTIONS:
            displacement = positions.MOVE_TO_ACTIONS[act]
            steps_code.append(
                '        last_action_completed = run_move_action("%s", %r, choreography_start + %.2f)'
                % (act, displacement, t_end)
            )
            steps_code.append('        if not last_action_completed: print("Azione %s non completata.")' % act)
        else:
            raise ValueError(
                "L'azione pianificata '%s' non ha un handler eseguibile." % act
            )

    all_steps_python = "\n".join(steps_code)

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
                self._motion_proxy.stopMove()
            except Exception as error:
                print("Impossibile interrompere lo spostamento: %s" % error)
            try:
                self._motion_proxy.killAll()
            except Exception as error:
                print("Impossibile interrompere i movimenti: %s" % error)
        self.onUnload()
        if not getattr(self, "_stop_sent", False):
            self._stop_sent = True
            self.onStopped()

    def onInput_onStart(self):
        # NOTA: La musica va avviata ESTERNAMENTE (da main.py o manualmente).
        # NON usare subprocess/os dentro Choregraphe: crasha il simulatore.

        choreography_target_time = __TARGET_TIME__
        crouch_start_time = __CROUCH_START_TIME__
        stop_margin_seconds = __STOP_MARGIN__
        choreography_stop_time = choreography_target_time - stop_margin_seconds
        choreography_stop = threading.Event()
        deadline_expired = threading.Event()
        deadline_cancel = threading.Event()
        motion_proxy_holder = []
        self._stop_sent = False
        self._choreography_stop = choreography_stop
        self._deadline_cancel = deadline_cancel

        def stop_robot_motion():
            if not motion_proxy_holder:
                return
            motion_proxy = motion_proxy_holder[0]
            try:
                motion_proxy.stopMove()
            except Exception as error:
                print("Impossibile interrompere lo spostamento: %s" % error)
            try:
                motion_proxy.killAll()
            except Exception as error:
                print("Impossibile interrompere i movimenti: %s" % error)

        def notify_stopped():
            if not self._stop_sent:
                self._stop_sent = True
                self.onStopped()

        def enforce_deadline():
            while not deadline_cancel.is_set():
                remaining = choreography_start + choreography_stop_time - time.time()
                if remaining <= 0:
                    break
                time.sleep(min(0.01, remaining))
            if deadline_cancel.is_set():
                return
            deadline_expired.set()
            choreography_stop.set()
            print(
                "[LIMITE] Arresto anticipato di %.1f secondi: movimenti e coreografia interrotti."
                % stop_margin_seconds
            )
            stop_robot_motion()
            notify_stopped()

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
        proxy_ready.wait(15.0)
        if not proxy_ready.is_set():
            print("Connessione ai proxy NAOqi scaduta dopo 15 secondi.")
            deadline_cancel.set()
            choreography_stop.set()
            notify_stopped()
            return
        if proxy_error:
            print("Impossibile connettersi ai proxy NAOqi: %s" % proxy_error[0])
            deadline_cancel.set()
            choreography_stop.set()
            notify_stopped()
            return
        motionProxy = proxy_result["motion"]
        postureProxy = proxy_result["posture"]
        self._motion_proxy = motionProxy
        motion_proxy_holder.append(motionProxy)
        choreography_start = time.time()
        deadline_thread = threading.Thread(target=enforce_deadline)
        deadline_thread.daemon = True
        deadline_thread.start()

        DANCE_JOINTS = __DANCE_JOINTS__
        DANCE_PHRASES = __DANCE_PHRASES__

        def wait_until(target_time, filler_name=None):
            filler_index = 0
            while not choreography_stop.is_set():
                remaining = target_time - time.time()
                if remaining <= 0:
                    return True
                if filler_name and remaining > 0.08:
                    pose = DANCE_PHRASES[filler_name][
                        filler_index % len(DANCE_PHRASES[filler_name])
                    ]
                    frame_duration = min(0.5, remaining)
                    angle_lists = []
                    time_lists = []
                    for joint_index, joint_name in enumerate(DANCE_JOINTS):
                        angle = pose[joint_index]
                        if joint_name not in ("LHand", "RHand"):
                            angle = math.radians(angle)
                        angle_lists.append([angle])
                        time_lists.append([frame_duration])
                    try:
                        motionProxy.angleInterpolation(
                            DANCE_JOINTS, angle_lists, time_lists, True
                        )
                    except Exception as error:
                        print(
                            "Impossibile eseguire il movimento di raccordo: %s"
                            % error
                        )
                        filler_name = None
                    filler_index += 1
                else:
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
                    postureProxy, task_id, deadline, stop_robot_motion
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

        def run_move_action(name, displacement, deadline):
            if choreography_stop.is_set() or time.time() >= deadline:
                print("Deadline raggiunta prima dello spostamento %s." % name)
                return False
            try:
                task_id = motionProxy.post.moveTo(*displacement)
                completed = wait_for_task(
                    motionProxy, task_id, deadline,
                    lambda: motionProxy.stop(task_id)
                )
                if not completed:
                    print("Spostamento %s interrotto alla deadline." % name)
                return completed
            except Exception as error:
                print("Errore nello spostamento %s: %s" % (name, error))
                return False

        last_action_completed = True

''' + all_steps_python + '''

        deadline_cancel.set()
        if not deadline_expired.is_set():
            notify_stopped()
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
    xar_template = xar_template.replace(
        "__STOP_MARGIN__", str(EXECUTION_STOP_MARGIN_SECONDS)
    )

    with open(os.path.join(project_dir, "behavior_1", "behavior.xar"), "w") as f:
        f.write(xar_template)

    return os.path.join(project_dir, "NAO_Choreography.pml")


def export_choregraphe_test_box(output_path=None):
    """Refresh the standalone test box from the planner's action catalog."""
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "RobotPositions",
            "choregraphe_test_box.py",
        )

    with open(output_path, "r") as source_file:
        template = source_file.read()

    generated_values = {
        "DANCE_JOINTS": positions.DANCE_JOINTS,
        "DANCE_PHRASES": positions.DANCE_PHRASES,
        "MOTION_PHRASES": {
            action: phrase
            for action in positions.ACTIONS
            for phrase in [positions.get_motion_phrase(action)]
            if phrase is not None
        },
        "MOVE_TO_ACTIONS": positions.MOVE_TO_ACTIONS,
        "ACTION_DURATIONS": {
            action: data["duration"]
            for action, data in positions.ACTIONS.items()
        },
        "POSTURE_ACTIONS": tuple(
            action
            for action, data in positions.ACTIONS.items()
            if data["type"] in ("start", "goal", "mandatory")
            and positions.get_motion_phrase(action) is None
        ),
    }
    start_marker = "        # BEGIN GENERATED PLANNER DATA"
    end_marker = "        # END GENERATED PLANNER DATA"
    start = template.index(start_marker)
    end = template.index(end_marker, start) + len(end_marker)
    data_block = [start_marker]
    data_block.extend(
        "        %s = %r" % (name, value)
        for name, value in generated_values.items()
    )
    data_block.append(end_marker)
    template = template[:start] + "\n".join(data_block) + template[end:]

    with open(output_path, "w") as output_file:
        output_file.write(template)
    return output_path


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
    print(" - Frequenza intermedie: %s" % ", ".join(
        "%s x%d" % (action, count)
        for action, count in sorted(plan_result["intermediate_usage"].items())
    ))
    print(" - Spostamenti distinti: %d (minimo: %d) -> %s" % (
        len(plan_result["distinct_spatial_actions"]),
        MIN_DISTINCT_SPATIAL_ACTIONS,
        "SODDISFATTO [OK]" if plan_result["is_space_ok"] else "FALLITO"
    ))
    print(" - Crouch: finestra %.1fs; durata stimata del movimento %.1fs" % (
        plan_result["steps"][-1]["duration"],
        positions.get_duration(positions.GOAL_POSITION),
    ))
    print("=" * 95)


if __name__ == "__main__":
    result = plan_choreography(target_total_time=120.0)
    print_plan_summary(result)

    with open("choreography_plan.json", "w") as fp:
        json.dump(result, fp, indent=2)

    export_choregraphe_project(result)
    export_choregraphe_test_box()
    print("\nProgetto Choregraphe aggiornato con successo per 'One More Time'!")
