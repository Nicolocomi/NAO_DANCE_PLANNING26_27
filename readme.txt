================================================================================
               NAO PLANNING COMPETITION - README PROGETTO
      Fundamentals of Artificial Intelligence - Università di Bologna (UniBo)
================================================================================

1. COMPONENTI DEL TEAM:
--------------------------------------------------------------------------------
- Nome Cognome 1: Sara Marcheselli
  Email:          sara.marcheselli2@studio.unibo.it

- Nome Cognome 2: Nicolò Comignani
  Email:          nicolo.comignani@studio.unibo.it

Repository GitHub:
https://github.com/Nicolocomi/NAO_DANCE_PLANNING26_27.git


2. STRUTTURA DEL PROGETTO:
--------------------------------------------------------------------------------
- positions.py:
    Modellazione dello spazio degli stati, posture (STANDING, SITTING, CROUCHING),
    metadati delle 25 azioni (durate, pre/post condizioni) e matrice di incompatibilità
    cinematica per prevenire cadute nel simulatore Choregraphe.
- planner.py:
    Algoritmo di Planning AI basato su scomposizione in sottoproblemi (Sub-goal Planning)
    e ricerca euristica A*. Include allocazione dinamica del budget temporale (target 120s)
    e funzione di costo g(n) con bonus di novità per garantire >= 5 intermedie distinte.
- main.py:
    Entry point principale per l'esecuzione della coreografia. Gestisce la connessione
    a NAOqi / Choregraphe e la sincronizzazione al secondo. La musica va fatta partire
    manualmente (es. dal telefono) quando richiesto dal programma.
- RobotPositions/:
    Raccolta degli script Python individuali di movimento e delle animazioni .crg.
- music.mp3:
    Traccia audio di 2 minuti: Daft Punk - 'One More Time' (123 BPM) sincronizzata al millisecondo.


3. REQUISITI SOFTWARE E LIBRERIE:
--------------------------------------------------------------------------------
- Python 2.7 (ambiente NAOqi SDK) oppure Python 3 (per il planner e dry-run)
- Choregraphe Suite (versione 2.1 o 2.8) con simulatore NAO virtuale
- SDK NAOqi (per la connessione ALProxy sul robot/simulatore)
- Librerie standard Python: sys, time, os, heapq, json, subprocess, math, threading


4. ISTRUZIONI PER IL TEST SUL ROBOT SIMULATO (CHOREGRAPHE):
--------------------------------------------------------------------------------
1) Avviare l'applicazione Choregraphe.
2) Connettersi al robot virtuale:
   - Menu 'Connection' -> 'Connect to virtual robot'.
   - Verificare l'indirizzo IP (default: 127.0.0.1) e la porta mostrata nella barra
     di stato (tipicamente 9559 oppure la porta visualizzata, es. 61476).
3) Aprire un terminale nella cartella del progetto.
4) Eseguire il comando di avvio passando IP e porta:
       python main.py 127.0.0.1 9559

   (Nota: se Choregraphe usa una porta diversa, sostituire 9559 con quella corretta).

5) Modalità di test senza robot (Dry-Run / Simulazione da console):
       python main.py --dry-run


5. DETTAGLI TECNICI SULL'APPROCCIO DI AI PLANNING MUSIC-DRIVEN:
--------------------------------------------------------------------------------
- Colonna Sonora Ufficiale: Daft Punk - 'One More Time' (123 BPM, 4/4).
- Formulazione AI: Sub-goal State-Space Search con A* guidato da vincoli musicali.
- Allineamento Metrico (123 BPM): ogni battuta dura ~1.95s; i cambi di sezione
  avvengono su frasi musicali di 8 battute (~15.6s) o 16 battute (~31.2s):
    1. Intro (Horns Hook): risveglio e saluto al pubblico (Hello).
    2. Verse 1 ('Celebrate'): danza funk e posa scenica (StandZero).
    3. Chorus 1 (First Party Drop): workout ed esplosione di festa (Sit).
    4. Breakdown 1: la batteria si ferma, momento chill a terra (SitRelax).
    5. Breakdown 2 (Riser): rullante in crescendo, alzata energica (Stand).
    6. Mega Drop Climax ('ONE MORE TIME!'): assolo chitarra rock, posa bicipiti
       Macho Man e asciugamento fronte (Wipe Forehead).
    7. Outro (Fade Out): passi d'onore e solenne inchino finale in ginocchio (Crouch).
- Funzione di Valutazione A* f(n) = g(n) + h(n):
    * Penalità energetica: aderenza del movimento al mood della sezione musicale.
    * Bonus di novità: incentiva l'uso di nuove mosse ed evita ripetizioni.
- Risultati ottenuti:
    * Durata totale: 119.5 secondi (target 120s perfettamente centrato).
    * Posizioni intermedie distinte utilizzate: 8 (regola >= 5 ampiamente superata).
    * Zero cadute e rispetto completo delle incompatibilità cinematiche.

