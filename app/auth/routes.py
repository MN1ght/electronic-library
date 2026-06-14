from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from . import auth_bp
from ..models import db, User, Role


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books.index'))

    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(login=login).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('books.index'))

        flash('Невозможно аутентифицироваться с указанными логином и паролем', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('books.index'))

    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip() or None

        # Проверки
        if not all([login_val, password, last_name, first_name]):
            flash('Заполните все обязательные поля.', 'danger')
            return render_template('auth/register.html', form=request.form)

        if password != password2:
            flash('Пароли не совпадают.', 'danger')
            return render_template('auth/register.html', form=request.form)

        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов.', 'danger')
            return render_template('auth/register.html', form=request.form)

        if User.query.filter_by(login=login_val).first():
            flash('Пользователь с таким логином уже существует.', 'danger')
            return render_template('auth/register.html', form=request.form)

        try:
            user_role = Role.query.filter_by(name='Пользователь').first()
            user = User(
                login=login_val,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                role=user_role
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash('Регистрация прошла успешно! Добро пожаловать.', 'success')
            return redirect(url_for('books.index'))

        except Exception as e:
            db.session.rollback()
            flash('Ошибка при регистрации. Попробуйте ещё раз.', 'danger')

    return render_template('auth/register.html', form=request.form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    next_page = request.referrer or url_for('books.index')
    return redirect(next_page)
