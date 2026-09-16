from models import db

class JobPosting(db.Model):
    """JobPosting database model storing open job requisitions."""
    __tablename__ = 'job_postings'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(80), nullable=True)
    required_skills = db.Column(db.String(255), nullable=True)  # e.g., "Python, Flask, SQL, HTML"
    description = db.Column(db.Text, nullable=False)

    # Relationship to Candidate model
    candidates = db.relationship('Candidate', backref='job_posting', lazy=True, cascade='all, delete-orphan')

    @property
    def skills_list(self):
        """Helper to split comma-separated required_skills into a clean list."""
        if self.required_skills:
            return [skill.strip() for skill in self.required_skills.split(',') if skill.strip()]
        return []

    def __repr__(self):
        return f'<JobPosting {self.title} ({self.department or "General"})>'
