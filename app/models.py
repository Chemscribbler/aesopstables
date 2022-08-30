from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    admin_rights = db.Column(db.Boolean, default=False)
    tournaments = db.relationship("Tournament", backref="TO", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User> {self.name}"


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    corp = db.Column(db.String)
    runner = db.Column(db.String)
    corp_deck = db.Column(db.Text)
    runner_deck = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))

    tournament = db.relationship("Tournament", back_populates="players")

    def __repr__(self) -> str:
        return f"<Player> {self.name}:{self.id} - Tournament {self.tid}"


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

    def __repr__(self) -> str:
        return f"<Tournament> {self.name}: {self.id}"


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
