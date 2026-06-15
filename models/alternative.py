from models import db

class Alternative(db.Model):
    __tablename__ = 'alternatives'

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('decision_problems.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # Relationship for cascade delete of consequences
    consequences = db.relationship('Consequence', backref='alternative', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'name': self.name
        }

    def __repr__(self):
        return f'<Alternative {self.name}>'
