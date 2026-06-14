from flask import Blueprint

collections_bp = Blueprint('collections', __name__)

from . import routes
