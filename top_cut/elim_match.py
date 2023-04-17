from aesops import db
from sqlalchemy.orm import Mapped
from pairing.match import ConclusionError
from top_cut.cut_player import CutPlayer
from random import randint
from top_cut.cut_tables import get_bracket


class ElimMatch(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    cut_id = db.Column(
        db.Integer,
        db.ForeignKey("cut.id", ondelete="CASCADE", name="cut_id_fk"),
    )
    rnd = db.Column(db.Integer)
    higher_seed_id = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    lower_seed_id = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    corp_player_id = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    runner_player_id = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    result = db.Column(db.Integer)
    concluded = db.Column(db.Boolean, default=False)
    winner_match_id = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    loser_match_id = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    table_number = db.Column(db.Integer)
    cut = db.relationship("Cut", backref="matches")
    higher_seed = db.relationship(
        "CutPlayer", foreign_keys=[higher_seed_id], backref="higher_seed_matches"
    )
    lower_seed = db.relationship(
        "CutPlayer", foreign_keys=[lower_seed_id], backref="lower_seed_matches"
    )
    corp_player = db.relationship(
        "CutPlayer", foreign_keys=[corp_player_id], backref="corp_cut_matches"
    )
    runner_player = db.relationship(
        "CutPlayer",
        foreign_keys=[runner_player_id],
        backref="runner_cut_matches",
    )

    def __repr__(self) -> str:
        return f"<CutMatch>: {self.cut_id} <Table> {self.table_number} - Result: {self.result}"

    def conclude(self):
        if self.result not in [-1, 1]:
            raise ConclusionError("No result recorded")
        self.concluded = True
        if self.reset == 1:
            self.winner_match_id = self.corp_player_id
            self.loser_match_id = self.runner_player_id
        else:
            self.winner_match_id = self.runner_player_id
            self.loser_match_id = self.corp_player_id
        self.update_elim()
        db.session.add(self)
        db.session.commit()

    def corp_win(self):
        self.result = 1
        db.session.add(self)
        db.session.commit()

    def runner_win(self):
        self.result = -1
        db.session.add(self)
        db.session.commit()

    def reset(self):
        self.result = None
        self.concluded = False
        db.session.add(self)
        db.session.commit()

    def add_player(self, cutplayer: CutPlayer):
        """_summary_: Adds a player to the match."""
        if self.higher_seed_id is None:
            self.higher_seed_id = cutplayer.id
        elif self.lower_seed_id is None:
            # Because lower numbered seed is higher seed
            if cutplayer.seed < CutPlayer.query.get(self.higher_seed_id).seed:
                self.lower_seed_id = self.higher_seed_id
                self.higher_seed_id = cutplayer.id
            else:
                self.lower_seed_id = cutplayer.id
        else:
            raise Exception("Match is full")
        db.session.add(self)
        db.session.commit()

    def determine_sides(self, is_second_final=False):
        """_summary_: Determines the sides of the match based on the side balance of the players.
        If the side balance is equal, it will randomly choose a side for each player.
        Otherwise, the player with the higher side balance will be the runner player.
        """
        if is_second_final:
            prior_match = self.cut.get_match_by_table(self.table_number - 1)
            self.corp_player_id = prior_match.runner_player_id
            self.runner_player_id = prior_match.corp_player_id
            db.session.add(self)
            db.session.commit()
            return self
        higher_seed = CutPlayer.query.get(self.higher_seed_id)
        lower_seed = CutPlayer.query.get(self.lower_seed_id)
        if higher_seed.get_side_balance() > lower_seed.get_side_balance():
            self.corp_player_id = self.lower_seed_id
            self.runner_player_id = self.higher_seed_id
        elif higher_seed.get_side_balance() < lower_seed.get_side_balance():
            self.corp_player_id = self.higher_seed_id
            self.runner_player_id = self.lower_seed_id
        else:
            if randint(0, 1):
                self.corp_player_id = self.lower_seed_id
                self.runner_player_id = self.higher_seed_id
            else:
                self.corp_player_id = self.higher_seed_id
                self.runner_player_id = self.lower_seed_id
        db.session.add(self)
        db.session.commit()
        return self

    def get_winner(self):
        """_summary_: Returns the winner of the match."""
        if self.result == 1:
            return self.corp_player
        elif self.result == -1:
            return self.runner_player
        else:
            raise ConclusionError("Match has not been concluded")

    def get_loser(self):
        """_summary_: Returns the loser of the match."""
        if self.result == 1:
            return self.runner_player
        elif self.result == -1:
            return self.corp_player
        else:
            raise ConclusionError("Match has not been concluded")

    def update_elim(self):
        """
        Checks against the bracket and updates the loser's elimination round if relevant.
        """
        bracket = get_bracket(self.cut.num_players, self.cut.double_elim)
        for match in bracket[f"round_{self.rnd}"]:
            if match["table"] == self.table_number:
                if "final" in match.keys() and not match["elim"]:

                    lower_semis_table_number = self.table_number - 1
                    semi_winner_id = (
                        self.cut.get_match_by_table(lower_semis_table_number)
                        .get_winner()
                        .id
                    )
                    if semi_winner_id == self.loser_match_id:
                        self.get_loser().elim_round = self.rnd
                        self.get_winner().elim_round = self.rnd + 1
                        db.session.add(self.get_loser())
                        db.session.add(self.get_winner())
                        db.session.commit()
                else:
                    if match["elim"]:
                        self.get_loser().elim_round = self.rnd
                        db.session.add(self.get_loser())
                        db.session.commit()
                        if "final" in match.keys():

                            self.get_winner().elim_round = self.rnd + 1
                            db.session.add(self.get_winner())
                            db.session.commit()

    def swap_sides(self):
        """_summary_: Swaps the sides of the match."""
        self.corp_player_id, self.runner_player_id = (
            self.runner_player_id,
            self.corp_player_id,
        )
        db.session.add(self)
        db.session.commit()
