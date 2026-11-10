# 1. Posizioni obbligatorie che il robot deve toccare durante la performance
MANDATORY_POSITIONS = [
    "StandInit",
    "Sit",
    "SitRelax",
    "Wipe Forehead",
    "Hello",
    "StandZero",
    "Crouch"
]

# 2. Set di posizioni intermedie e movimenti di base (richiesto l'uso di almeno 5)
INTERMEDIATE_POSITIONS = [
    "rotation_handgun",      # Movimento del braccio con oggetto
    "right_arm",             # Rotazione del braccio destro
    "double_movement",       # Rotazione di entrambi gli arti superiori
    "arms_opening",          # Apertura e rotazione di entrambi gli arti superiori
    "union_arms",            # Movimento di unione delle braccia
    "move_forward",          # 3 passi in avanti
    "move_backward",         # 3 passi indietro
    "diagonal_left",         # 1 passo diagonale a sinistra
    "diagonal_right",        # 1 passo diagonale a destra
    "rotation_foot_Lleg",    # Movimento con la gamba sinistra
    "rotation_foot_Rleg"     # Movimento con la gamba destra
]

# 3. File .crg aggiuntivi e animazioni complesse (importabili in Choregraphe)
CRG_ANIMATIONS = [
    "sing_with_me",          # NAO suona la chitarra
    "arm_dance",             # Danza con movimento delle braccia
    "birthday_dance",        # Danza di compleanno
    "sprinkler",             # Danza sprinkler
    "workout"                # Esercizio fisico / allenamento
]

INCOMPATIBILITIES = {
    # Esempio: se una posizione crea conflitti di equilibrio noti nel simulatore
    "Crouch": ["move_forward"], # Esempio concettuale
}