PROGETTO NAO - ONE MORE TIME
===========================

STRUTTURA
---------

File Python principali:
- main.py: avvia ed esegue il piano. Gestisce connessione NAOqi, tempi e
  conferma manuale per avviare la musica.
- planner.py: sceglie automaticamente le mosse con A* e genera il progetto
  Choregraphe. Non contiene una sequenza completa di mosse fissata a mano.
- positions.py: catalogo unico delle azioni, delle durate, delle posture e
  delle transizioni consentite.

Movimenti:
- RobotPositions/ contiene gli script delle singole azioni:
  1 Rotation_handgun_object; 2 Right_arm; 3 Double_movement;
  4 Arms_opening; 5 Union_arms; 6 Crouch; 7 Move_forward;
  8 Move_backward; 9 Diagonal_left; 10 Diagonal_right; 11 Stand;
  12 Rotation_foot_RLeg; 13 Rotation_foot_LLeg; 14 StandInit;
  15 StandZero; 16 Sit; 17 SitRelax; 18 Macho_man; 19 Hello;
  20 Wipe_forehead.
- RobotPositions/cgrFiles/ contiene le quattro animazioni Choregraphe
  usate come azioni: birthday_dance_no_sound, sing_with_me, sprinkler e workout.
- music.mp3: colonna sonora One More Time.

Progetto Choregraphe:
- NAO_Choreography_Project/NAO_Choreography.pml: progetto da aprire in
  Choregraphe.
- NAO_Choreography_Project/behavior_1/behavior.xar: comportamento eseguito
  da Choregraphe; viene generato da planner.py.
- NAO_Choreography_Project/manifest.xml: metadati del pacchetto.
- NAO_Choreography_Project/translations/translation_en_US.ts e
  translation_it_IT.ts: stringhe localizzate dell'interfaccia.

File generati/locali:
- choreography_plan.json: piano A* esportato da planner.py; è un risultato
  generato, non il codice sorgente.
- .gitignore: esclude cache Python, file macOS e il JSON generato.
- NAO_DANCE_PLANNING26_27.code-workspace: configurazione per aprire il
  repository in VS Code.
- .git/: cronologia Git e collegamento al repository GitHub (gestito da Git).

Non ci sono copie alternative da incollare o pacchetti completi duplicati:
per la versione Choregraphe si usa il progetto NAO_Choreography_Project.


COME USARLO
-----------

1. Calcolare il piano e aggiornare il progetto Choregraphe:
       python3 planner.py

2. Aprire il progetto nel simulatore:
       Choregraphe -> File -> Open project...
   Selezionare NAO_Choreography_Project/NAO_Choreography.pml e premere Play.

3. Eseguire il planner direttamente sul robot virtuale:
   - In Choregraphe, connettersi al robot virtuale.
   - Da un terminale nella cartella del repository eseguire:
       python3 main.py 127.0.0.1 9559
   - Quando richiesto, avviare One More Time e premere INVIO.
   - Sostituire IP e porta con i valori mostrati da Choregraphe.

4. Simulare solo tempi e piano nel terminale:
       python3 main.py --dry-run

Il pulsante Play di Choregraphe avvia il comportamento .xar; main.py è
un'esecuzione separata che invia le azioni al robot e richiede di avviare
la musica manualmente.


REQUISITI
---------
- Python 3 per planner.py e main.py.
- Python 2.7 con SDK NAOqi per gli script dei movimenti sul robot.
- Choregraphe con robot virtuale per la simulazione 3D.
