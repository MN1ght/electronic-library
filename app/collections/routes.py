from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from . import collections_bp
from ..models import db, Collection, Book


@collections_bp.route('/collections')
@login_required
def index():
    collections = (Collection.query
                   .filter_by(user_id=current_user.id)
                   .order_by(Collection.name)
                   .all())
    return render_template('collections/index.html', collections=collections)


@collections_bp.route('/collections/add', methods=['POST'])
@login_required
def add():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Введите название подборки.', 'danger')
        return redirect(url_for('collections.index'))

    try:
        collection = Collection(name=name, user_id=current_user.id)
        db.session.add(collection)
        db.session.commit()
        flash(f'Подборка «{name}» успешно создана!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при создании подборки.', 'danger')

    return redirect(url_for('collections.index'))


@collections_bp.route('/collections/<int:collection_id>')
@login_required
def show(collection_id):
    collection = Collection.query.filter_by(
        id=collection_id, user_id=current_user.id
    ).first_or_404()
    return render_template('collections/show.html', collection=collection)


@collections_bp.route('/collections/add-book', methods=['POST'])
@login_required
def add_book():
    book_id = request.form.get('book_id', type=int)
    collection_id = request.form.get('collection_id', type=int)

    book = Book.query.get_or_404(book_id)
    collection = Collection.query.filter_by(
        id=collection_id, user_id=current_user.id
    ).first_or_404()

    if book in collection.books:
        flash(f'Книга «{book.title}» уже есть в этой подборке.', 'warning')
        return redirect(url_for('books.show', book_id=book_id))

    try:
        collection.books.append(book)
        db.session.commit()
        flash(f'Книга «{book.title}» добавлена в подборку «{collection.name}»!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при добавлении книги в подборку.', 'danger')

    return redirect(url_for('books.show', book_id=book_id))


@collections_bp.route('/collections/user-collections')
@login_required
def user_collections_json():
    """Возвращает подборки текущего пользователя для модалки."""
    collections = Collection.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in collections])
