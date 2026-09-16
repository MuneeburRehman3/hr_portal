import unittest
from app import create_app, db
from models.user import User
from models.employee import Employee
from models.ticket import Ticket
from models.leave import Leave
from models.attendance import Attendance

class EmployeeExperienceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_1_navbar_hiding(self):
        """Test HR-only links are completely absent from employee nav HTML."""
        self.login('john', 'john123')
        res = self.client.get('/')
        html = res.data.decode('utf-8')
        
        # Verify HR-only navbar text/links are not present in navbar
        self.assertNotIn('href="/recruitment"', html)
        self.assertNotIn('href="/dashboard"', html)
        self.assertNotIn('href="/employees"', html)
        
        # Verify employee nav links are present
        self.assertIn('My Profile', html)
        self.assertIn('My Leave', html)
        self.assertIn('My Attendance', html)
        self.assertIn('Support', html)

    def test_2_employee_homepage(self):
        """Test employee homepage shows profile summary, leave status, and attendance summary."""
        self.login('john', 'john123')
        res = self.client.get('/')
        html = res.data.decode('utf-8')

        self.assertIn('Employee Portal', html)
        self.assertIn('Welcome back, John Doe!', html)
        self.assertIn('Profile Summary', html)
        self.assertIn('Leave Requests', html)
        self.assertIn('Attendance Log', html)
        self.assertIn('Support Tickets', html)

    def test_3_attendance_view_only_for_employee(self):
        """Test employees cannot mark attendance and are blocked from /attendance/mark."""
        self.login('john', 'john123')
        
        # Accessing /attendance/mark as employee must redirect to access-denied
        res = self.client.get('/attendance/mark', follow_redirects=True)
        self.assertIn(b'Access Denied', res.data)

        # Checking /attendance view does not have "Mark Attendance" button
        res_list = self.client.get('/attendance')
        html = res_list.data.decode('utf-8')
        self.assertNotIn('href="/attendance/mark"', html)

    def test_4_support_ticket_workflow(self):
        """Test employee ticket creation, HR viewing, HR reply + resolve, and employee viewing HR reply."""
        # Step A: Employee john creates a ticket
        self.login('john', 'john123')
        res_create = self.client.post('/support/create', data=dict(
            subject='Laptop Charger Request',
            message='I need a replacement USB-C charger for my work laptop.'
        ), follow_redirects=True)
        self.assertIn(b'Support ticket submitted successfully!', res_create.data)

        # Step B: Employee views ticket history (Status is Open)
        res_emp_tickets = self.client.get('/support')
        html_emp = res_emp_tickets.data.decode('utf-8')
        self.assertIn('Laptop Charger Request', html_emp)
        self.assertIn('Open', html_emp)

        # Logout employee
        self.logout()

        # Step C: HR admin views ticket details (subject, message, employee name)
        self.login('admin', 'admin123')
        res_hr_tickets = self.client.get('/support')
        html_hr = res_hr_tickets.data.decode('utf-8')
        self.assertIn('Laptop Charger Request', html_hr)
        self.assertIn('John Doe', html_hr)
        self.assertIn('I need a replacement USB-C charger for my work laptop.', html_hr)

        with self.app.app_context():
            ticket = Ticket.query.filter_by(subject='Laptop Charger Request').order_by(Ticket.id.desc()).first()
            self.assertIsNotNone(ticket)
            ticket_id = ticket.id

        # Step D: HR types reply and clicks Resolve
        res_resolve = self.client.post(f'/support/resolve/{ticket_id}', data=dict(
            reply='Charger has been ordered and dispatched by IT.'
        ), follow_redirects=True)
        self.assertIn(b'marked as Resolved', res_resolve.data)

        # Step E: Logout HR & login back as employee john to view HR response
        self.logout()
        self.login('john', 'john123')
        res_resolved_view = self.client.get('/support')
        html_resolved = res_resolved_view.data.decode('utf-8')

        self.assertIn('Resolved', html_resolved)
        self.assertIn('HR Response & Resolution Notes:', html_resolved)
        self.assertIn('Charger has been ordered and dispatched by IT.', html_resolved)

if __name__ == '__main__':
    unittest.main()
