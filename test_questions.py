import unittest
from utils.question_generator import generate_interview_questions
from utils.resume_matcher import calculate_match_score

class InterviewQuestionGeneratorTestCase(unittest.TestCase):
    def test_question_generation_gaps_and_strengths(self):
        """Test tailored question generation for candidate with both matched strengths and skill gaps."""
        matched_skills = ['Python', 'Flask']
        missing_skills = ['Docker', 'Kubernetes']
        
        questions = generate_interview_questions(
            job_title='Backend Developer',
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            score=65.0
        )
        
        # Verify 3-4 questions generated
        self.assertGreaterEqual(len(questions), 3)
        self.assertLessEqual(len(questions), 4)
        
        # Verify skill gaps are targeted in question categories
        categories = [q['category'] for q in questions]
        targets = [q['target'] for q in questions]
        
        self.assertIn('Skill Gap', categories)
        self.assertIn('Matched Strength', categories)
        self.assertIn('Docker', targets)
        self.assertIn('Python', targets)

    def test_resume_matcher_integration(self):
        """Test calculate_match_score includes interview_questions list in returned dictionary."""
        resume = "Experienced Software Engineer skilled in Python and Flask. Built REST APIs."
        job_title = "Senior Python Developer"
        job_desc = "Seeking a developer skilled in Python, Flask, Docker, and PostgreSQL."
        required_skills = "Python, Flask, Docker, PostgreSQL"
        
        result = calculate_match_score(
            resume_text=resume,
            job_title=job_title,
            job_description=job_desc,
            required_skills_str=required_skills
        )
        
        self.assertIn('interview_questions', result)
        questions = result['interview_questions']
        self.assertTrue(len(questions) >= 3)
        self.assertEqual(result['matched_skills'], ['Python', 'Flask'])
        self.assertEqual(result['missing_skills'], ['Docker', 'PostgreSQL'])

if __name__ == '__main__':
    unittest.main()
