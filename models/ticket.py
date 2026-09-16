from datetime import datetime
from models import db

class Ticket(db.Model):
    """Support Ticket model representing employee support inquiries to HR."""
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open', nullable=False)  # 'Open' or 'Resolved'
    reply = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to Employee
    employee = db.relationship('Employee', backref=db.backref('tickets', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Ticket #{self.id} {self.subject} ({self.status})>'
