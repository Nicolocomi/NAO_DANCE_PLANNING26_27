"""
main.py - Esecutore della Coreografia per il Robot Umanoide NAO.
Fundamentals of Artificial Intelligence - NAO Planning Competition (UniBo)

Uso:
    python main.py [ROBOT_IP] [PORT] [--dry-run]

Esempi:
    python main.py 127.0.0.1 9559            # Esecuzione standard con Choregraphe
    python main.py 127.0.0.1 61476           # Esecuzione con porta custom
    python main.py --dry-run                 # Simulazione console senza robot (test rapido)
"""

import argparse
import atexit
import math
import os
import subprocess
import sys
import threading
import time

import planner

# La posa finale occupa la finestra riservata prima del limite assoluto.
TARGET_TIME_SECONDS = 120.0
MUSIC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music.mp3")

# Tentativo di importazione di NAOqi (presente nell'ambiente Choregraphe/Python 2.7)
try:
    from naoqi import ALProxy
    NAOQI_AVAILABLE = True
except ImportError:
    ALProxy = None
    NAOQI_AVAILABLE = False


def _sleep_until(deadline):
    remaining = deadline - time.monotonic()
    if remaining > 0:
        time.sleep(remaining)


def _stop_robot_motion(motion_proxy):
    if motion_proxy is None:
        return
    try:
        motion_proxy.stopMove()
    except Exception as error:
        print("  [ERRORE] Impossibile interrompere lo spostamento: %s" % error)
    try:
        motion_proxy.killAll()
    except Exception as error:
        print("  [ERRORE] Impossibile fermare i movimenti in corso: %s" % error)


def _wait_for_task(task_proxy, task_id, deadline, on_timeout):
    while task_proxy.isRunning(task_id):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            on_timeout()
            return False
        time.sleep(min(0.03, remaining))
    return time.monotonic() <= deadline


def _start_music(disabled=False):
    if disabled:
        return None
    if sys.platform != "darwin":
        raise RuntimeError("La riproduzione automatica è supportata su macOS tramite afplay.")
    if not os.path.isfile(MUSIC_FILE):
        raise IOError("File musicale non trovato: %s" % MUSIC_FILE)
    try:
        player = subprocess.Popen(["afplay", MUSIC_FILE])
    except OSError as error:
        raise RuntimeError("Impossibile avviare afplay: %s" % error)
    if player.poll() is not None:
        raise RuntimeError("afplay non è riuscito ad avviare la riproduzione.")
    atexit.register(_stop_music, player)
    print(" Musica:       riproduzione avviata da music.mp3")
    return player


def _stop_music(player, deadline=None):
    if player is None or player.poll() is not None:
        return
    try:
        player.terminate()
    except ProcessLookupError:
        return
    wait_timeout = 2.0
    if deadline is not None:
        wait_timeout = min(wait_timeout, max(0.0, deadline - time.monotonic()))
        if wait_timeout == 0.0:
            return
    try:
        player.wait(timeout=wait_timeout)
    except subprocess.TimeoutExpired:
        if deadline is not None and time.monotonic() >= deadline:
            return
        player.kill()
        if deadline is None:
            player.wait()


def _start_deadline_watchdog(deadline, motion_proxy, music_process):
    deadline_reached = threading.Event()
    cancel_watchdog = threading.Event()

    def enforce_deadline():
        remaining = max(0.0, deadline - time.monotonic())
        if cancel_watchdog.wait(remaining):
            return
        deadline_reached.set()
        if music_process is not None and music_process.poll() is None:
            try:
                music_process.terminate()
            except ProcessLookupError:
                pass
        _stop_robot_motion(motion_proxy)
        print("\n[LIMITE] Scadenza assoluta raggiunta: movimenti e musica interrotti.")

    watchdog = threading.Thread(target=enforce_deadline)
    watchdog.daemon = True
    watchdog.start()
    return deadline_reached, cancel_watchdog


def _play_dance_phrase(motion_proxy, phrase_name, duration, deadline):
    poses = planner.positions.DANCE_PHRASES[phrase_name]
    frame_times = [
        duration * frame / float(len(poses))
        for frame in range(1, len(poses) + 1)
    ]
    angle_lists = []
    time_lists = []
    for joint_index, joint_name in enumerate(planner.positions.DANCE_JOINTS):
        joint_angles = [pose[joint_index] for pose in poses]
        if joint_name not in ("LHand", "RHand"):
            joint_angles = [math.radians(angle) for angle in joint_angles]
        angle_lists.append(joint_angles)
        time_lists.append(frame_times)

    completed = True
    try:
        task_id = motion_proxy.post.angleInterpolation(
            planner.positions.DANCE_JOINTS, angle_lists, time_lists, True
        )
        completed = _wait_for_task(
            motion_proxy, task_id, deadline,
            lambda: motion_proxy.stop(task_id)
        )
    except Exception as error:
        print("  [ERRORE] Frase di danza '%s' fallita: %s" % (phrase_name, error))
        completed = False

    if completed:
        _sleep_until(deadline)
    return completed


def _wait_with_motion(deadline, motion_proxy, posture):
    remaining = deadline - time.monotonic()
    if remaining < 0.75 or motion_proxy is None:
        _sleep_until(deadline)
        return

    phrase_name = (
        "seated_arm_to_sky"
        if posture == planner.positions.SITTING
        else "disco_groove"
        if posture == planner.positions.STANDING
        else None
    )
    if phrase_name is None:
        _sleep_until(deadline)
        return
    if not _play_dance_phrase(motion_proxy, phrase_name, remaining, deadline):
        print(
            "  [AVVISO] Impossibile eseguire il movimento di raccordo; "
            "mantengo la posa fino alla prossima battuta."
        )
        _sleep_until(deadline)


def _execute_builtin_action(step_info, deadline, motion_proxy, posture_proxy):
    action_name = step_info["action"]
    duration = step_info["duration"]

    phrase_name = planner.positions.get_motion_phrase(action_name)

    if phrase_name is not None:
        if motion_proxy is None:
            print("  [ERRORE] Proxy ALMotion non disponibile per '%s'." % action_name)
            return False
        return _play_dance_phrase(motion_proxy, phrase_name, duration, deadline)

    if action_name in ("StandInit", "StandZero", "Sit", "SitRelax", "Stand"):
        if posture_proxy is None:
            print("  [ERRORE] Proxy ALRobotPosture non disponibile per '%s'." % action_name)
            return False
        try:
            task_id = posture_proxy.post.goToPosture(action_name, 1.0)
            if not _wait_for_task(
                    posture_proxy, task_id, deadline,
                    lambda: _stop_robot_motion(motion_proxy)):
                print("  [LIMITE] Transizione '%s' interrotta alla scadenza." % action_name)
                return False
        except Exception as error:
            print("  [ERRORE] Transizione a '%s' fallita: %s" % (action_name, error))
            return False
        _wait_with_motion(deadline, motion_proxy, step_info["posture"])
        return True

    if action_name in planner.positions.MOVE_TO_ACTIONS:
        if motion_proxy is None:
            print("  [ERRORE] Proxy ALMotion non disponibile per '%s'." % action_name)
            return False
        try:
            task_id = motion_proxy.post.moveTo(
                *planner.positions.MOVE_TO_ACTIONS[action_name]
            )
            if not _wait_for_task(
                    motion_proxy, task_id, deadline,
                    lambda: motion_proxy.stop(task_id)):
                print("  [LIMITE] Spostamento '%s' interrotto alla scadenza." % action_name)
                _stop_robot_motion(motion_proxy)
                return False
        except Exception as error:
            print("  [ERRORE] Spostamento '%s' fallito: %s" % (action_name, error))
            _stop_robot_motion(motion_proxy)
            return False
        _wait_with_motion(deadline, motion_proxy, step_info["posture"])
        return True

    return None


def execute_action(step_info, robot_ip, port, dry_run=False, deadline=None,
                   motion_proxy=None, posture_proxy=None):
    """
    Esegue una specifica azione del piano:
    - Se dry_run=True: simula a video il tempo di esecuzione.
    - Se file .py: avvia lo script corrispondente in RobotPositions/.
    - Se file .crg: tenta l'esecuzione via ALBehaviorManager o simula il tempo.

    deadline è un limite monotono assoluto per le azioni diverse da Crouch.
    """
    action_name = step_info["action"]
    file_path = step_info["file"]
    duration = step_info["duration"]
    action_end = time.monotonic() + duration
    if deadline is not None:
        action_end = min(action_end, deadline)

    print("\n" + "=" * 60)
    print("▶ PASSO %02d: %s (%s)" % (
        step_info["step"],
        action_name.upper(),
        step_info["type"].upper()
    ))
    print("  Orario: %5.1fs -> %5.1fs  |  Durata: %.1fs  |  Postura: %s" % (
        step_info["start_time"],
        step_info["end_time"],
        duration,
        step_info["posture"]
    ))
    print("  Descrizione: %s" % step_info["description"])
    print("-" * 60)

    if action_name != "Crouch" and time.monotonic() >= action_end:
        print("  [LIMITE] Nessun tempo residuo per questa mossa; si passa al Crouch.")
        return False

    if action_name == "Crouch":
        if time.monotonic() >= action_end:
            print("  [ERRORE] Nessun tempo residuo per avviare Crouch.")
            return False
        if dry_run or not NAOQI_AVAILABLE:
            _sleep_until(action_end)
            print("  [COMPLETATO] Simulazione della posizione Crouch.")
            return True
        if posture_proxy is None:
            print("  [ERRORE] Proxy ALRobotPosture non disponibile: impossibile garantire Crouch.")
            return False
        try:
            task_id = posture_proxy.post.goToPosture("Crouch", 1.0)
            if not _wait_for_task(
                    posture_proxy, task_id, action_end,
                    lambda: _stop_robot_motion(motion_proxy)):
                print("  [ERRORE] Crouch ha superato la scadenza; movimento interrotto.")
                return False
            actual_posture = posture_proxy.getPosture()
        except Exception as error:
            print("  [ERRORE] Impossibile completare/verificare Crouch: %s" % error)
            return False
        if actual_posture != "Crouch":
            print("  [ERRORE] Postura finale verificata come '%s', non Crouch." % actual_posture)
            return False
        _sleep_until(action_end)
        print("  [COMPLETATO] Postura finale verificata: Crouch.")
        return True

    if dry_run or not NAOQI_AVAILABLE:
        if not dry_run and not NAOQI_AVAILABLE:
            print("  [AVVISO] NAOqi non trovato nell'ambiente Python corrente. Esecuzione in DRY-RUN.")
        ticks = 10
        simulation_start = time.monotonic()
        for tick in range(ticks):
            tick_deadline = simulation_start + duration * (tick + 1) / float(ticks)
            if deadline is not None and tick_deadline > deadline:
                _sleep_until(deadline)
                print("\n  [LIMITE] Tempo riservato raggiunto; si passa alla posa Crouch.")
                return False
            progress = int((tick + 1) / float(ticks) * 20)
            bar = "#" * progress + "-" * (20 - progress)
            sys.stdout.write("\r  Progresso: [%s] %.1fs / %.1fs" % (bar, (tick + 1) * duration / float(ticks), duration))
            sys.stdout.flush()
            _sleep_until(tick_deadline)
        print("  [COMPLETATO]")
        return True

    builtin_result = _execute_builtin_action(
        step_info, action_end, motion_proxy, posture_proxy
    )
    if builtin_result is not None:
        return builtin_result

    # Esecuzione reale con NAOqi
    if file_path.endswith(".py") and os.path.isfile(file_path):
        print("  Esecuzione script: %s" % file_path)
        try:
            proc = subprocess.Popen([sys.executable, file_path, robot_ip, str(port)])
            while proc.poll() is None and time.monotonic() < action_end:
                time.sleep(min(0.05, max(0.0, action_end - time.monotonic())))
            if proc.poll() is None:
                proc.kill()
                proc.wait()
                print("  [LIMITE] Script interrotto per riservare tempo al Crouch.")
                return False
            if proc.returncode != 0:
                print("  [ERRORE] Lo script è terminato con codice %d." % proc.returncode)
                return False
        except OSError as error:
            print("  [ERRORE] Avvio dello script fallito: %s" % error)
            return False
        _sleep_until(action_end)

    elif file_path.endswith(".crg"):
        print("  Esecuzione animazione CRG: %s" % file_path)
        behavior_name = os.path.splitext(os.path.basename(file_path))[0]
        try:
            bm_proxy = ALProxy("ALBehaviorManager", robot_ip, port)
            if bm_proxy.isBehaviorInstalled(behavior_name):
                bm_proxy.post.runBehavior(behavior_name)
                while bm_proxy.isBehaviorRunning(behavior_name) and time.monotonic() < action_end:
                    time.sleep(min(0.05, max(0.0, action_end - time.monotonic())))
                if bm_proxy.isBehaviorRunning(behavior_name):
                    bm_proxy.stopBehavior(behavior_name)
                    print("  [LIMITE] Animazione interrotta per riservare tempo al Crouch.")
                    return False
            else:
                print("  [INFO] Comportamento '%s' non pre-installato nel robot, attesa timing..." % behavior_name)
                _sleep_until(action_end)
        except Exception as error:
            print("  [ERRORE] Esecuzione animazione '%s' fallita: %s" % (behavior_name, error))
            return False
        _sleep_until(action_end)
    else:
        _sleep_until(action_end)

    print("  [COMPLETATO CON SUCCESSO]")
    return True


def main():
    parser = argparse.ArgumentParser(description="Esecutore Coreografia NAO - Planning Competition UniBo")
    parser.add_argument("robot_ip", nargs="?", default="127.0.0.1", help="Indirizzo IP del robot (default: 127.0.0.1)")
    parser.add_argument("port", nargs="?", type=int, default=9559, help="Porta NAOqi (default: 9559 o 61476)")
    parser.add_argument("--dry-run", action="store_true", help="Esegui simulazione temporale senza connettersi al robot reale")
    parser.add_argument("--no-music", action="store_true", help="Non avviare music.mp3 automaticamente")

    args = parser.parse_args()

    print("=" * 80)
    print("      NAO PLANNING COMPETITION - ESECUZIONE DELLA COREOGRAFIA")
    print("=" * 80)
    print(" Target Robot: %s:%d" % (args.robot_ip, args.port))
    print(" Modalita':    %s" % ("DRY-RUN (Simulazione Console)" if args.dry_run else "NAOqi Choregraphe / Robot"))
    print(" Durata Target: %.1f secondi (2 minuti, limite fisso)" % TARGET_TIME_SECONDS)
    print("=" * 80)

    # 1. Generazione del piano tramite A*
    print("\n[1/3] Calcolo del piano ottimale con A* (planner.py)...")
    plan_result = planner.plan_choreography(target_total_time=TARGET_TIME_SECONDS)
    planner.print_plan_summary(plan_result)

    if (
        not plan_result["is_time_ok"]
        or not plan_result["is_variety_ok"]
        or not plan_result["is_space_ok"]
    ):
        print("[ERRORE] Il piano non soddisfa tutti i vincoli della competizione!")
        sys.exit(1)

    # 2. Controllo connessione robot se non in dry-run
    motion = None
    posture = None
    if not args.dry_run and NAOQI_AVAILABLE:
        print("\n[2/3] Test connessione ALMotion su %s:%d..." % (args.robot_ip, args.port))
        try:
            motion = ALProxy("ALMotion", args.robot_ip, args.port)
            posture = ALProxy("ALRobotPosture", args.robot_ip, args.port)
            print("  Connessione a NAO stabilita con successo!")
        except Exception as e:
            print("  [ATTENZIONE] Impossibile connettersi al robot: %s" % e)
            print("  Vuoi continuare in modalita' DRY-RUN? [S/n]: ")
            choice = sys.stdin.readline().strip().lower()
            if choice not in ("", "s", "si", "y", "yes"):
                print("Esecuzione interrotta.")
                sys.exit(1)
            args.dry_run = True
    else:
        print("\n[2/3] Modalita' simulazione attiva (Dry-Run).")

    # 3. Avvio esecuzione
    print("\n[3/3] Premi INVIO per avviare musica e coreografia insieme...")
    sys.stdin.readline()

    start_wall_time = time.monotonic()
    try:
        music_process = _start_music(disabled=args.no_music)
    except (IOError, RuntimeError) as error:
        print("[ERRORE] %s" % error)
        sys.exit(1)

    print("\n" + "#" * 80)
    print("        INIZIO COREOGRAFIA NAO - SINCRONIZZAZIONE AL SECONDO ZERO")
    print("#" * 80)

    steps = plan_result["steps"]
    crouch_step = steps[-1]
    crouch_start = start_wall_time + crouch_step["start_time"]
    hard_deadline = start_wall_time + TARGET_TIME_SECONDS
    stop_deadline = hard_deadline - planner.EXECUTION_STOP_MARGIN_SECONDS
    deadline_reached, cancel_watchdog = _start_deadline_watchdog(
        stop_deadline, motion, music_process
    )
    forced_crouch = False
    completed_steps = []

    for step in steps[:-1]:
        if deadline_reached.is_set():
            forced_crouch = True
            break
        target_step_start = start_wall_time + step["start_time"]
        current_elapsed = time.monotonic()

        # Attesa sincronizzata per iniziare esattamente al timestamp previsto
        if current_elapsed < target_step_start:
            time.sleep(target_step_start - current_elapsed)

        if time.monotonic() >= crouch_start:
            forced_crouch = True
            break
        step_deadline = min(start_wall_time + step["end_time"], crouch_start)
        if time.monotonic() >= step_deadline:
            forced_crouch = True
            break
        action_completed = execute_action(
                step, args.robot_ip, args.port, dry_run=args.dry_run,
                deadline=step_deadline, motion_proxy=motion, posture_proxy=posture)
        if not action_completed:
            forced_crouch = True
            break
        completed_steps.append(step)

    if forced_crouch:
        print("\n[LIMITE] Interrompo le altre mosse e riservo il finale al Crouch.")
        _stop_robot_motion(motion)

    if time.monotonic() < stop_deadline and not deadline_reached.is_set():
        _sleep_until(crouch_start)
        if time.monotonic() < stop_deadline and not deadline_reached.is_set():
            crouch_completed = execute_action(
                crouch_step, args.robot_ip, args.port, dry_run=args.dry_run,
                deadline=stop_deadline, motion_proxy=motion, posture_proxy=posture)
        else:
            crouch_completed = False
    else:
        crouch_completed = False
    if crouch_completed:
        completed_steps.append(crouch_step)
    cancel_watchdog.set()

    total_real_elapsed = time.monotonic() - start_wall_time
    print("\n" + "=" * 80)
    all_mandatory_visited = set(
        step["action"] for step in completed_steps if step["type"] == "mandatory"
    )
    mandatory_count = len(all_mandatory_visited.intersection(planner.positions.MANDATORY_POSITIONS))
    completed_intermediates = set(
        step["action"] for step in completed_steps
        if step["type"] in ("intermediate", "crg")
    )
    within_limit = total_real_elapsed <= TARGET_TIME_SECONDS
    if crouch_completed and within_limit and not forced_crouch:
        print("               COREOGRAFIA COMPLETATA IN CROUCH!")
    elif crouch_completed and within_limit:
        print("        MOSSE INTERROTTE; FINALE CROUCH RAGGIUNTO ENTRO 120s.")
    else:
        print("  [ERRORE] Finale Crouch non verificato entro il limite di 120 secondi.")
    print("=" * 80)
    print(" Tempo totale pianificato: %.1fs" % plan_result["total_time"])
    print(" Tempo reale trascorso:    %.1fs" % total_real_elapsed)
    print(" Posizioni obbligatorie:   %d/6" % mandatory_count)
    print(" Mosse intermedie eseguite: %d distinte" % len(completed_intermediates))
    print("=" * 80)
    _stop_music(music_process, hard_deadline)
    atexit.unregister(_stop_music, music_process)
    if not crouch_completed or not within_limit:
        sys.exit(1)


if __name__ == "__main__":
    main()
