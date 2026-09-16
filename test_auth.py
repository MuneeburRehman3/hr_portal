import unittest
from app import create_app, db
from models.user import User
from models.employee import Employee
from models.leave import Leave
from models.attendance import Attendance

class AuthTestCase(unittest.TestCase):
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

    def test_seeded_users(self):
        with self.app.app_context():
            admin = User.query.filter_by(username='admin').first()
            john = User.query.filter_by(username='john').first()
            self.assertIsNotNone(admin)
            self.assertEqual(admin.role, 'hr')
            self.assertTrue(admin.check_password('admin123'))
            self.assertIsNotNone(john)
            self.assertEqual(john.role, 'employee')
            self.assertTrue(john.check_password('john123'))

    def test_hr_access(self):
        self.login('admin', 'admin123')
        # HR should access dashboard, employees, recruitment
        res_dash = self.client.get('/dashboard')
        self.assertEqual(res_dash.status_code, 200)
        res_emp = self.client.get('/employees')
        self.assertEqual(res_emp.status_code, 200)
        res_rec = self.client.get('/recruitment')
        self.assertEqual(res_rec.status_code, 200)

    def test_employee_restrictions(self):
        self.login('john', 'john123')
        # Employee attempting HR routes should redirect to access-denied (200 OK after follow_redirects)
        res_dash = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Access Denied', res_dash.data)

        res_emp = self.client.get('/employees', follow_redirects=True)
        self.assertIn(b'Access Denied', res_emp.data)

        res_rec = self.client.get('/recruitment', follow_redirects=True)
        self.assertIn(b'Access Denied', res_rec.data)

        # Employee can access my-profile, submit leave, attendance
        res_prof = self.client.get('/my-profile')
        self.assertEqual(res_prof.status_code, 200)

        res_leave = self.client.get('/leave')
        self.assertEqual(res_leave.status_code, 200)

        res_att = self.client.get('/attendance')
        self.assertEqual(res_att.status_code, 200)

if __name__ == '__main__':
    unittest.main()
