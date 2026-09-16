from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required

def hr_required(f):
    """
    Decorator restricting route access to users with the 'hr' role.
    Redirects employee users to access-denied view if attempted.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'hr':
            flash('Access Denied: HR privileges are required to access this resource.', 'danger')
            return redirect(url_for('access_denied'))
        return f(*args, **kwargs)
    return decorated_function
