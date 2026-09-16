import re
import numpy as np
from sentence_transformers import SentenceTransformer

# Cached global model instance
_MODEL_INSTANCE = None

def get_transformer_model():
    """Lazy load and cache lightweight SentenceTransformer model."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        # Load fast, lightweight 384-dimensional embedding model (~80MB)
        _MODEL_INSTANCE = SentenceTransformer('all-MiniLM-L6-v2')
    return _MODEL_INSTANCE

def calculate_match_score(resume_text, job_title, job_description, required_skills_str=""):
    """
    Calculate AI semantic cosine similarity score (0-100%) and extract matched/missing skills.
    
    :param resume_text: Raw candidate resume text.
    :param job_title: Title of job posting.
    :param job_description: Description text of job posting.
    :param required_skills_str: Comma-separated list of required skills.
    :return: dict with 'score', 'matched_skills', 'missing_skills', 'total_required_skills'
    """
    if not resume_text or not job_description:
        return {
            'score': 0.0,
            'matched_skills': [],
            'missing_skills': [],
            'total_required_skills': 0
        }

    # 1. Parse Required Skills & Keyword Extraction
    skills_list = []
    if required_skills_str:
        skills_list = [s.strip() for s in required_skills_str.split(',') if s.strip()]

    matched_skills = []
    missing_skills = []

    resume_lower = resume_text.lower()
    for skill in skills_list:
        # Simple case-insensitive word boundary or substring match
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, resume_lower) or skill.lower() in resume_lower:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    # 2. Semantic Embedding Comparison via SentenceTransformer
    try:
        model = get_transformer_model()
        job_prompt = f"Job Title: {job_title}. Description: {job_description}. Required Skills: {required_skills_str or ''}"
        
        # Generate normalized 384-dimensional dense vector embeddings
        embeddings = model.encode([resume_text, job_prompt], normalize_embeddings=True)
        
        # Cosine similarity of normalized vectors is the dot product
        raw_sim = float(np.dot(embeddings[0], embeddings[1]))
        
        # Scale to 0.0 - 100.0 percentage range
        # Note: Cosine similarity for semantic texts typically ranges between 0.15 and 0.85
        score_pct = round(max(0.0, min(100.0, raw_sim * 100)), 1)
    except Exception as e:
        # Fallback if embedding computation fails
        score_pct = 50.0

    # 3. Generate Candidate-Tailored Suggested Interview Questions
    from utils.question_generator import generate_interview_questions
    interview_questions = generate_interview_questions(
        job_title=job_title,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        score=score_pct
    )

    return {
        'score': score_pct,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'total_required_skills': len(skills_list),
        'interview_questions': interview_questions
    }
