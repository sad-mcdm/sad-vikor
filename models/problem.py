from datetime import datetime, timezone
from models import db

class DecisionProblem(db.Model):
    __tablename__ = 'decision_problems'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    rationality = db.Column(db.String(50), nullable=False)  # 'compensatory' or 'non-compensatory'
    problematic = db.Column(db.String(50), nullable=False)   # 'choice', 'ranking', 'sorting', 'portfolio'
    method = db.Column(db.String(50), nullable=False)        # 'smarts', 'smarter', 'ahp', 'macbeth', 'bwm', 'bwt'
    
    # Store method-specific configuration (e.g. comparisons, criteria ranks, swing weights, etc.) as JSON
    preferences = db.Column(db.JSON, default=dict)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    alternatives = db.relationship('Alternative', backref='problem', lazy='dynamic', cascade='all, delete-orphan')
    criteria = db.relationship('Criterion', backref='problem', lazy='dynamic', cascade='all, delete-orphan')
    consequences = db.relationship('Consequence', backref='problem', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'rationality': self.rationality,
            'problematic': self.problematic,
            'method': self.method,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<DecisionProblem {self.name}>'
