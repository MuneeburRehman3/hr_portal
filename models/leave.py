from datetime import date
from models import db

class Leave(db.Model):
    """Leave database model storing leave applications."""
    __tablename__ = 'leaves'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Pending')

    @property
    def duration_days(self):
        """Calculate total leave duration in calendar days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def __repr__(self):
        return f'<Leave {self.leave_type} ({self.status}) - Employee ID {self.employee_id}>'
