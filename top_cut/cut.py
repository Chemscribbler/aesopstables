from aesops import db
from sqlalchemy.orm import Mapped
from sqlalchemy import and_
from pairing.match import ConclusionError
from pairing.player import Player
from pairing.tournament import Tournament
from random import randint
from top_cut.cut_tables import get_bracket
from top_cut.cut_player import CutPlayer
from top_cut.elim_match import ElimMatch


class Cut(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    rnd = db.Column(db.Integer, default=1)
    num_players = db.Column(db.Integer)
    double_elim = db.Column(db.Boolean, default=False)
    tournament = db.relationship("Tournament", back_populates="cut")
    current_matches = db.relationship(
        "ElimMatch",
        primaryjoin="and_(Cut.id == ElimMatch.cut_id, ElimMatch.rnd == Cut.rnd)",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Cut> TID: {self.tid} - RND: {self.rnd}"

    def get_players_by_seed(self):
        player_list = self.players
        player_list.sort(key=lambda x: x.seed)
        return player_list

    def generate_round(self):
        bracket = get_bracket(self.num_players, self.double_elim)
        print(f"Bracket: {bracket}")
        for match in self.matches:
            if not match.concluded:
                raise ConclusionError(
                    "All matches must be concluded before generating next round"
                )
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
            if self.get_standings()["unranked_players"] == 0:
                raise ValueError("All Players have been ranked")
            matches = bracket[f"round_{self.rnd}"]
            for match in matches:
                cut_match = ElimMatch(
                    cut_id=self.id, rnd=self.rnd, table_number=match["table"]
                )
                if self.num_players == 3:
                    plyrs = self.get_players_by_seed()
                    player = plyrs[0]
                else:
                    table_number, who_grab = match["higher_seed"]
                    if who_grab == "winner":
                        print(f"Getting table {table_number} winner")
                        player = self.get_match_by_table(table_number).get_winner()
                    elif who_grab == "loser":
                        print(f"Getting table {table_number} loser")
                        player = self.get_match_by_table(table_number).get_loser()
                    else:
                        raise ValueError(f"Invalid value for who_grab: {who_grab}")
                print(player)
                cut_match.add_player(player)
                print(cut_match.higher_seed)
                table_number, who_grab = match["lower_seed"]
                if who_grab == "winner":
                    print(f"Getting table {table_number} winner")
                    player = self.get_match_by_table(table_number).get_winner()
                elif who_grab == "loser":
                    print(f"Getting table {table_number} loser")
                    player = self.get_match_by_table(table_number).get_loser()
                cut_match.add_player(player)
                print(cut_match.higher_seed)
                print(cut_match.lower_seed)
                cut_match.determine_sides(is_second_final=self.is_second_final())
                db.session.add(cut_match)
            db.session.commit()

    def get_match_by_table(self, table_number):
        match = ElimMatch.query.filter(
            and_(ElimMatch.table_number == table_number, ElimMatch.cut_id == self.id)
        ).first()
        return match

    def create(self, tournament: Tournament, num_players: int, double_elim: bool):
        self.tid = tournament.id
        if num_players not in [3, 4, 8, 16]:
            raise ValueError(f"Invalid number of players for cut {num_players}")
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
        for match in ElimMatch.query.filter_by(cut_id=self.id).all():
            db.session.delete(match)

        for player in CutPlayer.query.filter_by(cut_id=self.id).all():
            db.session.delete(player)
        db.session.delete(self)
        db.session.commit()

    def conclude_round(self):
        for match in self.current_matches:
            match.conclude()
        self.rnd += 1
        db.session.add(self)
        db.session.commit()

    def get_standings(self):
        players = self.players
        # Check to see if only one player hasn't been eliminated
        # Check length of players with no value for elim_round
        if len([player for player in players if player.elim_round is None]) == 0:
            players.sort(key=lambda x: x.seed)
            players.sort(key=lambda x: x.elim_round, reverse=True)
            return {"ranked_players": players, "unranked_players": 0}
        else:
            eliminated_players = [player for player in players if player.elim_round]
            eliminated_players.sort(key=lambda x: x.seed)
            eliminated_players.sort(key=lambda x: x.elim_round)
            remaining_players = [player for player in players if not player.elim_round]
            return {
                "ranked_players": eliminated_players,
                "unranked_players": len(remaining_players),
            }

    def get_round(self, rnd: int):
        return ElimMatch.query.filter(
            and_(ElimMatch.cut_id == self.id, ElimMatch.rnd == rnd)
        ).all()

    def delete_round(self, rnd: int):
        if rnd == 1:
            raise ValueError("Cannot delete first round")
        if rnd < self.rnd:
            raise ValueError("Cannot delete round that has already been played")
        if rnd > self.rnd:
            raise ValueError("Cannot delete future round")
        for match in self.get_round(rnd):
            db.session.delete(match)
            db.session.commit()
        self.rnd -= 1
        db.session.add(self)
        db.session.commit()
        for player in self.players:
            if player.elim_round is None:
                continue
            if player.elim_round >= rnd:
                player.elim_round = None
                db.session.add(player)
                db.session.commit()

    def is_second_final(self):
        if not self.double_elim:
            return False
        bracket = get_bracket(self.num_players, self.double_elim)
        round_numbers = [int(round_name.split("_")[1]) for round_name in bracket.keys()]
        return self.rnd == max(round_numbers)
