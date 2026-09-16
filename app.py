import os
import uuid
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from config import Config
from models import db
from models.user import User
from models.employee import Employee
from models.leave import Leave
from models.attendance import Attendance
from models.job_posting import JobPosting
from models.candidate import Candidate
from models.ticket import Ticket
from utils.resume_matcher import calculate_match_score
from utils.pdf_extractor import extract_text_from_pdf
from utils.decorators import hr_required

def create_app():
    """Application factory for HR Portal."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize SQLAlchemy database instance
    db.init_app(app)

    # Initialize Flask-Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please sign in to access the HR Portal.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """User loader callback for Flask-Login."""
        return User.query.get(int(user_id))

    # Ensure database tables exist & seed default accounts
    with app.app_context():
        db.create_all()
        seed_users()

    # --- Authentication & Access Control Routes ---

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Sign in route for HR and Employee accounts."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash(f'Welcome back, {user.username}! Logged in as [{user.role.upper()}].', 'success')

                # Redirect based on role
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                if user.role == 'employee':
                    return redirect(url_for('my_profile'))
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        """Sign out user session."""
        logout_user()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('login'))

    @app.route('/access-denied')
    def access_denied():
        """Access denied page for unauthorized role access attempts."""
        return render_template('access_denied.html')

    @app.route('/my-profile')
    @login_required
    def my_profile():
        """Self-service profile page for employee users."""
        employee = current_user.employee if current_user.employee_id else None
        return render_template('my_profile.html', employee=employee)

    # --- Home & Dashboard Routes ---

    @app.route('/')
    @login_required
    def index():
        """Homepage welcome view."""
        if current_user.role == 'employee':
            employee = current_user.employee if current_user.employee_id else None
            employee_id = current_user.employee_id

            leave_stats = {
                'total': Leave.query.filter_by(employee_id=employee_id).count() if employee_id else 0,
                'pending': Leave.query.filter_by(employee_id=employee_id, status='Pending').count() if employee_id else 0,
                'approved': Leave.query.filter_by(employee_id=employee_id, status='Approved').count() if employee_id else 0,
                'rejected': Leave.query.filter_by(employee_id=employee_id, status='Rejected').count() if employee_id else 0,
            }

            attendance_stats = {
                'present': Attendance.query.filter_by(employee_id=employee_id, status='Present').count() if employee_id else 0,
                'late': Attendance.query.filter_by(employee_id=employee_id, status='Late').count() if employee_id else 0,
                'absent': Attendance.query.filter_by(employee_id=employee_id, status='Absent').count() if employee_id else 0,
            }

            ticket_stats = {
                'total': Ticket.query.filter_by(employee_id=employee_id).count() if employee_id else 0,
                'open': Ticket.query.filter_by(employee_id=employee_id, status='Open').count() if employee_id else 0,
                'resolved': Ticket.query.filter_by(employee_id=employee_id, status='Resolved').count() if employee_id else 0,
            }

            recent_leaves = Leave.query.filter_by(employee_id=employee_id).order_by(Leave.id.desc()).limit(3).all() if employee_id else []
            recent_tickets = Ticket.query.filter_by(employee_id=employee_id).order_by(Ticket.id.desc()).limit(3).all() if employee_id else []

            return render_template(
                'index_employee.html',
                employee=employee,
                leave_stats=leave_stats,
                attendance_stats=attendance_stats,
                ticket_stats=ticket_stats,
                recent_leaves=recent_leaves,
                recent_tickets=recent_tickets
            )

        employee_count = Employee.query.count()
        pending_leaves = Leave.query.filter_by(status='Pending').count()
        today_attendance = Attendance.query.filter_by(date=date.today()).count()
        open_jobs = JobPosting.query.count()
        open_tickets = Ticket.query.filter_by(status='Open').count()
        return render_template(
            'index.html',
            employee_count=employee_count,
            pending_leaves=pending_leaves,
            today_attendance=today_attendance,
            open_jobs=open_jobs,
            open_tickets=open_tickets
        )

    @app.route('/dashboard')
    @hr_required
    def dashboard():
        """Dashboard overview route summarizing key HR metrics and recent activity."""
        today = date.today()

        total_employees = Employee.query.count()
        pending_leaves_count = Leave.query.filter_by(status='Pending').count()

        today_attendance = {
            'present': Attendance.query.filter_by(date=today, status='Present').count(),
            'late': Attendance.query.filter_by(date=today, status='Late').count(),
            'absent': Attendance.query.filter_by(date=today, status='Absent').count()
        }

        recent_leaves = Leave.query.order_by(Leave.id.desc()).limit(5).all()
        recent_attendances = Attendance.query.order_by(Attendance.id.desc()).limit(5).all()

        return render_template(
            'dashboard.html',
            total_employees=total_employees,
            pending_leaves_count=pending_leaves_count,
            today_attendance=today_attendance,
            recent_leaves=recent_leaves,
            recent_attendances=recent_attendances,
            today_date=today.strftime('%Y-%m-%d')
        )

    # --- Employee Management Routes (HR Restricted) ---

    @app.route('/employees')
    @hr_required
    def list_employees():
        """List all employees in the directory."""
        employees = Employee.query.order_by(Employee.id.desc()).all()
        return render_template('employees/list.html', employees=employees)

    @app.route('/employees/add', methods=['GET', 'POST'])
    @hr_required
    def add_employee():
        """Form route to add a new employee record."""
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            department = request.form.get('department', '').strip()
            position = request.form.get('position', '').strip()
            join_date_str = request.form.get('join_date', '').strip()

            if not name or not email:
                flash('Name and Email are required fields.', 'danger')
                return render_template('employees/add.html', today_date=date.today().isoformat())

            if Employee.query.filter_by(email=email).first():
                flash(f'An employee with email "{email}" already exists.', 'danger')
                return render_template('employees/add.html', today_date=date.today().isoformat())

            try:
                join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date() if join_date_str else date.today()
            except ValueError:
                join_date = date.today()

            new_employee = Employee(
                name=name,
                email=email,
                department=department if department else None,
                position=position if position else None,
                join_date=join_date
            )

            db.session.add(new_employee)
            db.session.commit()

            flash(f'Employee "{name}" added successfully!', 'success')
            return redirect(url_for('list_employees'))

        return render_template('employees/add.html', today_date=date.today().isoformat())

    @app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
    @hr_required
    def edit_employee(id):
        """Form route to edit an existing employee record."""
        employee = Employee.query.get_or_404(id)

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            department = request.form.get('department', '').strip()
            position = request.form.get('position', '').strip()
            join_date_str = request.form.get('join_date', '').strip()

            if not name or not email:
                flash('Name and Email cannot be empty.', 'danger')
                return render_template('employees/edit.html', employee=employee)

            existing_email = Employee.query.filter(Employee.email == email, Employee.id != id).first()
            if existing_email:
                flash(f'The email "{email}" is already used by another employee.', 'danger')
                return render_template('employees/edit.html', employee=employee)

            employee.name = name
            employee.email = email
            employee.department = department if department else None
            employee.position = position if position else None

            if join_date_str:
                try:
                    employee.join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

            db.session.commit()
            flash(f'Employee "{name}" details updated successfully.', 'success')
            return redirect(url_for('list_employees'))

        return render_template('employees/edit.html', employee=employee)

    @app.route('/employees/delete/<int:id>', methods=['POST'])
    @hr_required
    def delete_employee(id):
        """Action route to delete an employee record."""
        employee = Employee.query.get_or_404(id)
        emp_name = employee.name
        db.session.delete(employee)
        db.session.commit()

        flash(f'Employee "{emp_name}" was successfully deleted.', 'warning')
        return redirect(url_for('list_employees'))

    # --- Leave Management Routes ---

    @app.route('/leave')
    @login_required
    def list_leaves():
        """Display leave requests list (all leaves for HR, own leaves for Employee)."""
        if current_user.role == 'hr':
            leaves = Leave.query.order_by(Leave.id.desc()).all()
        else:
            if current_user.employee_id:
                leaves = Leave.query.filter_by(employee_id=current_user.employee_id).order_by(Leave.id.desc()).all()
            else:
                leaves = []
        return render_template('leave/list.html', leaves=leaves)

    @app.route('/leave/apply', methods=['GET', 'POST'])
    @login_required
    def apply_leave():
        """Form route for submitting a leave request."""
        if current_user.role == 'hr':
            employees = Employee.query.order_by(Employee.name).all()
        else:
            employees = [current_user.employee] if current_user.employee else []

        if request.method == 'POST':
            employee_id_str = request.form.get('employee_id', '').strip()
            leave_type = request.form.get('leave_type', '').strip()
            start_date_str = request.form.get('start_date', '').strip()
            end_date_str = request.form.get('end_date', '').strip()
            reason = request.form.get('reason', '').strip()

            if not employee_id_str or not leave_type or not start_date_str or not end_date_str:
                flash('Please fill in all required fields.', 'danger')
                return render_template('leave/apply.html', employees=employees, today_date=date.today().isoformat())

            try:
                employee_id = int(employee_id_str)
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date or employee selection format.', 'danger')
                return render_template('leave/apply.html', employees=employees, today_date=date.today().isoformat())

            # Scope restriction: Employees can only submit leave for themselves
            if current_user.role == 'employee' and employee_id != current_user.employee_id:
                flash('Access Denied: You can only submit leave requests for yourself.', 'danger')
                return redirect(url_for('list_leaves'))

            if end_date < start_date:
                flash('End date cannot be before start date.', 'danger')
                return render_template('leave/apply.html', employees=employees, today_date=date.today().isoformat())

            employee = Employee.query.get(employee_id)
            if not employee:
                flash('Selected employee does not exist.', 'danger')
                return render_template('leave/apply.html', employees=employees, today_date=date.today().isoformat())

            leave_request = Leave(
                employee_id=employee_id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason if reason else None,
                status='Pending'
            )

            db.session.add(leave_request)
            db.session.commit()

            flash(f'Leave request for "{employee.name}" submitted successfully!', 'success')
            return redirect(url_for('list_leaves'))

        return render_template('leave/apply.html', employees=employees, today_date=date.today().isoformat())

    @app.route('/leave/approve/<int:id>', methods=['POST'])
    @hr_required
    def approve_leave(id):
        """Action route to approve a leave request (HR Restricted)."""
        leave_req = Leave.query.get_or_404(id)
        leave_req.status = 'Approved'
        db.session.commit()

        emp_name = leave_req.employee.name if leave_req.employee else f'Employee #{leave_req.employee_id}'
        flash(f'Leave request #{id} for "{emp_name}" has been Approved.', 'success')
        return redirect(url_for('list_leaves'))

    @app.route('/leave/reject/<int:id>', methods=['POST'])
    @hr_required
    def reject_leave(id):
        """Action route to reject a leave request (HR Restricted)."""
        leave_req = Leave.query.get_or_404(id)
        leave_req.status = 'Rejected'
        db.session.commit()

        emp_name = leave_req.employee.name if leave_req.employee else f'Employee #{leave_req.employee_id}'
        flash(f'Leave request #{id} for "{emp_name}" has been Rejected.', 'warning')
        return redirect(url_for('list_leaves'))

    # --- Attendance Management Routes ---

    @app.route('/attendance')
    @login_required
    def list_attendance():
        """Display attendance history (all records for HR, own attendance for Employee)."""
        if current_user.role == 'hr':
            employees = Employee.query.order_by(Employee.name).all()
            emp_id_param = request.args.get('employee_id', type=int)
            date_param_str = request.args.get('date', '').strip()

            query = Attendance.query
            if emp_id_param:
                query = query.filter_by(employee_id=emp_id_param)
            if date_param_str:
                try:
                    selected_date = datetime.strptime(date_param_str, '%Y-%m-%d').date()
                    query = query.filter_by(date=selected_date)
                except ValueError:
                    pass

            attendances = query.order_by(Attendance.date.desc(), Attendance.id.desc()).all()
            return render_template(
                'attendance/list.html',
                attendances=attendances,
                employees=employees,
                selected_employee_id=emp_id_param,
                selected_date=date_param_str
            )
        else:
            # Employee role: Filter to own attendance records
            if current_user.employee_id:
                attendances = Attendance.query.filter_by(employee_id=current_user.employee_id).order_by(Attendance.date.desc()).all()
            else:
                attendances = []
            return render_template(
                'attendance/list.html',
                attendances=attendances,
                employees=[],
                selected_employee_id=current_user.employee_id,
                selected_date=''
            )

    @app.route('/attendance/mark', methods=['GET', 'POST'])
    @hr_required
    def mark_attendance():
        """Route to mark or update an employee's attendance (HR Restricted)."""
        employees = Employee.query.order_by(Employee.name).all()

        if request.method == 'POST':
            employee_id_str = request.form.get('employee_id', '').strip()
            date_str = request.form.get('date', '').strip()
            status = request.form.get('status', '').strip()

            if not employee_id_str or not date_str or not status:
                flash('All fields are required to mark attendance.', 'danger')
                return render_template('attendance/mark.html', employees=employees, today_date=date.today().isoformat())

            try:
                employee_id = int(employee_id_str)
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date or employee selection format.', 'danger')
                return render_template('attendance/mark.html', employees=employees, today_date=date.today().isoformat())

            if status not in ['Present', 'Absent', 'Late']:
                flash('Invalid attendance status selected.', 'danger')
                return render_template('attendance/mark.html', employees=employees, today_date=date.today().isoformat())

            employee = Employee.query.get(employee_id)
            if not employee:
                flash('Selected employee does not exist.', 'danger')
                return render_template('attendance/mark.html', employees=employees, today_date=date.today().isoformat())

            existing_record = Attendance.query.filter_by(employee_id=employee_id, date=attendance_date).first()

            if existing_record:
                existing_record.status = status
                db.session.commit()
                flash(f'Attendance updated to "{status}" for {employee.name} on {attendance_date.strftime("%Y-%m-%d")}.', 'info')
            else:
                new_attendance = Attendance(
                    employee_id=employee_id,
                    date=attendance_date,
                    status=status
                )
                db.session.add(new_attendance)
                db.session.commit()
                flash(f'Attendance marked as "{status}" for {employee.name} on {attendance_date.strftime("%Y-%m-%d")}.', 'success')

            return redirect(url_for('list_attendance'))

        preselect_emp_id = request.args.get('emp_id', type=int)
        preselect_date = request.args.get('att_date', '')

        return render_template(
            'attendance/mark.html',
            employees=employees,
            today_date=date.today().isoformat(),
            preselect_emp_id=preselect_emp_id,
            preselect_date=preselect_date
        )

    # --- Recruitment & AI Resume Screening Routes (HR Restricted) ---

    @app.route('/recruitment')
    @hr_required
    def list_jobs():
        """List all active job postings."""
        jobs = JobPosting.query.order_by(JobPosting.id.desc()).all()
        return render_template('recruitment/jobs.html', jobs=jobs)

    @app.route('/recruitment/job/add', methods=['GET', 'POST'])
    @hr_required
    def add_job():
        """Form route to post a new job opening."""
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            department = request.form.get('department', '').strip()
            required_skills = request.form.get('required_skills', '').strip()
            description = request.form.get('description', '').strip()

            if not title or not description:
                flash('Job Title and Description are required fields.', 'danger')
                return render_template('recruitment/add_job.html')

            job = JobPosting(
                title=title,
                department=department if department else None,
                required_skills=required_skills if required_skills else None,
                description=description
            )

            db.session.add(job)
            db.session.commit()

            flash(f'Job posting "{title}" created successfully!', 'success')
            return redirect(url_for('list_jobs'))

        return render_template('recruitment/add_job.html')

    @app.route('/recruitment/job/<int:id>')
    @hr_required
    def job_details(id):
        """View details of a job posting along with AI candidate screening scores."""
        job = JobPosting.query.get_or_404(id)

        candidates_with_ai = []
        for cand in job.candidates:
            ai_result = calculate_match_score(
                resume_text=cand.resume_text,
                job_title=job.title,
                job_description=job.description,
                required_skills_str=job.required_skills
            )
            cand.match_analysis = ai_result
            candidates_with_ai.append(cand)

        candidates_sorted = sorted(candidates_with_ai, key=lambda c: c.match_analysis['score'], reverse=True)
        return render_template('recruitment/job_details.html', job=job, candidates=candidates_sorted)

    @app.route('/recruitment/job/<int:id>/matches')
    @hr_required
    def job_matches(id):
        """Dedicated results page showing all candidate applicants ranked by AI match score."""
        job = JobPosting.query.get_or_404(id)

        candidates_with_ai = []
        for cand in job.candidates:
            ai_result = calculate_match_score(
                resume_text=cand.resume_text,
                job_title=job.title,
                job_description=job.description,
                required_skills_str=job.required_skills
            )
            cand.match_analysis = ai_result
            candidates_with_ai.append(cand)

        candidates_sorted = sorted(candidates_with_ai, key=lambda c: c.match_analysis['score'], reverse=True)
        return render_template('recruitment/matches.html', job=job, candidates=candidates_sorted)

    @app.route('/recruitment/candidate/add', methods=['GET', 'POST'])
    @hr_required
    def add_candidate():
        """Form route to submit a candidate application via PDF resume upload."""
        jobs = JobPosting.query.order_by(JobPosting.title).all()

        if request.method == 'POST':
            job_id_str = request.form.get('applied_job_id', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            file = request.files.get('resume_file')

            if not job_id_str or not name or not email:
                flash('Job title, Candidate Name, and Email are required.', 'danger')
                preselect_job_id = int(job_id_str) if job_id_str.isdigit() else None
                return render_template('recruitment/add_candidate.html', jobs=jobs, preselect_job_id=preselect_job_id)

            if not file or file.filename == '':
                flash('Please select a PDF resume file to upload.', 'danger')
                preselect_job_id = int(job_id_str) if job_id_str.isdigit() else None
                return render_template('recruitment/add_candidate.html', jobs=jobs, preselect_job_id=preselect_job_id)

            if not file.filename.lower().endswith('.pdf'):
                flash('Invalid file format. Only PDF (.pdf) files are supported.', 'danger')
                preselect_job_id = int(job_id_str) if job_id_str.isdigit() else None
                return render_template('recruitment/add_candidate.html', jobs=jobs, preselect_job_id=preselect_job_id)

            try:
                job_id = int(job_id_str)
            except ValueError:
                flash('Invalid job selection.', 'danger')
                return render_template('recruitment/add_candidate.html', jobs=jobs)

            job = JobPosting.query.get(job_id)
            if not job:
                flash('Selected job posting does not exist.', 'danger')
                return render_template('recruitment/add_candidate.html', jobs=jobs)

            clean_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex[:8]}_{clean_filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            file.save(save_path)

            extracted_text, extract_error = extract_text_from_pdf(save_path)
            if extract_error:
                flash(f'PDF Warning: {extract_error}', 'warning')
                extracted_text = f"Resume PDF uploaded: {clean_filename}. (No extractable text found in PDF)"

            candidate = Candidate(
                name=name,
                email=email,
                resume_filename=unique_filename,
                resume_text=extracted_text,
                applied_job_id=job_id
            )

            db.session.add(candidate)
            db.session.commit()

            flash(f'PDF resume for "{name}" uploaded and screened successfully!', 'success')
            return redirect(url_for('job_matches', id=job_id))

        preselect_job_id = request.args.get('job_id', type=int)
        return render_template('recruitment/add_candidate.html', jobs=jobs, preselect_job_id=preselect_job_id)

    @app.route('/uploads/<path:filename>')
    @login_required
    def download_resume(filename):
        """Serve uploaded PDF resume files for viewing/downloading in the browser."""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # --- Support Ticket Routes ---

    @app.route('/support')
    @login_required
    def list_tickets():
        """Display support tickets list (all for HR, own tickets for Employee)."""
        if current_user.role == 'employee':
            if current_user.employee_id:
                tickets = Ticket.query.filter_by(employee_id=current_user.employee_id).order_by(Ticket.created_at.desc()).all()
            else:
                tickets = []
        else:
            tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
        return render_template('support/list.html', tickets=tickets)

    @app.route('/support/create', methods=['GET', 'POST'])
    @login_required
    def create_ticket():
        """Form route to submit a new support ticket."""
        if request.method == 'POST':
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()

            if not subject or not message:
                flash('Subject and message are required fields.', 'danger')
                return render_template('support/create.html')

            if current_user.role == 'employee' and not current_user.employee_id:
                flash('Your account is not linked to an employee profile.', 'danger')
                return redirect(url_for('list_tickets'))

            emp_id = current_user.employee_id if current_user.role == 'employee' else request.form.get('employee_id', type=int)
            if not emp_id and current_user.employee_id:
                emp_id = current_user.employee_id

            if not emp_id:
                flash('A valid employee association is required to submit a ticket.', 'danger')
                return redirect(url_for('list_tickets'))

            ticket = Ticket(
                employee_id=emp_id,
                subject=subject,
                message=message,
                status='Open'
            )

            db.session.add(ticket)
            db.session.commit()

            flash('Support ticket submitted successfully!', 'success')
            return redirect(url_for('list_tickets'))

        return render_template('support/create.html')

    @app.route('/support/resolve/<int:id>', methods=['POST'])
    @hr_required
    def resolve_ticket(id):
        """Action route for HR to resolve a support ticket with an optional reply."""
        ticket = Ticket.query.get_or_404(id)
        reply = request.form.get('reply', '').strip()

        ticket.status = 'Resolved'
        if reply:
            ticket.reply = reply

        db.session.commit()
        flash(f'Support ticket #{ticket.id} marked as Resolved.', 'success')
        return redirect(url_for('list_tickets'))

    return app

def seed_users():
    """Seed initial default HR Admin and Employee user accounts if empty."""
    if User.query.count() == 0:
        # 1. Seed HR Admin User Account
        hr_user = User(
            username='admin',
            email='hr@company.com',
            role='hr'
        )
        hr_user.set_password('admin123')
        db.session.add(hr_user)

        # 2. Seed Employee Profile & Linked User Account
        john_emp = Employee(
            name='John Doe',
            email='john.doe@company.com',
            department='Engineering',
            position='Software Engineer',
            join_date=date.today()
        )
        db.session.add(john_emp)
        db.session.commit()

        john_user = User(
            username='john',
            email='john.doe@company.com',
            role='employee',
            employee_id=john_emp.id
        )
        john_user.set_password('john123')
        db.session.add(john_user)
        db.session.commit()

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
