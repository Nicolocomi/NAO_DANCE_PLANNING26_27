# Prova tempi NAO

Banco di misura per il robot virtuale Choregraphe. Le prove sono individuali:
imposta `ACTION` in `RobotPositions/choregraphe_test_box.py`, incolla il box in
Choregraphe e avvialo una volta per ogni azione. Il tempo misurato viene
stampato nel Log Viewer. Rispetta la precondizione indicata in
`action_timings.csv` prima di avviare il test.

Il box usa velocita' 1.0 per `goToPosture` e `angleInterpolationWithSpeed`.
Le altre API non hanno un singolo parametro percentuale equivalente:

- `moveTo` usa i limiti di velocita' correnti di ALMotion.
- le animazioni CRG e `arm_dance` mantengono la loro velocita' interna.
- le rotazioni dei piedi usano `positionInterpolation` con traiettoria a 3 s;
  il tempo misurato include anche le transizioni a `StandInit`.

Queste modalita' sono riportate nel CSV: non confrontare direttamente i loro
tempi come se fossero tutte mosse a velocita' 100%. Esegui ogni prova tre volte
e annota la mediana. `current_duration_s` e' il valore attuale in `positions.py`;
inserisci la mediana in `measured_median_s` e poi aggiorna il catalogo.

Questa cartella e' per il simulatore. Prima di provare su un NAO fisico, verifica
che l'area sia libera e che la posa iniziale sia stabile.
