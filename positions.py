"""
positions.py - Modellazione dello Spazio degli Stati, Azioni e Vincoli per NAO.
Fundamentals of Artificial Intelligence - NAO Planning Competition (UniBo)
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
    "rotation_foot_Rleg"     # Movimento con la gamba/piede destro
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
# 3. CATALOGO COMPLETO DELLE AZIONI (METADATI, DURATE E POSTURE)
# ==============================================================================
# Ogni azione specifica:
# - 'duration': durata stimata di esecuzione (in secondi)
# - 'pre': postura richiesta prima dell'esecuzione (None = applicabile sempre)
# - 'post': postura risultante dopo l'esecuzione
# - 'type': tipologia ('start', 'goal', 'mandatory', 'intermediate', 'crg')
# - 'file': file sorgente o riferimento in RobotPositions/
# - 'description': breve descrizione del movimento
ACTIONS = {
    # --- STATO INIZIALE & GOAL ---
    "StandInit": {
        "duration": 4.0,
        "pre": None,
        "post": STANDING,
        "type": "start",
        "file": "RobotPositions/14-StandInit.py",
        "description": "Posizione eretta iniziale con braccia avanzate"
    },
    "Crouch": {
        "duration": 4.0,
        "pre": STANDING,
        "post": CROUCHING,
        "type": "goal",
        "file": "RobotPositions/6-Crouch.py",
        "description": "Posizione finale rannicchiata / in ginocchio"
    },

    # --- POSIZIONI OBBLIGATORIE (MANDATORY) ---
    "Sit": {
        "duration": 5.0,
        "pre": STANDING,
        "post": SITTING,
        "type": "mandatory",
        "file": "RobotPositions/16-Sit.py",
        "description": "Il robot passa dalla posizione in piedi a seduta"
    },
    "SitRelax": {
        "duration": 4.0,
        "pre": SITTING,
        "post": SITTING,
        "type": "mandatory",
        "file": "RobotPositions/17-SitRelax.py",
        "description": "Il robot si rilassa rimanendo seduto"
    },
    "Stand": {
        "duration": 4.5,
        "pre": SITTING,
        "post": STANDING,
        "type": "mandatory",
        "file": "RobotPositions/11-Stand.py",
        "description": "Il robot si rialza in piedi dalla posizione seduta"
    },
    "StandZero": {
        "duration": 3.5,
        "pre": STANDING,
        "post": STANDING,
        "type": "mandatory",
        "file": "RobotPositions/15-StandZero.py",
        "description": "Posizione in piedi con braccia distese in avanti"
    },
    "Wipe Forehead": {
        "duration": 5.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "mandatory",
        "file": "box:Animations/Wipe Forehead",
        "description": "Gesto di asciugarsi la fronte (box Choregraphe)"
    },
    "Hello": {
        "duration": 4.5,
        "pre": STANDING,
        "post": STANDING,
        "type": "mandatory",
        "file": "box:Animations/Hello",
        "description": "Gesto di saluto con la mano (box Choregraphe)"
    },

    # --- POSIZIONI INTERMEDIE (INTERMEDIATE) ---
    "rotation_handgun": {
        "duration": 8.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/1-Rotation_handgun_object.py",
        "description": "Movimento del braccio che regge il ventaglio/oggetto"
    },
    "right_arm": {
        "duration": 10.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/2-Right_arm.py",
        "description": "Rotazione completa del braccio destro sopra la testa"
    },
    "double_movement": {
        "duration": 8.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/3-Double_movement.py",
        "description": "Movimento coordinato con entrambe le braccia"
    },
    "arms_opening": {
        "duration": 10.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/4-Arms_opening.py",
        "description": "Apertura e rotazione simultanea delle braccia"
    },
    "union_arms": {
        "duration": 9.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/5-Union_arms.py",
        "description": "Gesto di unione delle due braccia al centro"
    },
    "move_forward": {
        "duration": 4.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/7-Move_forward.py",
        "description": "3 passi in avanti"
    },
    "move_backward": {
        "duration": 4.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/8-Move_backward.py",
        "description": "3 passi all'indietro"
    },
    "diagonal_left": {
        "duration": 4.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/9-Diagonal_left.py",
        "description": "Passo diagonale a sinistra"
    },
    "diagonal_right": {
        "duration": 4.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/10-Diagonal_right.py",
        "description": "Passo diagonale a destra"
    },
    "rotation_foot_Lleg": {
        "duration": 11.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/13-Rotation_foot_LLeg.py",
        "description": "Rotazione e bilanciamento sulla gamba sinistra"
    },
    "rotation_foot_Rleg": {
        "duration": 11.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "intermediate",
        "file": "RobotPositions/12-Rotation_foot_RLeg.py",
        "description": "Rotazione e bilanciamento sulla gamba destra"
    },

    # --- ANIMAZIONI DA FILE .CRG ---
    "sing_with_me": {
        "duration": 14.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "RobotPositions/cgrFiles/sing_with_me.crg",
        "description": "NAO simula di suonare la chitarra"
    },
    "arm_dance": {
        "duration": 10.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "box:Dances/Arm Dance",
        "description": "Danza ritmica con movimento delle braccia"
    },
    "birthday_dance": {
        "duration": 15.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "RobotPositions/cgrFiles/birthday_dance_no_sound.crg",
        "description": "Coreografia di compleanno"
    },
    "sprinkler": {
        "duration": 8.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "RobotPositions/cgrFiles/sprinkler.crg",
        "description": "Mossa della danza sprinkler"
    },
    "workout": {
        "duration": 12.0,
        "pre": STANDING,
        "post": STANDING,
        "type": "crg",
        "file": "RobotPositions/cgrFiles/workout.crg",
        "description": "Sequenza di esercizi ginnici"
    }
}

# ==============================================================================
# 4. INCOMPATIBILITÀ ESPLICITE (Transizioni vietate nel simulatore)
# ==============================================================================
# Oltre al controllo della postura (es. niente passi da seduti),
# queste coppie consecutive (da -> a) provocano problemi di stabilità, cadute o
# contraddizioni fisiche/cinematiche nel simulatore Choregraphe.
INCOMPATIBILITIES = {
    # Non eseguire passi opposti consecutivi (annullamento estetico poco fluido)
    ("move_forward", "move_backward"),
    ("move_backward", "move_forward"),
    ("diagonal_left", "diagonal_right"),
    ("diagonal_right", "diagonal_left"),

    # Ripetere consecutivamente rotazioni della stessa gamba destabilizza il baricentro
    ("rotation_foot_RLeg", "rotation_foot_RLeg"),
    ("rotation_foot_LLeg", "rotation_foot_LLeg"),

    # Crouch è lo stato terminale: nessuna transizione consentita dopo Crouch
    ("Crouch", "StandInit"),
    ("Crouch", "Stand"),
    ("Crouch", "move_forward"),
    ("Crouch", "right_arm")
}


# ==============================================================================
# 5. FUNZIONI HELPER PER IL PLANNER
# ==============================================================================
def get_duration(action_name):
    """Restituisce la durata in secondi di un'azione."""
    if action_name in ACTIONS:
        return ACTIONS[action_name]["duration"]
    raise KeyError("Azione sconosciuta: %s" % action_name)

def get_posture(action_name):
    """Restituisce la postura risultante ('post') dopo l'azione."""
    if action_name in ACTIONS:
        return ACTIONS[action_name]["post"]
    raise KeyError("Azione sconosciuta: %s" % action_name)

def is_transition_valid(prev_action, next_action):
    """
    Verifica se la transizione da prev_action a next_action è valida:
    1. Verifica l'esistenza di entrambe le azioni.
    2. Controlla che la postura post di prev_action soddisfi la pre di next_action.
    3. Controlla che la coppia non sia presente in EXPLICIT_INCOMPATIBILITIES.
    """
    if prev_action not in ACTIONS or next_action not in ACTIONS:
        return False

    prev_data = ACTIONS[prev_action]
    next_data = ACTIONS[next_action]

    # Controllo incompatibilità esplicite
    if (prev_action, next_action) in INCOMPATIBILITIES:
        return False

    # Controllo precondizione di postura
    required_pre = next_data["pre"]
    if required_pre is not None and prev_data["post"] != required_pre:
        return False

    return True

def get_valid_next_actions(current_action, candidate_list=None):
    """
    Restituisce tutte le azioni applicabili a partire da current_action.
    Se candidate_list è fornita, filtra solo all'interno di quella lista.
    """
    pool = candidate_list if candidate_list is not None else ACTIONS.keys()
    valid_actions = []
    for candidate in pool:
        if is_transition_valid(current_action, candidate):
            valid_actions.append(candidate)
    return valid_actions