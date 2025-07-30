from random import choices, random, randint
from string import ascii_uppercase
from aesops import app
from data_models.model_store import db
from data_models.tournaments import Tournament
from data_models.players import Player
from data_models.match import Match
import aesops.business_logic.match as m_logic
import aesops.business_logic.tournament as t_logic
import aesops.business_logic.players as p_logic
from aesops.business_logic.matchmaking import pair_round
import tqdm
from timeit import default_timer as timer


def create_players(t: Tournament, count: int, num_byes: int = 0):
    for i in range(num_byes):
        t_logic.add_player(t, ascii_uppercase[i], first_round_bye=True)
    for _ in range(count - num_byes):
        t_logic.add_player(t, "".join(choices(ascii_uppercase, k=5)))


def create_results(m: Match):
    if m.is_bye:
        return
    if m.concluded:
        return
    r = random()
    if r < 0.49:
        m_logic.corp_win(m)
    elif r < 0.51:
        m_logic.tie(m)
    else:
        m_logic.runner_win(m)
    return


def sim_round(t: Tournament):
    # start_time = timer()
    for m in t.active_matches:
        create_results(m)
    db.session.commit()
    t = db.session.get(Tournament, t.id)
    t_logic.conclude_round(t)
    # print(
    #     f"Round {t.current_round} took {timer() - start_time:.2f} seconds to conclude"
    # )


def time_pair_round(t: Tournament):
    # start_time = timer()
    pair_round(t)
    db.session.commit()
    # print(
    #     f"Pairing round {t.current_round} took {timer() - start_time:.2f} seconds to complete"
    # )
    return t


def display_players(t: Tournament):
    for p in t_logic.rank_players(t):
        print(f"{p.name} {p.score} {p.sos} {p.esos}")


def drop_players(t: Tournament, drops_per_round: int, drop_rate: float = 0.9):
    if drops_per_round <= 0:
        return
    ranked_players = t_logic.calculate_player_ranks(t)
    active_ranked_players = [p for p in ranked_players if p["active"]]
    for i in range(drops_per_round):
        if random() < drop_rate:
            player = db.session.get(Player, active_ranked_players[-i - 1]["id"])
            player.active = False
            db.session.add(player)
    db.session.commit()


def sim_tournament(
    n_players: int,
    n_rounds: int,
    name: str = None,
    num_byes: int = 0,
    drops_per_round: int = 0,
    drop_rate: float = 0.9,
):
    if name is None:
        t = Tournament()
    else:
        t = Tournament(
            name=name,
            description=f"Simulated Tournament - {num_byes} byes - {drops_per_round} drops - {drop_rate} drop rate",
        )
        db.session.add(t)
        db.session.commit()
    create_players(t, count=n_players, num_byes=num_byes)
    for _ in range(n_rounds):
        pair_round(t)
        sim_round(t)
        drop_players(t, drops_per_round, drop_rate=drop_rate)
    return t


def clean_db():
    db.drop_all()
    db.create_all()
    from data_models.users import User

    admin = User()
    db.session.commit()


def test_tournaments(
    n_tournaments: int,
    n_players: int = 16,
    n_rounds: int = 4,
    name_prefix: str = "Sim_",
    num_byes: int = 0,
    drops_per_round: int = 0,
    drop_rate: float = 0.9,
):
    clean_db()
    # start = timer()
    for i in tqdm.trange(n_tournaments):
        sim_tournament(
            n_players=n_players,
            n_rounds=n_rounds,
            name=name_prefix + str(i),
            num_byes=num_byes,
            drops_per_round=drops_per_round,
            drop_rate=drop_rate,
        )
        db.session.expunge_all()
        db.session.commit()
        # print(f"Tournament {i} finished in {timer() - start:.2f} seconds")


def create_report(t: Tournament):
    import pandas as pd

    # tournament_df = pd.read_sql(
    #     f"SELECT * FROM tournament WHERE id = {t.id}",
    #     db.engine,
    # )
    players_df = pd.read_sql(
        f"SELECT * FROM player WHERE tid = {t.id}",
        db.engine,
    )
    players_df = players_df.sort_values(
        by=["score", "esos", "sos"], ascending=[False, False, False]
    )
    players_df["side_balance"] = players_df["id"].apply(
        lambda x: p_logic.get_side_balance(db.session.get(Player, x))
    )

    side_balance = players_df["side_balance"].sum()
    num_non_even_players = len(players_df[players_df["side_balance"] != 0])
    num_active_non_even_players = len(
        players_df[(players_df["side_balance"] != 0) & (players_df["active"])]
    )
    num_greater_than_one = len(players_df[abs(players_df["side_balance"]) > 1])
    # return players_df[
    #     [
    #         "name",
    #         "score",
    #         "esos",
    #         "sos",
    #         "side_balance",
    #     ]
    # ]
    return pd.DataFrame().from_dict(
        {
            "id": [t.id],
            "side_balance": [side_balance],
            "num_non_even_players": [num_non_even_players],
            "num_active_non_even_players": [num_active_non_even_players],
            "num_greater_than_one": [num_greater_than_one],
        },
        orient="columns",
    )


if __name__ == "__main__":
    # N_PLAYERS = 20
    # N_ROUNDS = 5
    # N_BYES = 0
    # DROPS_PER_ROUND = 0
    # import cProfile
    # from pstats import Stats, SortKey

    # with cProfile.Profile() as pr:
    #     with app.app_context():
    #         clean_db()
    #         test_tournaments(
    #             n_tournaments=50,
    #             n_players=N_PLAYERS,
    #             n_rounds=N_ROUNDS,
    #             name_prefix="Sim_",
    #             num_byes=N_BYES,
    #             drops_per_round=DROPS_PER_ROUND,
    #         )
    #         tournaments = [create_report(t) for t in Tournament.query.all()]
    #     import pandas as pd

    #     pd.concat(tournaments).to_csv(
    #         f"tournament_report_{N_PLAYERS}_{N_ROUNDS}_{DROPS_PER_ROUND}.csv",
    #         index=False,
    #     )
    #     (Stats(pr).sort_stats(SortKey.CALLS).print_stats(20))

    N_PLAYERS = 130
    N_ROUNDS = 12
    N_BYES = 8
    DROPS_PER_ROUND = 3
    with app.app_context():
        clean_db()
        test_tournaments(
            n_tournaments=50,
            n_players=N_PLAYERS,
            n_rounds=N_ROUNDS,
            name_prefix="Sim_",
            num_byes=N_BYES,
            drops_per_round=DROPS_PER_ROUND,
        )
        tournaments = [create_report(t) for t in Tournament.query.all()]
    import pandas as pd

    pd.concat(tournaments).to_csv(
        f"tournament_report_{N_PLAYERS}_{N_ROUNDS}_{DROPS_PER_ROUND}.csv", index=False
    )

    N_PLAYERS = 420
    N_ROUNDS = 14
    N_BYES = 6
    DROPS_PER_ROUND = 3
    with app.app_context():
        clean_db()
        test_tournaments(
            n_tournaments=25,
            n_players=N_PLAYERS,
            n_rounds=N_ROUNDS,
            name_prefix="Sim_",
            num_byes=N_BYES,
            drops_per_round=DROPS_PER_ROUND,
        )
        tournaments = [create_report(t) for t in Tournament.query.all()]
    import pandas as pd

    pd.concat(tournaments).to_csv(
        f"tournament_report_{N_PLAYERS}_{N_ROUNDS}_{DROPS_PER_ROUND}.csv", index=False
    )
