from celery import shared_task
from data_models.match import MatchResult
from data_models.model_store import db
from data_models.players import Player

def get_record(player :Player) -> dict[str, float]:
    score = 0
    games_played = 0
    for match in player.runner_matches:
        if not match.concluded:
            continue
        if match.result == MatchResult.RUNNER_WIN.value and match.concluded:
            score += 3
        if match.result in [MatchResult.DRAW.value, MatchResult.INTENTIONAL_DRAW.value] and match.concluded:
            score += 1
        games_played += 1
    for match in player.corp_matches:
        if not match.concluded:
            continue
        if match.result == MatchResult.CORP_WIN.value and match.concluded:
            score += 3
        if match.result in [MatchResult.DRAW.value, MatchResult.INTENTIONAL_DRAW.value] and match.concluded:
            score += 1
        games_played += 1
    return {"score": score, "games_played": games_played}

def get_side_balance(player :Player):
    played_corp_matchest = [
        m for m in player.corp_matches if m.is_bye == False and m.concluded
    ]
    return len(played_corp_matchest) - len(
        [m for m in player.runner_matches if m.concluded]
    )

def get_average_score(player :Player) -> float:
    return player.score / max(player.games_played, 1)

def get_sos(player :Player) -> float:
    opp_average_score = sum(
        [get_average_score(m.corp_player) for m in player.runner_matches]
    )
    opp_average_score += sum(
        [
            get_average_score(m.runner_player)
            for m in player.corp_matches
            if m.is_bye == False
        ]
    )
    return round(opp_average_score / max(player.games_played, 1), 3)

def get_esos(player :Player) -> float:
    opp_total_sos = sum([get_sos(m.corp_player) for m in player.runner_matches])
    opp_total_sos += sum(
        [get_sos(m.runner_player) for m in player.corp_matches if m.is_bye == False]
    )
    return round(opp_total_sos / max(player.games_played, 1), 3)

@shared_task
def update_score(player_id :int):
    player = Player.query.get(player_id)
    if player:
        player_record = get_record(player)
        if (player.score != player_record["score"]) or (player.games_played != player_record["games_played"]):
            player.score = player_record["score"]
            player.games_played = player_record["games_played"]
            db.session.add(player)
            db.session.commit()

@shared_task
def update_sos_esos(player_id :int):
    player = Player.query.get(player_id)
    if player:
        player.sos = get_sos(player)
        player.esos = get_esos(player)
        db.session.add(player)
        db.session.commit()
