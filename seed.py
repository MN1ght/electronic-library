"""
Запускать ОДИН РАЗ после flask db upgrade:
    python seed.py
"""
from app import create_app
from app.models import db, Role, User, Genre

app = create_app()

with app.app_context():
    # Роли
    roles_data = [
        ('Администратор', 'Суперпользователь, полный доступ к системе'),
        ('Модератор', 'Может редактировать книги'),
        ('Пользователь', 'Может оставлять рецензии и создавать подборки'),
    ]
    for name, desc in roles_data:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, description=desc))
    db.session.commit()

    # Жанры
    genres = [
        'Фантастика', 'Фэнтези', 'Детектив', 'Роман', 'Классика',
        'Приключения', 'Ужасы', 'Научная литература', 'История', 'Биография',
    ]
    for g in genres:
        if not Genre.query.filter_by(name=g).first():
            db.session.add(Genre(name=g))
    db.session.commit()

    # Тестовые пользователи
    admin_role = Role.query.filter_by(name='Администратор').first()
    mod_role = Role.query.filter_by(name='Модератор').first()
    user_role = Role.query.filter_by(name='Пользователь').first()

    users_data = [
        ('admin', 'Admin123!', 'Иванов', 'Иван', 'Иванович', admin_role),
        ('moder', 'Moder123!', 'Петров', 'Пётр', None, mod_role),
        ('user1', 'User123!', 'Сидоров', 'Сидор', 'Сидорович', user_role),
    ]
    for login, pwd, last, first, middle, role in users_data:
        if not User.query.filter_by(login=login).first():
            u = User(login=login, last_name=last, first_name=first,
                     middle_name=middle, role=role)
            u.set_password(pwd)
            db.session.add(u)
    db.session.commit()

    print('База заполнена! Пользователи: admin/Admin123!, moder/Moder123!, user1/User123!')
