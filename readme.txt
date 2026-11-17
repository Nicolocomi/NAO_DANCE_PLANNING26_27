PROGETTO NAO - ONE MORE TIME
===========================

STRUTTURA
---------

File Python principali:
- main.py: avvia ed esegue il piano. Gestisce connessione NAOqi, tempi e
  conferma manuale per avviare la musica.
- planner.py: distribuisce le azioni nelle sezioni musicali e genera il
  progetto Choregraphe.
- nao_problem.py: definisce il problema di ricerca delle singole sezioni
  tramite AIMA e A*.
- aima/: libreria di ricerca AIMA inclusa nel progetto (licenza MIT).
- positions.py: catalogo unico delle azioni, delle durate, delle posture e
  delle transizioni consentite.

Movimenti:
- RobotPositions/ contiene gli script delle singole azioni:
  1 Rotation_handgun_object; 2 Right_arm; 3 Double_movement;
  4 Arms_opening; 5 Union_arms; 6 Crouch; 7 Move_forward;
  8 Move_backward; 9 Diagonal_left; 10 Diagonal_right; 11 Stand;
  12 Rotation_foot_RLeg; 13 Rotation_foot_LLeg; 14 StandInit;
  15 StandZero; 16 Sit; 17 SitRelax; 19 Hello;
  20 Wipe_forehead; 21 Arm_to_sky; 23 Seated_arm_to_sky;
  24 Disco_groove; 25 Side_step_groove; 26 Robot_pulse;
  27 Arm_wave_combo; 28 Party_punches; 29 Climax_reach.
- Gli script 23-29 sono eseguibili singolarmente e condividono
  RobotPositions/action_runner.py per le chiamate NAOqi e le pose definite
  in positions.py.
- RobotPositions/choregraphe_test_box.py contiene un box Python di prova:
  copiarne il contenuto in un box Python di Choregraphe e cambiare ACTION
  per provare una singola azione (tutte le 27 azioni .py e le 4 animazioni
  .crg); il tempo viene stampato nel Log Viewer. Le .crg devono essere
  installate nel robot virtuale. arm_dance è un box Choregraphe, non un file
  locale, e non è incluso nel box di prova.
- timing_trials/: istruzioni e tabella CSV per misurare tutte le azioni,
  annotare tre prove e aggiornare le durate in positions.py.
- Il planner inserisce Arm_to_sky all'inizio della prima strofa, sul primo
  "One more time", e poi prosegue con le altre mosse.
- L'A* può alternare le frasi di danza con gli spostamenti avanti, indietro e
  diagonali, usando le durate del catalogo. Penalizza le ripetizioni nella
  stessa sezione, riutilizza meno le mosse già eseguite e limita ogni
  intermedia a due esecuzioni nella coreografia.
- Le durate del catalogo sono stime: il piano viene allineato al target di
  120 secondi (tolleranza di pianificazione ±2s), ma il tempo fisico dipende
  dal robot e va verificato nel simulatore.
- RobotPositions/cgrFiles/ contiene le quattro animazioni Choregraphe
  usate come azioni: birthday_dance_no_sound, sing_with_me, sprinkler e workout.
- music.mp3: colonna sonora One More Time, tagliata a 120 secondi.

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
   - Quando richiesto, premere INVIO: `main.py` avvia `music.mp3` e la
     coreografia insieme in background tramite `afplay` su macOS.
   - Sostituire IP e porta con i valori mostrati da Choregraphe.
   - L'esecuzione ha un limite fisso di 120 secondi: gli ultimi 4 secondi
     (da 116s) sono riservati al Crouch. Se una mossa sfora il proprio intervallo,
     le mosse successive vengono saltate e il runner passa al Crouch.
   - Dopo `StandInit`, `disco_groove` parte senza una pausa iniziale aggiunta.
   - Il piano è generato dinamicamente con A* dai vincoli musicali, dalle
     pose obbligatorie e dalle transizioni ammesse; choreography_plan.json
     è solo un output rigenerabile.
   - Usa `--no-music` se vuoi avviare la musica manualmente.

4. Simulare solo tempi e piano nel terminale:
       python3 main.py --dry-run

Il pulsante Play verde di Choregraphe avvia il comportamento .xar senza musica.
Dopo aver rigenerato il progetto con `python3 planner.py`, ricaricare il
progetto in Choregraphe prima di usare Play, altrimenti si potrebbe eseguire
la copia del comportamento già caricata in memoria.
Per sincronizzare musica e robot usa `main.py`. Il comportamento .xar
generato fa partire il timer appena riceve Play (prima della connessione ai
proxy), assegna una deadline a ogni mossa, avvia il Crouch al secondo 116 e
invia onStopped e ALMotion.killAll al secondo 120.
Il pulsante Stop invia `ALMotion.killAll()` per interrompere subito i movimenti
attivi. La deadline impedisce al software di continuare oltre 120 secondi,
ma il raggiungimento fisico della posa dipende dalla risposta del robot e va
verificato in simulazione prima di usare il robot reale.


REQUISITI
---------
- Python 3 per planner.py e main.py.
- NumPy per la libreria AIMA inclusa. Installare con:
      python3 -m pip install -r requirements.txt
- Python 2.7 con SDK NAOqi per gli script dei movimenti sul robot.
- Choregraphe con robot virtuale per la simulazione 3D.
