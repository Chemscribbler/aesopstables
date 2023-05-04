from aesops import db
from sqlalchemy.orm import Mapped
from pairing.player import Player
from pairing.match import Match
from random import shuffle


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String, nullable=False)
    current_round = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime(timezone=True), default=db.func.now())
    description = db.Column(db.String)

    players = db.relationship(
        "Player", back_populates="tournament", cascade="all, delete-orphan"
    )
    matches = db.relationship(
        "Match", back_populates="tournament", cascade="all, delete-orphan"
    )
    active_players = db.relationship(
        "Player",
        primaryjoin="and_(Tournament.id == Player.tid, Player.active==True)",
        viewonly=True,
    )
    active_matches = db.relationship(
        "Match",
        primaryjoin="and_(Tournament.id == Match.tid, Match.rnd == Tournament.current_round)",
        viewonly=True,
    )
    cut = db.relationship("Cut", uselist=False, back_populates="tournament")

    def __repr__(self) -> str:
        return f"<Tournament> {self.name}: {self.id}"

    def add_player(
        self, name, corp=None, runner=None, corp_deck=None, runner_deck=None
    ) -> Player:
        p = Player(
            name=name,
            corp=corp,
            runner=runner,
            corp_deck=corp_deck,
            runner_deck=runner_deck,
            tid=self.id,
        )
        db.session.add(p)
        db.session.commit()
        return p

    def conclude_round(self):
        for match in self.active_matches:
            match.conclude()
        for player in self.players:
            player.update_score()
            player.update_sos_esos()
        # self.current_round += 1
        db.session.add(self)
        db.session.commit()

    def rank_players(self):
        player_list = self.players
        player_list.sort(key=lambda x: x.esos, reverse=True)
        player_list.sort(key=lambda x: x.sos, reverse=True)
        player_list.sort(key=lambda x: x.get_record()["score"], reverse=True)
        return player_list

    def bye_setup(self) -> tuple[list[Player], Player]:
        if len(self.active_players) % 2 == 0:
            return (self.active_players, None)
        eligible_players = [p for p in self.active_players if not p.recieved_bye]
        lowest_score = 1000
        player_index = None
        shuffle(eligible_players)
        for index, p in enumerate(eligible_players):
            if p.score < lowest_score:
                lowest_score = p.score
                player_index = index
        bye_player = eligible_players.pop(player_index)
        non_bye_players = [p for p in self.active_players if p.id != bye_player.id]
        return (non_bye_players, bye_player)

    def get_round(self, round) -> list[Match]:
        return [m for m in self.matches if m.rnd == round]

    def unpair_round(self):
        if self.cut is not None:
            raise Exception("Cannot unpair a round after a cut has been made")
        for match in self.active_matches:
            match.delete()
        self.current_round -= 1
        db.session.add(self)
        db.session.commit()
        return self

    def top_n_cut(self, n):
        player_list = self.rank_players()
        cut_players = []
        for i in range(len(player_list)):
            if player_list[i].active:
                cut_players.append(player_list[i])
                if len(cut_players) == n:
                    break
        # cut_players = player_list[:n]
        return cut_players

    def get_unpaired_players(self):
        return [p for p in self.active_players if not p.is_paired(self.current_round)]
