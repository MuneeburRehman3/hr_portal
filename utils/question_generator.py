import random

def generate_interview_questions(job_title, matched_skills, missing_skills, score=50.0):
    """
    Generate 3-4 candidate-tailored interview questions based on matched strengths,
    missing skill gaps, and overall job alignment.

    :param job_title: Title of the job posting.
    :param matched_skills: List of required skills found in the candidate's resume.
    :param missing_skills: List of required skills missing from the candidate's resume.
    :param score: Overall AI semantic match score (0-100%).
    :return: List of question dicts with 'category', 'target', 'question', and 'rationale'.
    """
    questions = []

    # 1. Generate Questions for Missing Skills (Skill Gaps)
    for skill in missing_skills[:2]:
        question_templates = [
            f"Our team heavily relies on {skill}, which wasn't highlighted in your resume. Can you describe your experience with {skill} or how quickly you've adopted similar tools in past roles?",
            f"If selected for the {job_title} position, what steps would you take to quickly ramp up and achieve proficiency in {skill} during your first month?",
            f"Can you share an example of a technical challenge where you had to work with a skill like {skill} without prior formal training?"
        ]
        # Pick deterministic template based on skill hash
        idx = hash(skill) % len(question_templates)
        questions.append({
            'category': 'Skill Gap',
            'badge_class': 'bg-danger-subtle text-danger border border-danger-subtle',
            'icon': 'bi-exclamation-triangle-fill text-danger',
            'target': skill,
            'question': question_templates[idx],
            'rationale': f"Targeted at missing skill gap '{skill}' identified during resume parsing."
        })

    # 2. Generate Questions for Matched Skills (Strengths)
    for skill in matched_skills[:2]:
        question_templates = [
            f"Your resume shows strong experience in {skill}. Could you walk us through your most complex implementation or architectural challenge involving {skill}?",
            f"What best practices or design patterns do you enforce when building production applications using {skill}?",
            f"How have you leveraged your expertise in {skill} to optimize performance, reliability, or team productivity in prior projects?"
        ]
        idx = hash(skill) % len(question_templates)
        questions.append({
            'category': 'Matched Strength',
            'badge_class': 'bg-success-subtle text-success border border-success-subtle',
            'icon': 'bi-check-circle-fill text-success',
            'target': skill,
            'question': question_templates[idx],
            'rationale': f"Probing deep proficiency in candidate strength '{skill}'."
        })

    # 3. Supplemental Role Fit / Behavioral Question to ensure 3-4 questions total
    while len(questions) < 3:
        if score >= 70:
            questions.append({
                'category': 'Role Leadership',
                'badge_class': 'bg-primary-subtle text-primary border border-primary-subtle',
                'icon': 'bi-stars text-primary',
                'target': job_title,
                'question': f"Given your high technical match ({score}%) for the {job_title} role, how do you approach mentoring junior team members and driving engineering excellence?",
                'rationale': f"Tailored to high overall semantic match score ({score}%)."
            })
        else:
            questions.append({
                'category': 'Role Fit',
                'badge_class': 'bg-info-subtle text-info-emphasis border border-info-subtle',
                'icon': 'bi-person-badge text-info',
                'target': job_title,
                'question': f"What specific aspect of the {job_title} requisition interests you most, and how do your transferable skills make you a strong candidate?",
                'rationale': f"Evaluates general alignment and enthusiasm for the {job_title} position."
            })

    # Limit to maximum 4 questions
    return questions[:4]
