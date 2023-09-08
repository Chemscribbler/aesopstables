from data_models.model_store import db


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    rnd = db.Column(db.Integer)
    corp_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    runner_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    result = db.Column(db.Integer)
    concluded = db.Column(db.Boolean, default=False)
    is_bye = db.Column(db.Boolean, default=False)
    table_number = db.Column(db.Integer)

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
