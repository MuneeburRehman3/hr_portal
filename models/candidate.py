from models import db

class Candidate(db.Model):
    """Candidate database model storing job applicants, PDF filename, and extracted resume text."""
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    resume_filename = db.Column(db.String(255), nullable=True)  # Name of saved PDF file
    resume_text = db.Column(db.Text, nullable=False)            # Extracted resume text for AI screening
    applied_job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)

    def __repr__(self):
        return f'<Candidate {self.name} ({self.email}) - Job #{self.applied_job_id}>'
