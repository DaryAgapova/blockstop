from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Добро пожаловать!', 'success')
            return redirect(next_page or url_for('main.index'))
        flash('Неверный email или пароль.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if not full_name or not email or not password:
            flash('Заполните все обязательные поля.', 'danger')
        elif password != password2:
            flash('Пароли не совпадают.', 'danger')
        elif len(password) < 6:
            flash('Пароль должен быть не менее 6 символов.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже зарегистрирован.', 'danger')
        else:
            user = User(full_name=full_name, email=email, phone=phone)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Аккаунт успешно создан!', 'success')
            return redirect(url_for('main.index'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('main.index'))
