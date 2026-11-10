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
    a NAOqi / Choregraphe, la riproduzione della musica e la sincronizzazione al secondo.
- RobotPositions/:
    Raccolta degli script Python individuali di movimento e delle animazioni .crg.
- music.mp3:
    Traccia audio di 2 minuti sincronizzata con la coreografia.


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


5. DETTAGLI TECNICI SULL'APPROCCIO DI AI PLANNING:
--------------------------------------------------------------------------------
- Formulazione: Sub-goal State-Space Search con A*.
- Posizioni Obbligatorie (6): Sit, SitRelax, Stand, StandZero, Wipe Forehead, Hello.
- Stato Iniziale: StandInit (t = 0.0s) | Stato Obiettivo: Crouch (t = 119.5s).
- Euristica h(n): stima della discrepanza temporale rimanente rispetto al budget del segmento:
      h(n) = | T_budget - (t_accumulato + durata(P_target)) |
- Funzione di Costo g(n): penalizza la frammentazione del cammino e assegna un bonus
  di novità (-4.0) a ogni mossa intermedia non ancora utilizzata.
- Risultati ottenuti:
    * Durata totale: 119.5 secondi (target 120s pienamente soddisfatto).
    * Posizioni intermedie distinte utilizzate: 9 (regola >= 5 superata).
    * Zero cadute e rispetto completo delle incompatibilità cinematiche.

