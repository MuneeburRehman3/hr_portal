from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(UserMixin, db.Model):
    """User authentication and role model."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # 'hr' or 'employee'
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)

    def set_password(self, password):
        """Hash and set user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_hr(self):
        """Check if user has HR admin role."""
        return self.role == 'hr'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
