import bleach
import markdown
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from . import reviews_bp
from ..models import db, Review, Book

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'pre', 'code', 'blockquote', 'ul', 'ol', 'li',
    'strong', 'em', 'del'
]

RATING_LABELS = {
    5: 'Отлично',
    4: 'Хорошо',
    3: 'Удовлетворительно',
    2: 'Неудовлетворительно',
    1: 'Плохо',
    0: 'Ужасно',
}


@reviews_bp.route('/books/<int:book_id>/reviews/new', methods=['GET', 'POST'])
@login_required
def new(book_id):
    book = Book.query.get_or_404(book_id)

    existing = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()
    if existing:
        flash('Вы уже оставляли рецензию на эту книгу.', 'warning')
        return redirect(url_for('books.show', book_id=book_id))

    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        text = bleach.clean(request.form.get('text', ''), tags=ALLOWED_TAGS, strip=True)

        if rating is None or not text.strip():
            flash('Заполните все поля.', 'danger')
            return render_template('reviews/new.html', book=book, rating_labels=RATING_LABELS)

        try:
            review = Review(
                book_id=book_id,
                user_id=current_user.id,
                rating=rating,
                text=text
            )
            db.session.add(review)
            db.session.commit()
            flash('Рецензия успешно добавлена!', 'success')
            return redirect(url_for('books.show', book_id=book_id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error saving review: {e}')
            flash('При сохранении данных возникла ошибка.', 'danger')

    return render_template('reviews/new.html', book=book, rating_labels=RATING_LABELS)


@reviews_bp.route('/my-reviews')
@login_required
def my_reviews():
    reviews = (Review.query
               .filter_by(user_id=current_user.id)
               .order_by(Review.created_at.desc())
               .all())
    return render_template('reviews/my_reviews.html', reviews=reviews, rating_labels=RATING_LABELS)
