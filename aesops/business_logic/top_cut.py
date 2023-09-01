from data_models.model_store import CutPlayer

def get_side_balance(cut_player :CutPlayer):
    corp_games = len([match for match in cut_player.corp_cut_matches if match.concluded])
    runner_games = len(
        [match for match in cut_player.runner_cut_matches if match.concluded]
    )
    return corp_games - runner_games
