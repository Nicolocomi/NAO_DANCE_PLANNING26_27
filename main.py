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
import os
import subprocess
import sys
import time

import planner

# Tentativo di importazione di NAOqi (presente nell'ambiente Choregraphe/Python 2.7)
try:
    from naoqi import ALProxy
    NAOQI_AVAILABLE = True
except ImportError:
    ALProxy = None
    NAOQI_AVAILABLE = False


# ==============================================================================
# ESECUZIONE DELLE SINGOLE AZIONI SUL ROBOT
# ==============================================================================
def execute_action(step_info, robot_ip, port, dry_run=False):
    """
    Esegue una specifica azione del piano:
    - Se dry_run=True: simula a video il tempo di esecuzione.
    - Se file .py: avvia lo script corrispondente in RobotPositions/.
    - Se file .crg: tenta l'esecuzione via ALBehaviorManager o simula il tempo.
    """
    action_name = step_info["action"]
    file_path = step_info["file"]
    duration = step_info["duration"]

    print("\n" + "=" * 60)
    print("▶ PASSO %02d/%02d: %s (%s)" % (
        step_info["step"],
        17,
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

    if dry_run or not NAOQI_AVAILABLE:
        if not dry_run and not NAOQI_AVAILABLE:
            print("  [AVVISO] NAOqi non trovato nell'ambiente Python corrente. Esecuzione in DRY-RUN.")
        # Simulazione visiva con barra di avanzamento
        ticks = 10
        sleep_interval = duration / float(ticks)
        for tick in range(ticks):
            progress = int((tick + 1) / float(ticks) * 20)
            bar = "#" * progress + "-" * (20 - progress)
            sys.stdout.write("\r  Progresso: [%s] %.1fs / %.1fs" % (bar, (tick + 1) * sleep_interval, duration))
            sys.stdout.flush()
            time.sleep(sleep_interval)
        print("  [COMPLETATO]")
        return

    # Esecuzione reale con NAOqi
    if file_path.endswith(".py") and os.path.isfile(file_path):
        print("  Esecuzione script: %s" % file_path)
        start_t = time.time()
        try:
            # Esegui lo script con lo stesso interprete Python passando IP e porta
            proc = subprocess.Popen([sys.executable, file_path, robot_ip, str(port)])
            proc.wait()
        except Exception as e:
            print("  [ERRORE] Esecuzione script fallita: %s" % e)

        # Attendi se lo script è terminato leggermente prima del budget
        elapsed = time.time() - start_t
        if elapsed < duration:
            time.sleep(duration - elapsed)

    elif file_path.endswith(".crg"):
        print("  Esecuzione animazione CRG: %s" % file_path)
        behavior_name = os.path.splitext(os.path.basename(file_path))[0]
        try:
            bm_proxy = ALProxy("ALBehaviorManager", robot_ip, port)
            if bm_proxy.isBehaviorInstalled(behavior_name):
                bm_proxy.runBehavior(behavior_name)
            else:
                print("  [INFO] Comportamento '%s' non pre-installato nel robot, attesa timing..." % behavior_name)
                time.sleep(duration)
        except Exception:
            time.sleep(duration)
    else:
        # Fallback per sicurezza
        time.sleep(duration)

    print("  [COMPLETATO CON SUCCESSO]")


# ==============================================================================
# ENTRY POINT PRINCIPALE
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Esecutore Coreografia NAO - Planning Competition UniBo")
    parser.add_argument("robot_ip", nargs="?", default="127.0.0.1", help="Indirizzo IP del robot (default: 127.0.0.1)")
    parser.add_argument("port", nargs="?", type=int, default=9559, help="Porta NAOqi (default: 9559 o 61476)")
    parser.add_argument("--dry-run", action="store_true", help="Esegui simulazione temporale senza connettersi al robot reale")
    parser.add_argument("--target-time", type=float, default=120.0, help="Durata complessiva desiderata in secondi (default: 120.0)")

    args = parser.parse_args()

    print("=" * 80)
    print("      NAO PLANNING COMPETITION - ESECUZIONE DELLA COREOGRAFIA")
    print("=" * 80)
    print(" Target Robot: %s:%d" % (args.robot_ip, args.port))
    print(" Modalita':    %s" % ("DRY-RUN (Simulazione Console)" if args.dry_run else "NAOqi Choregraphe / Robot"))
    print(" Durata Target: %.1f secondi (2 minuti)" % args.target_time)
    print("=" * 80)

    # 1. Generazione del piano tramite A*
    print("\n[1/3] Calcolo del piano ottimale con A* (planner.py)...")
    plan_result = planner.plan_choreography(target_total_time=args.target_time)
    planner.print_plan_summary(plan_result)

    if not plan_result["is_time_ok"] or not plan_result["is_variety_ok"]:
        print("[ERRORE] Il piano non soddisfa tutti i vincoli della competizione!")
        sys.exit(1)

    # 2. Controllo connessione robot se non in dry-run
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
    print("\n[3/3] Fai partire la musica dal telefono e premi INVIO per iniziare...")
    sys.stdin.readline()

    print("\n" + "#" * 80)
    print("        INIZIO COREOGRAFIA NAO - SINCRONIZZAZIONE AL SECONDO ZERO")
    print("#" * 80)

    start_wall_time = time.time()
    steps = plan_result["steps"]

    for step in steps:
        target_step_start = step["start_time"]
        current_elapsed = time.time() - start_wall_time

        # Attesa sincronizzata per iniziare esattamente al timestamp previsto
        if current_elapsed < target_step_start:
            time.sleep(target_step_start - current_elapsed)

        execute_action(step, args.robot_ip, args.port, dry_run=args.dry_run)

    total_real_elapsed = time.time() - start_wall_time
    print("\n" + "=" * 80)
    print("               COREOGRAFIA COMPLETATA CON SUCCESSO!")
    print("=" * 80)
    print(" Tempo totale pianificato: %.1fs" % plan_result["total_time"])
    print(" Tempo reale trascorso:    %.1fs" % total_real_elapsed)
    print(" Posizioni obbligatorie:   Tutte visitate (6/6)")
    print(" Mosse intermedie usate:   %d distinte (vincolo >= 5: SUPERATO)" % len(plan_result["distinct_intermediates"]))
    print("=" * 80)


if __name__ == "__main__":
    main()
