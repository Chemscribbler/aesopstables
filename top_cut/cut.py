from aesops import db
from sqlalchemy.orm import Mapped
from sqlalchemy import and_
from pairing.match import ConclusionError
from pairing.player import Player
from pairing.tournament import Tournament
from random import randint
from top_cut.cut_tables import (
    double_elim_4,
    double_elim_8,
    double_elim_16,
    single_elim_4,
)
from top_cut.cut_player import CutPlayer
from top_cut.elim_match import ElimMatch


class Cut(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    rnd = db.Column(db.Integer, default=1)
    num_players = db.Column(db.Integer)
    double_elim = db.Column(db.Boolean, default=False)
    tournament = db.relationship("Tournament", back_populates="cut")

    def __repr__(self) -> str:
        return f"<Cut> TID: {self.tid} - RND: {self.rnd}"

    def get_players_by_seed(self):
        player_list = self.players
        player_list.sort(key=lambda x: x.seed)
        return player_list

    def generate_round(self):
        if not self.double_elim:
            bracket = single_elim_4
        elif self.num_players == 4:
            bracket = double_elim_4
        elif self.num_players == 8:
            bracket = double_elim_8
        elif self.num_players == 16:
            bracket = double_elim_16
        else:
            raise ValueError("Invalid number of players for cut")

        if self.rnd == 1:
            plyrs = self.get_players_by_seed()
            for m in bracket["round_1"]:
                match = ElimMatch(cut_id=self.id, rnd=1, table_number=m["table"])
                match.add_player(plyrs[m["higher_seed"] - 1])
                match.add_player(plyrs[m["lower_seed"] - 1])
                match.determine_sides()
                db.session.add(match)
            db.session.commit()
        else:
            matches = bracket[f"round_{self.rnd + 1}"]
            for match in matches:
                match = ElimMatch(
                    cut_id=self.id, rnd=self.rnd + 1, table_number=match["table"]
                )
                table_number, who_grab = match["higher_seed"]
                if who_grab == "winner":
                    player = self.get_match_by_table(table_number).get_winner()
                elif who_grab == "loser":
                    player = self.get_match_by_table(table_number).get_loser()
                match.add_player(player)

                table_number, who_grab = match["lower_seed"]
                if who_grab == "winner":
                    player = self.get_match_by_table(table_number).get_winner()
                elif who_grab == "loser":
                    player = self.get_match_by_table(table_number).get_loser()
                match.add_player(player)

                db.session.add(match)
            db.session.commit()

    def get_match_by_table(self, table_number):
        match = ElimMatch.query.filter(
            and_(ElimMatch.table_number == table_number, ElimMatch.tid == self.tid)
        ).first()
        return match

    def create(self, tournament: Tournament, num_players: int, double_elim: bool):
        self.tid = tournament.id
        if num_players not in [4, 8, 16]:
            raise ValueError("Invalid number of players for cut")
        self.num_players = num_players
        self.double_elim = double_elim
        db.session.add(self)
        db.session.commit()
        top_players = tournament.top_n_cut(n=num_players)
        for i, player in enumerate(top_players):
            cut_player = CutPlayer()
            cut_player.player_id = player.id
            cut_player.seed = i + 1
            cut_player.cut_id = self.id
            db.session.add(cut_player)
        db.session.commit()

    def destroy(self):
        for player in CutPlayer.query.filter_by(cid=self.id):
            db.session.delete(player)
        for match in ElimMatch.query.filter_by(cid=self.id):
            db.session.delete(match)
        db.session.delete(self)
        db.session.commit()
