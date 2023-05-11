# Restarting
### Valid options: "LUBY", "CADICAL"
PARAMS_RESTARTER = "CADICAL"
## LUBY
PARAMS_RESTART_LUBY_BASE = 1024
## CADICAL
PARAMS_RESTART_CADICAL_INTERVAL = 32
PARAMS_RESTART_CADICAL_RELUCTANT = 1024
PARAMS_RESTART_CADICAL_RELUCTANT_MAX = 1048576
PARAMS_RESTART_CADICAL_MARGIN = 0.25
PARAMS_RESTART_CADICAL_ALPHA_GLUCOSE_FAST = 1 / 32
PARAMS_RESTART_CADICAL_ALPHA_GLUCOSE_SLOW = 1 / 256
PARAMS_RESTART_CADICAL_STABLIZE = True
PARAMS_RESTART_CADICAL_STABLIZE_FACTOR = 2
PARAMS_RESTART_CADICAL_STABLIZE_STABLIZEINT = 1e3
PARAMS_RESTART_CADICAL_STABLIZE_STABLIZEMAXINT = 2e9

# Branching Heuristics
## UCB Switcher
PARAMS_UCB_BETA = 0.5
## VSIDS
PARAMS_VSIDS_DECAY = 0.95
HEURISTIC_ENABLE_VSIDS = False
## EVSIDS
PARAMS_EVSIDS_INCRE = 1.2
HEURISTIC_ENABLE_EVSIDS = False
## LRB
PARAMS_LRB_ALPHA = 0.4
PARAMS_LRB_ALPHA_LIM = 0.06
PARAMS_LRB_ALPHA_EPSILON = 1e-6
PARAMS_LRB_DECAY = 0.95
### Valid options: "CONFLICT_CLAUSE" ('incorrect' implementation), "CONFLICT_SIDE" (original implementation)
PARAMS_LRB_STRATEGY = "CONFLICT_SIDE"
HEURISTIC_ENABLE_LRB = True
## CHB
PARAMS_CHB_STEP = 0.4
PARAMS_CHB_STEP_MIN = 0.06
PARAMS_CHB_STEP_DECAY = 1e-6
PARAMS_REDUCE_LIM = 300
HEURISTIC_ENABLE_CHB = False

# Subsumption
ENABLE_SUBSUMPTION_ON_THE_FLY = True