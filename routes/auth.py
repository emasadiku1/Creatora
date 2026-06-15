from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, CREATOR_ROLES
from models import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        email    = request.form['email'].strip().lower()
        role     = request.form['role']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('auth.register'))
        if role not in CREATOR_ROLES:
            flash('Invalid creator role.', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            email=email,
            role=role,
            password=generate_password_hash(password),
            display_name=request.form.get('display_name', '').strip(),
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome to Creatora, {user.username}!', 'success')
        return redirect(url_for('dashboard.home'))

    return render_template('auth/register.html', roles=CREATOR_ROLES)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'].strip().lower()).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.home'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('public.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        # Always show the same message to avoid user enumeration
        if not user or not user.security_question:
            flash('If that email exists and has a security question set, you can now answer it.', 'info')
            return redirect(url_for('auth.forgot_password'))
        return redirect(url_for('auth.reset_answer', email=email))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-answer', methods=['GET', 'POST'])
def reset_answer():
    email = request.args.get('email', '').strip().lower()
    user = User.query.filter_by(email=email).first_or_404()
    if not user.security_question:
        flash('No security question set for this account.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        answer = request.form.get('answer', '').strip().lower()
        new_password = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')

        if not check_password_hash(user.security_answer, answer):
            flash('Incorrect answer.', 'danger')
            return render_template('auth/reset_answer.html', user=user, email=email)
        if len(new_password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/reset_answer.html', user=user, email=email)
        if new_password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_answer.html', user=user, email=email)

        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_answer.html', user=user, email=email)