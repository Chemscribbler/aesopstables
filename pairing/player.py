from aesops import db
from sqlalchemy.orm import Mapped


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
    first_round_bye: Mapped[bool] = db.Column(db.Boolean, default=False)

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
        return round(opp_total_sos / max(self.get_record["games_played"], 1), 3)

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
        db.session.commit()

    def undrop(self):
        self.active = True
        db.session.add(self)
        db.session.commit()

    def is_paired(self, rnd):
        for match in self.runner_matches:
            if match.rnd == rnd:
                return True
        for match in self.corp_matches:
            if match.rnd == rnd:
                return True
        return False
