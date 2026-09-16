from datetime import date
from models import db

class Employee(db.Model):
    """Employee database model storing staff records."""
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(80), nullable=True)
    position = db.Column(db.String(80), nullable=True)
    join_date = db.Column(db.Date, nullable=False, default=date.today)

    # Relationships
    leaves = db.relationship('Leave', backref='employee', lazy=True, cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='employee', lazy=True, cascade='all, delete-orphan')
    user_account = db.relationship('User', backref='employee', uselist=False)

    def __repr__(self):
        return f'<Employee {self.name} ({self.email})>'
