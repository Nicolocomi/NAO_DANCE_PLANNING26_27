"""
positions.py - Modellazione dello Spazio degli Stati, Azioni e Vincoli per NAO.
Fundamentals of Artificial Intelligence - NAO Planning Competition (UniBo)
Ottimizzato per la sincronizzazione musicale con Daft Punk - 'One More Time' (123 BPM)
"""

# ==============================================================================
# 1. MACRO-POSTURE (Stati cinematici del Robot)
# ==============================================================================
STANDING = "STANDING"    # In piedi (posizione eretta o bilanciata per movimenti/passi)
SITTING = "SITTING"      # Seduto (a terra o su supporto)
CROUCHING = "CROUCHING"  # In ginocchio / rannicchiato (stato finale)

# ==============================================================================
# 2. DEFINIZIONE DEGLI STATI CHIAVE (Slide 12, 13 e 15)
# ==============================================================================
START_POSITION = "StandInit"  # Stato Iniziale al tempo t = 0
GOAL_POSITION = "Crouch"      # Stato Finale al tempo t = 120s (2 min)

# Le 6 posizioni obbligatorie che devono essere toccate durante la coreografia
MANDATORY_POSITIONS = [
    "Sit",
    "SitRelax",
    "Wipe Forehead",
    "Stand",
    "Hello",
    "StandZero"
]

# Set di posizioni intermedie e movimenti di base (richiesto l'uso di almeno 5 distinte)
INTERMEDIATE_POSITIONS = [
    "rotation_handgun",      # Movimento del braccio con oggetto/ventaglio
    "right_arm",             # Rotazione del braccio destro sopra la testa
    "double_movement",       # Rotazione sincrona di entrambi gli arti superiori
    "arms_opening",          # Apertura e rotazione di entrambi gli arti superiori
    "union_arms",            # Movimento di unione delle braccia
    "move_forward",          # 3 passi in avanti
    "move_backward",         # 3 passi indietro
    "diagonal_left",         # 1 passo diagonale a sinistra
    "diagonal_right",        # 1 passo diagonale a destra
    "rotation_foot_Lleg",    # Movimento con la gamba/piede sinistro
    "rotation_foot_Rleg",    # Movimento con la gamba/piede destro
    "macho_man"              # Posa double-biceps con entrambe le braccia
]

# Animazioni avanzate da file .crg (importabili in Choregraphe)
CRG_ANIMATIONS = [
    "sing_with_me",          # NAO suona la chitarra
    "arm_dance",             # Danza con movimento delle braccia
    "birthday_dance",        # Danza di compleanno
    "sprinkler",             # Danza sprinkler
    "workout"                # Esercizio fisico / allenamento
]

# ==============================================================================
# 3. CATALOGO COMPLETO DELLE AZIONI (METADATI, DURATE, ENERGIA E POSTURE)
# ==============================================================================
# Ogni azione specifica:
# - 'duration': durata stimata di esecuzione (in secondi)
# - 'energy': livello energetico da 1 (calmo/a terra) a 5 (massimo dinamismo/climax)
# - 'pre': postura richiesta prima dell'esecuzione (None = applicabile sempre)
# - 'post': postura risultante dopo l'esecuzione
# - 'type': tipologia ('start', 'goal', 'mandatory', 'intermediate', 'crg')
# - 'file': file sorgente o riferimento in RobotPositions/
# - 'description': breve descrizione del movimento
ACTIONS = {
    # --- STATO INIZIALE & GOAL ---
    "StandInit": {
        "duration": 4.0,
        "energy": 2,
        "pre": None,
        "post": STANDING,
        "type": "start",
        "file": "RobotPositions/14-StandInit.py",
        "description": "Posizione eretta iniziale con braccia avanzate (risveglio)"
    },
    "Crouch": {
        "duration": 4.0,
        "energy": 1,
        "pre": STANDING,
        "post": CROUCHING,
        "type": "goal",
        "file": "RobotPositions/6-Crouch.py",
        "description": "Inchino finale rannicchiato / in ginocchio (chiusura)"
    },

    # --- POSIZIONI OBBLIGATORIE (MANDATORY) ---
    "Sit": {
        "duration": 5.0,
        "energy": 1,
        "pre": STANDING,
        "post": SITTING,
        "type": "mandatory",
        "file": "RobotPositions/16-Sit.py",
        "description": "Il robot passa dalla posizione in piedi a seduta"
    },
    "SitRelax": {
        "duration": 4.0,
        "energy": 1,
        "pre": SITTING,
        "post": SITTING,
        "type": "mandatory",
        "file": "RobotPositions/17-SitRelax.py",
        "description": "Il robot si rilassa rimanendo seduto (breakdown musicale)"
    },
    "Stand": {
        "duration": 4.5,
        "energy": 3,
        "pre": SITTING,
        "post": STANDING,
        "type": "mandatory",
        "file": "RobotPositions/11-Stand.py",
        "description": "Il robot si rialza in piedi con energia (snare riser)"
    },
    "StandZero": {
        "duration": 3.5,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "mandatory",
        "file": "RobotPositions/15-StandZero.py",
        "description": "Posa scenica in piedi con braccia distese in avanti"
    },
    "Wipe Forehead": {
        "duration": 5.0,
        "energy": 2,
        "pre": STANDING,
        "post": STANDING,
        "type": "mandatory",
        "file": "RobotPositions/20-Wipe_forehead.py",
        "description": "Gesto di asciugarsi la fronte per la fatica dopo il ballo"
    },
    "Hello": {
        "duration": 4.5,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "mandatory",
        "file": "RobotPositions/19-Hello.py",
        "description": "Gesto di saluto con la mano destra al pubblico"
    },

    # --- POSIZIONI INTERMEDIE (INTERMEDIATE) ---
    "rotation_handgun": {
        "duration": 8.0,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/1-Rotation_handgun_object.py",
        "description": "Movimento ritmico con il braccio e l'oggetto"
    },
    "right_arm": {
        "duration": 10.0,
        "energy": 4,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/2-Right_arm.py",
        "description": "Rotazione disco-funk del braccio destro sopra la testa"
    },
    "double_movement": {
        "duration": 8.0,
        "energy": 4,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/3-Double_movement.py",
        "description": "Movimento sincrono ed energico con entrambe le braccia"
    },
    "arms_opening": {
        "duration": 10.0,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/4-Arms_opening.py",
        "description": "Apertura solenne e rotazione simultanea delle braccia"
    },
    "union_arms": {
        "duration": 9.0,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/5-Union_arms.py",
        "description": "Gesto di unione delle braccia al centro del petto"
    },
    "move_forward": {
        "duration": 4.0,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/7-Move_forward.py",
        "description": "3 passi a tempo in avanti verso la platea"
    },
    "move_backward": {
        "duration": 4.0,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/8-Move_backward.py",
        "description": "3 passi ritmati all'indietro tornando al centro"
    },
    "diagonal_left": {
        "duration": 4.0,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/9-Diagonal_left.py",
        "description": "Passo diagonale scenografico a sinistra"
    },
    "diagonal_right": {
        "duration": 4.0,
        "energy": 3,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/10-Diagonal_right.py",
        "description": "Passo diagonale scenografico a destra"
    },
    "rotation_foot_Lleg": {
        "duration": 11.0,
        "energy": 4,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/13-Rotation_foot_LLeg.py",
        "description": "Footwork ritmico e bilanciamento sulla gamba sinistra"
    },
    "rotation_foot_Rleg": {
        "duration": 11.0,
        "energy": 4,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/12-Rotation_foot_RLeg.py",
        "description": "Footwork ritmico e bilanciamento sulla gamba destra"
    },
    "macho_man": {
        "duration": 4.0,
        "energy": 5,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/18-Macho_man.py",
        "description": "Posa double-biceps: flette i muscoli con fierezza al culmine del drop!"
    },

    # --- ANIMAZIONI DA FILE .CRG ---
    "sing_with_me": {
        "duration": 14.0,
        "energy": 5,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "RobotPositions/cgrFiles/sing_with_me.crg",
        "description": "Chitarra elettrica Daft Punk: plettrata ritmata sul campionamento rock"
    },
    "arm_dance": {
        "duration": 10.0,
        "energy": 4,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "box:Dances/Arm Dance",
        "description": "Danza ritmica con movimento delle braccia"
    },
    "birthday_dance": {
        "duration": 15.0,
        "energy": 4,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "RobotPositions/cgrFiles/birthday_dance_no_sound.crg",
        "description": "Danza festosa a tutto corpo: ideale per il ritornello"
    },
    "sprinkler": {
        "duration": 8.0,
        "energy": 4,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "RobotPositions/cgrFiles/sprinkler.crg",
        "description": "Mossa della danza sprinkler a tempo di beat"
    },
    "workout": {
        "duration": 12.0,
        "energy": 5,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "RobotPositions/cgrFiles/workout.crg",
        "description": "Aerobica ad altissima energia sul drop del ritornello"
    }
}

# ==============================================================================
# 4. INCOMPATIBILITÀ ESPLICITE
# ==============================================================================
EXPLICIT_INCOMPATIBILITIES = {
    # Non eseguire passi opposti consecutivi
    ("move_forward", "move_backward"),
    ("move_backward", "move_forward"),
    ("diagonal_left", "diagonal_right"),
    ("diagonal_right", "diagonal_left"),

    # Ripetere consecutivamente rotazioni della stessa gamba destabilizza il baricentro
    ("rotation_foot_RLeg", "rotation_foot_RLeg"),
    ("rotation_foot_LLeg", "rotation_foot_LLeg"),

    # Crouch è lo stato terminale
    ("Crouch", "StandInit"),
    ("Crouch", "Stand"),
    ("Crouch", "move_forward"),
    ("Crouch", "right_arm")
}

# ==============================================================================
# 5. FUNZIONI HELPER
# ==============================================================================
def get_duration(action_name):
    """Restituisce la durata in secondi di un'azione."""
    if action_name in ACTIONS:
        return ACTIONS[action_name]["duration"]
    raise KeyError("Azione sconosciuta: %s" % action_name)

def get_energy(action_name):
    """Restituisce il livello energetico (1-5) dell'azione."""
    if action_name in ACTIONS:
        return ACTIONS[action_name].get("energy", 3)
    return 3

def get_posture(action_name):
    """Restituisce la postura risultante ('post') dopo l'azione."""
    if action_name in ACTIONS:
        return ACTIONS[action_name]["post"]
    raise KeyError("Azione sconosciuta: %s" % action_name)

def is_transition_valid(prev_action, next_action):
    """Verifica se la transizione rispetta postura e stabilità."""
    if prev_action not in ACTIONS or next_action not in ACTIONS:
        return False

    prev_data = ACTIONS[prev_action]
    next_data = ACTIONS[next_action]

    if (prev_action, next_action) in EXPLICIT_INCOMPATIBILITIES:
        return False

    required_pre = next_data["pre"]
    if required_pre is not None and prev_data["post"] != required_pre:
        return False

    return True
