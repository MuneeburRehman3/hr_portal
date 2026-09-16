# Flask HR Portal

> An AI-powered workforce management and candidate screening system built with Flask, SQLAlchemy, SentenceTransformers, and Bootstrap 5.

---

## 📋 Overview

The **Flask HR Portal** is a comprehensive Human Resources management application that combines core workforce operations (employee directory, leave workflows, attendance logging, and support ticket management) with **AI-driven recruitment intelligence**. Utilizing local NLP sentence transformer embeddings, the portal automatically ranks candidate PDF resumes against job requirements and generates candidate-tailored interview questions.

---

## 🌟 Key Features

### 👑 HR Admin Role
- **Employee Directory Management**: Complete CRUD operations for staff records with department tagging, position titles, and search filter.
- **Leave Request Management**: Review, validate date ranges, and approve or reject employee leave applications.
- **Attendance Management**: Mark and update daily check-ins (`Present`, `Late`, `Absent`) with automatic duplicate date prevention.
- **AI-Powered Recruitment**: Post job requisitions, upload candidate PDF resumes, and view automated applicant rankings.
- **Semantic AI Resume Screening**: Compare resumes against job descriptions using dense vector embeddings to calculate match scores (0–100%) and extract matched vs. missing required skills.
- **AI-Generated Interview Questions**: Review 3–4 automatically generated, candidate-tailored interview questions targeting specific skill gaps and matched strengths.
- **Support Ticket Resolution**: Inspect employee help inquiries, type response/resolution notes, and mark tickets as resolved.
- **HR Insights Dashboard**: Real-time overview of workforce headcount, pending leave requests, today's attendance summary, and recent activity feeds.

### 👤 Employee Role
- **Personalized Employee Dashboard**: Overview of personal profile details, leave request counts, attendance logs, and active support tickets.
- **Profile View**: View contract details, position, department, and join date (`/my-profile`).
- **Leave Self-Service**: Submit leave requests with automatic end-date validation and track approval status.
- **View-Only Attendance**: Access read-only personal biometric check-in history.
- **Support Tickets**: Submit support inquiries to HR, track open/resolved ticket status, and view HR's response notes.

---

## 🛠️ Tech Stack

- **Backend Framework**: Flask (Python 3)
- **Database & ORM**: SQLite, Flask-SQLAlchemy
- **Authentication & Security**: Flask-Login, Werkzeug Security (salted password hashing), Custom RBAC Decorator (`@hr_required`)
- **AI & NLP Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`), NumPy, Scikit-Learn
- **PDF Processing**: `pypdf` / `PyPDF2`
- **Frontend UI**: Bootstrap 5, Bootstrap Icons, Custom Theme CSS

---

## 🧠 How AI Features Work

### 1. AI Resume Screening & Semantic Match Scoring
1. **Dense Vector Embeddings**: Uses `sentence-transformers` (`all-MiniLM-L6-v2`) to encode candidate resume text and job description prompts into 384-dimensional normalized dense vectors.
2. **Cosine Similarity**: Calculates the dot product of normalized embeddings to generate a semantic match score percentage (0–100%), capturing context beyond simple keyword matching.
3. **Skill Gap & Match Extraction**: Uses regex pattern parsing to identify which required skills appear in the resume text (**Matched Skills**) versus which are missing (**Missing Skills**).

### 2. Tailored Interview Question Generator
1. **Candidate-Specific Slot Filling**: Analyzes the parsed `matched_skills`, `missing_skills`, and overall match score for each candidate.
2. **Targeted Question Prompts**: Generates 3–4 tailored interview questions:
   - **Skill Gaps**: Probes missing required skills (e.g. *"Our team relies on Docker, which wasn't highlighted in your resume. Can you describe your experience with Docker?"*).
   - **Matched Strengths**: Deep-dives into technical proficiency for skills found on the resume.
   - **Role Leadership / Fit**: Evaluates general alignment and career goals.
3. **Rationale Notes**: Provides an explicit rationale note for HR explaining why each question was generated.

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10 or higher
- Git

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/flask-hr-portal.git
   cd flask-hr-portal
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the portal**:
   Open your browser and navigate to `http://127.0.0.1:5000`.

---

## 🔑 Demo Credentials

The database automatically seeds two initial user accounts upon first launch:

| Role | Username | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **HR Admin** | `admin` | `admin123` | Full access (`/dashboard`, `/employees`, `/recruitment`, `/leave`, `/attendance`, `/support`) |
| **Employee** | `john` | `john123` | Employee access (`/my-profile`, own leave, own attendance, own support tickets) |

---

## 🧪 Running Tests

Run the automated unit test suite:

```bash
python -m unittest discover -p "test_*.py"
```

---

## 🔮 Future Improvements

- **Candidate Self-Service Portal**: Public job portal allowing external candidates to submit applications directly.
- **Attrition Risk Prediction**: Machine learning model analyzing attendance patterns and tenure to predict turnover risk.
- **Email & Push Notifications**: Automated email notifications via SendGrid/SMTP for leave approvals and ticket responses.
- **Calendar Integration**: iCal and Google Calendar sync for approved employee leave periods.
- **Multi-Tenancy Support**: Departmental hierarchy permissions and multi-office support.
