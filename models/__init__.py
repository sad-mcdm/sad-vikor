from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.problem import DecisionProblem
from models.alternative import Alternative
from models.criterion import Criterion
from models.consequence import Consequence

__all__ = [
    'db',
    'User',
    'DecisionProblem',
    'Alternative',
    'Criterion',
    'Consequence'
]
