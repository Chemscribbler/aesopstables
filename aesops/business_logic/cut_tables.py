def get_bracket(num_players: int, double_elim: bool = False):
    """_summary_: Returns the bracket for the cut.
    _params_:
        num_players: The number of players in the cut.
        double_elim: Whether the cut is double elimination or not.
    _returns_: A dictionary containing the bracket for the cut.
    """
    if num_players not in [3, 4, 8, 16]:
        raise ValueError("Invalid number of players for cut")
    if double_elim:
        if num_players == 4:
            return double_elim_4
        elif num_players == 8:
            return double_elim_8
        elif num_players == 16:
            return double_elim_16
    else:
        if num_players == 8:
            return single_elim_8
        if num_players == 4:
            return single_elim_4
        elif num_players == 3:
            return single_elim_3


double_elim_16 = {
    "round_1": [
        {"table": 1, "higher_seed": 1, "lower_seed": 16, "elim": False},
        {"table": 2, "higher_seed": 8, "lower_seed": 9, "elim": False},
        {"table": 3, "higher_seed": 5, "lower_seed": 12, "elim": False},
        {"table": 4, "higher_seed": 4, "lower_seed": 13, "elim": False},
        {"table": 5, "higher_seed": 3, "lower_seed": 14, "elim": False},
        {"table": 6, "higher_seed": 6, "lower_seed": 11, "elim": False},
        {"table": 7, "higher_seed": 7, "lower_seed": 10, "elim": False},
        {"table": 8, "higher_seed": 2, "lower_seed": 15, "elim": False},
    ],
    "round_2": [
        {
            "table": 13,
            "higher_seed": (1, "winner"),
            "lower_seed": (2, "winner"),
            "elim": False,
        },
        {
            "table": 14,
            "higher_seed": (3, "winner"),
            "lower_seed": (4, "winner"),
            "elim": False,
        },
        {
            "table": 15,
            "higher_seed": (5, "winner"),
            "lower_seed": (6, "winner"),
            "elim": False,
        },
        {
            "table": 16,
            "higher_seed": (7, "winner"),
            "lower_seed": (8, "winner"),
            "elim": False,
        },
        {
            "table": 9,
            "higher_seed": (1, "loser"),
            "lower_seed": (2, "loser"),
            "elim": True,
        },
        {
            "table": 10,
            "higher_seed": (3, "loser"),
            "lower_seed": (4, "loser"),
            "elim": True,
        },
        {
            "table": 11,
            "higher_seed": (5, "loser"),
            "lower_seed": (6, "loser"),
            "elim": True,
        },
        {
            "table": 12,
            "higher_seed": (7, "loser"),
            "lower_seed": (8, "loser"),
            "elim": True,
        },
    ],
    "round_3": [
        {
            "table": 17,
            "higher_seed": (16, "loser"),
            "lower_seed": (9, "winner"),
            "elim": True,
        },
        {
            "table": 18,
            "higher_seed": (15, "loser"),
            "lower_seed": (10, "winner"),
            "elim": True,
        },
        {
            "table": 19,
            "higher_seed": (11, "winner"),
            "lower_seed": (14, "loser"),
            "elim": True,
        },
        {
            "table": 20,
            "higher_seed": (13, "loser"),
            "lower_seed": (12, "winner"),
            "elim": True,
        },
        {
            "table": 21,
            "higher_seed": (13, "winner"),
            "lower_seed": (14, "winner"),
            "elim": False,
        },
        {
            "table": 22,
            "higher_seed": (15, "winner"),
            "lower_seed": (16, "winner"),
            "elim": False,
        },
    ],
    "round_4": [
        {
            "table": 23,
            "higher_seed": (17, "winner"),
            "lower_seed": (18, "winner"),
            "elim": True,
        },
        {
            "table": 24,
            "higher_seed": (19, "winner"),
            "lower_seed": (20, "winner"),
            "elim": True,
        },
        {
            "table": 25,
            "higher_seed": (21, "winner"),
            "lower_seed": (22, "winner"),
            "elim": False,
        },
    ],
    "round_5": [
        {
            "table": 26,
            "higher_seed": (21, "loser"),
            "lower_seed": (23, "winner"),
            "elim": True,
        },
        {
            "table": 27,
            "higher_seed": (22, "loser"),
            "lower_seed": (24, "winner"),
            "elim": True,
        },
    ],
    "round_6": [
        {
            "table": 28,
            "higher_seed": (26, "winner"),
            "lower_seed": (27, "winner"),
            "elim": True,
        },
    ],
    "round_7": [
        {
            "table": 29,
            "higher_seed": (25, "loser"),
            "lower_seed": (28, "winner"),
            "elim": True,
        },
    ],
    "round_8": [
        {
            "table": 30,
            "higher_seed": (25, "winner"),
            "lower_seed": (29, "winner"),
            "elim": False,
            "final": True,
        },
    ],
    "round_9": [
        {
            "table": 31,
            "higher_seed": (30, "winner"),
            "lower_seed": (30, "loser"),
            "elim": True,
            "final": True,
        },
    ],
}

double_elim_8 = {
    "round_1": [
        {"table": 1, "higher_seed": 1, "lower_seed": 8, "elim": False},
        {"table": 2, "higher_seed": 4, "lower_seed": 5, "elim": False},
        {"table": 3, "higher_seed": 3, "lower_seed": 6, "elim": False},
        {"table": 4, "higher_seed": 2, "lower_seed": 7, "elim": False},
    ],
    "round_2": [
        {
            "table": 5,
            "higher_seed": (1, "loser"),
            "lower_seed": (2, "loser"),
            "elim": True,
        },
        {
            "table": 6,
            "higher_seed": (3, "loser"),
            "lower_seed": (4, "loser"),
            "elim": True,
        },
        {
            "table": 7,
            "higher_seed": (1, "winner"),
            "lower_seed": (2, "winner"),
            "elim": False,
        },
        {
            "table": 8,
            "higher_seed": (3, "winner"),
            "lower_seed": (4, "winner"),
            "elim": False,
        },
    ],
    "round_3": [
        {
            "table": 9,
            "higher_seed": (5, "winner"),
            "lower_seed": (8, "loser"),
            "elim": True,
        },
        {
            "table": 10,
            "higher_seed": (6, "winner"),
            "lower_seed": (7, "loser"),
            "elim": True,
        },
        {
            "table": 11,
            "higher_seed": (7, "winner"),
            "lower_seed": (8, "winner"),
            "elim": False,
        },
    ],
    "round_4": [
        {
            "table": 12,
            "higher_seed": (9, "winner"),
            "lower_seed": (10, "winner"),
            "elim": True,
        },
    ],
    "round_5": [
        {
            "table": 13,
            "higher_seed": (11, "loser"),
            "lower_seed": (12, "winner"),
            "elim": True,
        },
    ],
    "round_6": [
        {
            "table": 14,
            "higher_seed": (11, "winner"),
            "lower_seed": (13, "winner"),
            "final": True,
            "elim": False,
        },
    ],
    "round_7": [
        {
            "table": 15,
            "higher_seed": (14, "winner"),
            "lower_seed": (14, "loser"),
            "final": True,
            "elim": True,
        },
    ],
}

double_elim_4 = {
    "round_1": [
        {"table": 1, "higher_seed": 1, "lower_seed": 4, "elim": False},
        {"table": 2, "higher_seed": 2, "lower_seed": 3, "elim": False},
    ],
    "round_2": [
        {
            "table": 3,
            "higher_seed": (1, "loser"),
            "lower_seed": (2, "loser"),
            "elim": True,
        },
        {
            "table": 4,
            "higher_seed": (1, "winner"),
            "lower_seed": (2, "winner"),
            "elim": False,
        },
    ],
    "round_3": [
        {
            "table": 5,
            "higher_seed": (3, "winner"),
            "lower_seed": (4, "loser"),
            "elim": True,
        },
    ],
    "round_4": [
        {
            "table": 6,
            "higher_seed": (4, "winner"),
            "lower_seed": (5, "winner"),
            "elim": False,
            "final": True,
        },
    ],
    "round_5": [
        {
            "table": 7,
            "higher_seed": (6, "winner"),
            "lower_seed": (6, "loser"),
            "elim": True,
            "final": True,
        },
    ],
}

single_elim_4 = {
    "round_1": [
        {"table": 1, "higher_seed": 1, "lower_seed": 4, "elim": True},
        {"table": 2, "higher_seed": 2, "lower_seed": 3, "elim": True},
    ],
    "round_2": [
        {
            "table": 3,
            "higher_seed": (1, "winner"),
            "lower_seed": (2, "winner"),
            "elim": True,
            "final": True,
        },
    ],
}

single_elim_3 = {
    "round_1": [
        {"table": 1, "higher_seed": 2, "lower_seed": 3, "elim": True},
    ],
    "round_2": [
        {
            "table": 2,
            "higher_seed": 1,
            "lower_seed": (1, "winner"),
            "elim": True,
            "final": True,
        }
    ],
}

single_elim_8 = {
    "round_1": [
        {"table": 1, "higher_seed": 1, "lower_seed": 8, "elim": True},
        {"table": 2, "higher_seed": 4, "lower_seed": 5, "elim": True},
        {"table": 3, "higher_seed": 3, "lower_seed": 6, "elim": True},
        {"table": 4, "higher_seed": 2, "lower_seed": 7, "elim": True},
    ],
    "round_2": [
        {
            "table": 5,
            "higher_seed": (1, "winner"),
            "lower_seed": (2, "winner"),
            "elim": True,
        },
        {
            "table": 6,
            "higher_seed": (3, "winner"),
            "lower_seed": (4, "winner"),
            "elim": True,
        },
    ],
    "round_3": [
        {
            "table": 7,
            "higher_seed": (5, "winner"),
            "lower_seed": (6, "winner"),
            "elim": True,
            "final": True,
        }
    ],
}
