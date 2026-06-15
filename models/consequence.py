from models import db

class Consequence(db.Model):
    __tablename__ = 'consequences'

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('decision_problems.id'), nullable=False)
    alternative_id = db.Column(db.Integer, db.ForeignKey('alternatives.id'), nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criteria.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('problem_id', 'alternative_id', 'criterion_id', name='uq_consequence_cell'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'alternative_id': self.alternative_id,
            'criterion_id': self.criterion_id,
            'value': self.value
        }

    def __repr__(self):
        return f'<Consequence problem={self.problem_id} alt={self.alternative_id} crit={self.criterion_id} val={self.value}>'
