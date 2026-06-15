from models import db

class Criterion(db.Model):
    __tablename__ = 'criteria'

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('decision_problems.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    criteria_type = db.Column(db.String(10), nullable=False)  # 'benefit' or 'cost'
    weight = db.Column(db.Float, nullable=True)               # Final calculated weight
    rank_position = db.Column(db.Integer, nullable=True)       # Optional importance rank

    # Relationship for cascade delete of consequences
    consequences = db.relationship('Consequence', backref='criterion', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'name': self.name,
            'criteria_type': self.criteria_type,
            'weight': self.weight,
            'rank_position': self.rank_position
        }

    def __repr__(self):
        return f'<Criterion {self.name} ({self.criteria_type})>'
