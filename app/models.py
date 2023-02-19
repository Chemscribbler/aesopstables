from datetime import date
from app import db
from sqlalchemy.orm import Mapped
from random import shuffle


class ConclusionError(BaseException):
    pass


class User(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[bool] = db.Column(db.String, nullable=False)
    password_hash: Mapped[str] = db.Column(db.String, nullable=False)
    admin_rights: Mapped[bool] = db.Column(db.Boolean, default=False)
    tournaments: Mapped["Tournament"] = db.relationship(
        "Tournament", backref="TO", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<User> {self.name}"

    def create_tournament(self, name, date=date.today()):
        t = Tournament(name=name, date=date, admin_id=self.id)
        db.session.add(t)
        db.session.commit()


class Player(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String, nullable=False)
    corp: Mapped[str] = db.Column(db.String)
    runner: Mapped[str] = db.Column(db.String)
    corp_deck: Mapped[str] = db.Column(db.Text)
    runner_deck: Mapped[str] = db.Column(db.Text)
    active: Mapped[bool] = db.Column(db.Boolean, default=True)
    tid: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("tournament.id"), nullable=False
    )
    recieved_bye: Mapped[bool] = db.Column(db.Boolean, default=False)
    score: Mapped[int] = db.Column(db.Integer, default=0)
    sos: Mapped[float] = db.Column(db.Numeric, default=0.0)
    esos: Mapped[float] = db.Column(db.Numeric, default=0.0)
    is_bye: Mapped[bool] = db.Column(db.Boolean, default=False)

    tournament = db.relationship("Tournament", back_populates="players")

    def __repr__(self) -> str:
        return f"<Player> {self.name}:{self.id} - Tournament {self.tid}"

    def get_record(self) -> dict[str, float]:
        score = 0
        games_played = 0
        for match in self.runner_matches:
            if not match.concluded:
                continue
            if match.result == -1 and match.concluded:
                score += 3
            if match.result == 0 and match.concluded:
                score += 1
            games_played += 1
        for match in self.corp_matches:
            if not match.concluded:
                continue
            if match.result == 1 and match.concluded:
                score += 3
            if match.result == 0 and match.concluded:
                score += 1
            # Only doing this here because bye is always Corp side
            if not match.is_bye:
                games_played += 1
        return {"score": score, "games_played": games_played}

    def get_side_balance(self):
        played_corp_matchest = [
            m for m in self.corp_matches if m.is_bye == False and m.concluded
        ]
        return len(played_corp_matchest) - len(
            [m for m in self.runner_matches if m.concluded]
        )

    def get_sos(self) -> float:
        opp_total_score = 0
        total_opp_matches = 0
        for match in self.runner_matches:
            opp_record = match.corp_player.get_record()
            opp_total_score += opp_record["score"]
            total_opp_matches += opp_record["games_played"]
        for match in self.corp_matches:
            if match.is_bye:
                continue
            opp_record = match.runner_player.get_record()
            opp_total_score += opp_record["score"]
            total_opp_matches += opp_record["games_played"]
        return round(opp_total_score / max(total_opp_matches, 1), 3)

    def get_esos(self) -> float:
        opp_total_sos = 0
        total_opp_matches = 0
        for match in self.runner_matches:
            opp_record = match.corp_player.get_record()
            opp_total_sos += match.corp_player.get_sos()
            total_opp_matches += opp_record["games_played"]
        for match in self.corp_matches:
            if match.is_bye:
                continue
            opp_record = match.runner_player.get_record()
            opp_total_sos += match.runner_player.get_sos()
            total_opp_matches += opp_record["games_played"]
        return round(opp_total_sos / max(total_opp_matches, 1), 3)

    def update_score(self):
        old_score = self.score
        self.score = self.get_record()["score"]
        print(f"Updated {self.name}'s score from {old_score} to {self.score}")
        db.session.add(self)
        db.session.commit()

    def update_sos_esos(self):
        self.sos = self.get_sos()
        self.esos = self.get_esos()
        db.session.add(self)
        db.session.commit()

    def reset(self):
        self.update_score()
        self.update_sos_esos()

    def drop(self):
        self.active = False
        db.session.add(self)
        db.session.commit(self)


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String, nullable=False)
    current_round = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime(timezone=True))

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


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    rnd = db.Column(db.Integer)
    corp_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    runner_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    result = db.Column(db.Integer)
    concluded = db.Column(db.Boolean, default=False)
    is_bye = db.Column(db.Boolean, default=True)

    corp_player = db.relationship(
        "Player",
        foreign_keys=[corp_player_id],
        backref="corp_matches",
    )
    runner_player = db.relationship(
        "Player", foreign_keys=[runner_player_id], backref="runner_matches"
    )
    tournament = db.relationship("Tournament", back_populates="matches")

    def __repr__(self) -> str:
        return f"<Match> TID: {self.tid} - RND: {self.rnd} - Result: {self.result}"

    def conclude(self):
        if self.result not in [-1, 0, 1]:
            raise ConclusionError("No result recorded")
        self.concluded = True
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

    def tie(self):
        self.result = 0
        db.session.add(self)
        db.session.commit()

    def reset(self):
        self.result = None
        self.concluded = False
        db.session.add(self)
        db.session.commit()

    def delete(self):
        if self.is_bye:
            self.corp_player.recieved_bye = False
            self.corp_player.reset()
        else:
            self.corp_player.reset()
            self.runner_player.reset()
        db.session.delete(self)
        db.session.commit()
