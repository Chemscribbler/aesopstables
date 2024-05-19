from data_models.match import MatchResult
from data_models.model_store import db
from data_models.players import Player

# Depreciating all of these because hitting the database for every player is not efficient
# Caching the results is a better solution for readability than my mess in the tournament logic
# But I'm not sure how to implement that yet


def get_record(player: Player, count_byes=True) -> dict[str, float]:
    score = 0
    games_played = 0
    for match in player.runner_matches:
        if not match.concluded:
            continue
        if match.result == MatchResult.RUNNER_WIN.value and match.concluded:
            score += 3
        if (
            match.result in [MatchResult.DRAW.value, MatchResult.INTENTIONAL_DRAW.value]
            and match.concluded
        ):
            score += 1
        games_played += 1
    for match in player.corp_matches:
        if not match.concluded:
            continue
        if match.result == MatchResult.CORP_WIN.value and match.concluded:
            score += 3
        if (
            match.result in [MatchResult.DRAW.value, MatchResult.INTENTIONAL_DRAW.value]
            and match.concluded
        ):
            score += 1
        if count_byes or not match.is_bye:
            games_played += 1
    return {"score": score, "games_played": games_played}


def get_side_balance(player: Player):
    played_corp_matchest = [
        m for m in player.corp_matches if m.is_bye == False and m.concluded
    ]
    return len(played_corp_matchest) - len(
        [m for m in player.runner_matches if m.concluded]
    )


# def get_average_score(player: Player) -> float:
#     return get_record(player)["score"] / max(get_record(player)["games_played"], 1)


# def get_sos(player: Player) -> float:
#     opp_average_score = sum(
#         [get_average_score(m.corp_player) for m in player.runner_matches]
#     )
#     opp_average_score += sum(
#         [
#             get_average_score(m.runner_player)
#             for m in player.corp_matches
#             if m.is_bye == False
#         ]
#     )
#     return round(
#         opp_average_score
#         / max(get_record(player, count_byes=False)["games_played"], 1),
#         3,
#     )


# def get_esos(player: Player) -> float:
#     opp_total_sos = sum([get_sos(m.corp_player) for m in player.runner_matches])
#     opp_total_sos += sum(
#         [get_sos(m.runner_player) for m in player.corp_matches if m.is_bye == False]
#     )
#     return round(
#         opp_total_sos / max(get_record(player, count_byes=False)["games_played"], 1), 3
#     )


# def update_score(player: Player):
#     player.score = get_record(player)["score"]
#     player.sos = get_sos(player)
#     player.esos = get_esos(player)
#     db.session.add(player)
#     db.session.commit()


# def update_sos_esos(player: Player):
#     player.sos = get_sos(player)
#     player.esos = get_esos(player)
#     db.session.add(player)
#     db.session.commit()


# def reset(player: Player):
#     update_score(player)
#     update_sos_esos(player)


def drop(player: Player):
    player.active = False
    db.session.add(player)
    db.session.commit()


def undrop(player: Player):
    player.active = True
    db.session.add(player)
    db.session.commit()


def is_paired(player: Player, rnd):
    for match in player.runner_matches:
        if match.rnd == rnd:
            return True
    for match in player.corp_matches:
        if match.rnd == rnd:
            return True
    return False


def side_record(player: Player, side):
    results = {"W": 0, "L": 0, "T": 0}
    side_function = {"runner": player.runner_matches, "corp": player.corp_matches}
    for match in side_function[side]:
        if match.is_bye:
            continue
        if match.concluded:
            if match.result == MatchResult.RUNNER_WIN.value:
                if side == "runner":
                    results["W"] += 1
                else:
                    results["L"] += 1
            elif match.result == MatchResult.CORP_WIN.value:
                if side == "corp":
                    results["W"] += 1
                else:
                    results["L"] += 1
            else:
                results["T"] += 1
    return results


def reveal_decklists(player, tournament):
    if tournament.reveal_decklists:
        return True
    if tournament.reveal_cut_decklists and player.cut_player:
        return True
    return False
