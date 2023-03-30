from aesops import db
from sqlalchemy.orm import Mapped


class ConclusionError(BaseException):
    pass


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    rnd = db.Column(db.Integer)
    corp_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    runner_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    result = db.Column(db.Integer)
    concluded = db.Column(db.Boolean, default=False)
    is_bye = db.Column(db.Boolean, default=True)
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
