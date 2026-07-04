import functools

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from ..forms import LoginForm

bp = Blueprint('auth', __name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login', next=request.path))
        return view(**kwargs)
    return wrapped_view


@bp.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password_hash = current_app.config['ADMIN_PASSWORD_HASH']
        if (form.username.data == current_app.config['ADMIN_USERNAME']
                and password_hash
                and check_password_hash(password_hash, form.password.data)):
            session.clear()
            session['logged_in'] = True
            next_page = request.args.get('next', '')
            # only follow same-site relative paths
            if not next_page.startswith('/') or next_page.startswith('//'):
                next_page = url_for('admin.dashboard')
            return redirect(next_page)
        flash('Invalid username or password.', 'error')
    return render_template('auth/login.html', form=form)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('public.index'))
