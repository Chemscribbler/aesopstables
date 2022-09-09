from datetime import date
from unittest import result
from app import db


class ConclusionError(BaseException):
    pass


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    admin_rights = db.Column(db.Boolean, default=False)
    tournaments = db.relationship("Tournament", backref="TO", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User> {self.name}"

    def create_tournament(self, name, date=date.today()):
        t = Tournament(name=name, date=date, admin_id=self.id)
        db.session.add(t)
        db.session.commit()


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    corp = db.Column(db.String)
    runner = db.Column(db.String)
    corp_deck = db.Column(db.Text)
    runner_deck = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    recieved_bye = db.Column(db.Boolean, default=False)

    tournament = db.relationship("Tournament", back_populates="players")

    def __repr__(self) -> str:
        return f"<Player> {self.name}:{self.id} - Tournament {self.tid}"

    def get_record(self) -> dict:
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
            games_played += 1
        return {"score": score, "games_played": games_played}

    def get_side_balance(self):
        return len(self.corp_matches) - len(self.runner_matches)

    def get_sos(self):
        opp_total_score = 0
        total_opp_matches = 0
        for match in self.runner_matches:
            opp_record = match.corp_player.get_record()
            opp_total_score += opp_record["score"]
            total_opp_matches += opp_record["games_played"]
        for match in self.corp_matches:
            opp_record = match.corp_player.get_record()
            opp_total_score += opp_record["score"]
            total_opp_matches += opp_record["games_played"]
        return round(opp_total_score / total_opp_matches, 3)

    def get_esos(self):
        opp_total_sos = 0
        total_opp_matches = 0
        for match in self.runner_matches:
            opp_record = match.corp_player.get_record()
            opp_total_sos += match.corp_player.get_sos()
            total_opp_matches += opp_record["games_played"]
        for match in self.corp_matches:
            opp_record = match.corp_player.get_sos()
            opp_total_sos += opp_record["score"]
            total_opp_matches += opp_record["games_played"]
        return round(opp_total_sos / total_opp_matches, 3)


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String, nullable=False)
    current_round = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime(timezone=True))

    players = db.relationship("Player", back_populates="tournament")
    matches = db.relationship("Match", back_populates="tournament")
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
    ):
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

    def conclude_round(self):
        for match in self.active_matches:
            match.conclude()
        self.current_round += 1
        db.session.add(self)
        db.session.commit()


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    rnd = db.Column(db.Integer)
    corp_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    runner_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    result = db.Column(db.Integer)
    concluded = db.Column(db.Boolean, default=False)

    corp_player = db.relationship(
        "Player", foreign_keys=[corp_player_id], backref="corp_matches"
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
        db.session.add(self)
        db.session.commit()
