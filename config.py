import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(__file__)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "library.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'covers')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
