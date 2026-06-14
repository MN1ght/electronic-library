import os
import hashlib
from flask import (render_template, redirect, url_for, flash,
                   request, current_app, abort)
from flask_login import login_required, current_user
import bleach
import markdown

from . import books_bp
from ..models import db, Book, Genre, Cover, Review

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'pre', 'code', 'blockquote', 'ul', 'ol', 'li', 'hr',
    'strong', 'em', 'del', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

PER_PAGE = 10


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Для выполнения данного действия необходимо пройти процедуру аутентификации', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_admin:
            flash('У вас недостаточно прав для выполнения данного действия', 'danger')
            return redirect(url_for('books.index'))
        return f(*args, **kwargs)
    return decorated


def admin_or_moderator_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Для выполнения данного действия необходимо пройти процедуру аутентификации', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if not (current_user.is_admin or current_user.is_moderator):
            flash('У вас недостаточно прав для выполнения данного действия', 'danger')
            return redirect(url_for('books.index'))
        return f(*args, **kwargs)
    return decorated


def save_cover(file, book_id):
    data = file.read()
    md5 = hashlib.md5(data).hexdigest()
    mime = file.mimetype

    existing = Cover.query.filter_by(md5_hash=md5).first()
    if existing:
        cover = Cover(filename=existing.filename, mime_type=mime, md5_hash=md5, book_id=book_id)
        db.session.add(cover)
        return cover

    cover = Cover(filename='', mime_type=mime, md5_hash=md5, book_id=book_id)
    db.session.add(cover)
    db.session.flush()

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
    filename = f'{cover.id}.{ext}'
    cover.filename = filename

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    with open(filepath, 'wb') as f:
        f.write(data)

    return cover


@books_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = (Book.query
                  .order_by(Book.year.desc())
                  .paginate(page=page, per_page=PER_PAGE, error_out=False))
    return render_template('index.html', pagination=pagination)


@books_bp.route('/books/<int:book_id>')
def show(book_id):
    book = Book.query.get_or_404(book_id)
    desc_html = bleach.clean(
        markdown.markdown(book.description, extensions=['extra', 'nl2br']),
        tags=ALLOWED_TAGS,
        strip=True
    )

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            book_id=book_id, user_id=current_user.id
        ).first()

    return render_template('books/show.html',
                           book=book,
                           desc_html=desc_html,
                           user_review=user_review)


@books_bp.route('/books/add', methods=['GET', 'POST'])
@admin_required
def add():
    genres = Genre.query.order_by(Genre.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = bleach.clean(request.form.get('description', ''), tags=ALLOWED_TAGS, strip=True)
        year = request.form.get('year', type=int)
        publisher = request.form.get('publisher', '').strip()
        author = request.form.get('author', '').strip()
        pages = request.form.get('pages', type=int)
        genre_ids = request.form.getlist('genre_ids', type=int)
        cover_file = request.files.get('cover')

        if not all([title, description, year, publisher, author, pages, genre_ids, cover_file]):
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
            return render_template('books/form.html', genres=genres, form_data=request.form, is_edit=False)

        try:
            book = Book(
                title=title,
                description=description,
                year=year,
                publisher=publisher,
                author=author,
                pages=pages
            )
            book.genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
            db.session.add(book)
            db.session.flush()

            save_cover(cover_file, book.id)
            db.session.commit()
            flash(f'Книга «{book.title}» успешно добавлена!', 'success')
            return redirect(url_for('books.show', book_id=book.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding book: {e}')
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')

    return render_template('books/form.html', genres=genres, form_data=request.form, is_edit=False)


@books_bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@admin_or_moderator_required
def edit(book_id):
    book = Book.query.get_or_404(book_id)
    genres = Genre.query.order_by(Genre.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = bleach.clean(request.form.get('description', ''), tags=ALLOWED_TAGS, strip=True)
        year = request.form.get('year', type=int)
        publisher = request.form.get('publisher', '').strip()
        author = request.form.get('author', '').strip()
        pages = request.form.get('pages', type=int)
        genre_ids = request.form.getlist('genre_ids', type=int)

        if not all([title, description, year, publisher, author, pages, genre_ids]):
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
            return render_template('books/form.html', genres=genres, form_data=request.form,
                                   book=book, is_edit=True)

        try:
            book.title = title
            book.description = description
            book.year = year
            book.publisher = publisher
            book.author = author
            book.pages = pages
            book.genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
            db.session.commit()
            flash(f'Книга «{book.title}» успешно обновлена!', 'success')
            return redirect(url_for('books.show', book_id=book.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error editing book: {e}')
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')

    return render_template('books/form.html', genres=genres, form_data=None, book=book, is_edit=True)


@books_bp.route('/books/<int:book_id>/delete', methods=['POST'])
@admin_required
def delete(book_id):
    book = Book.query.get_or_404(book_id)
    title = book.title

    try:
        if book.cover and book.cover.filename:
            same_file = Cover.query.filter_by(filename=book.cover.filename).count()
            if same_file <= 1:
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], book.cover.filename)
                if os.path.exists(filepath):
                    os.remove(filepath)

        db.session.delete(book)
        db.session.commit()
        flash(f'Книга «{title}» успешно удалена.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting book: {e}')
        flash('Ошибка при удалении книги.', 'danger')

    return redirect(url_for('books.index'))
