from models import db

class Attendance(db.Model):
    """Attendance model tracking daily employee check-ins."""
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Late

    # Unique constraint ensuring an employee has only one record per date
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='uq_employee_date'),
    )

    def __repr__(self):
        return f'<Attendance Employee #{self.employee_id} - {self.date}: {self.status}>'
