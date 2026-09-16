import os

class Config:
    """Base configuration settings for HR Portal web application."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-hr-portal-2026'
    
    # SQLite Database settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'hr_portal.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads folder settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file upload size
