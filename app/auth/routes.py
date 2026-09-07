"""
Routes autentikasi admin: login & logout.
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from ..models import AdminUser
from ..forms import LoginForm


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login admin."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login berhasil! Selamat datang.', 'success')

            # Redirect ke halaman yang diminta sebelumnya
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout admin."""
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('main.index'))
