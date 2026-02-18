import os
from dotenv import load_dotenv

# Загружаем .env файл
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # База данных - используем абсолютный путь для instance
    instance_path = os.path.join(os.path.dirname(basedir), 'instance')
    default_db_path = f'sqlite:///{os.path.join(instance_path, "focus_app.db")}'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', default_db_path)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'timeout': 30}
    }
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/google/callback')
    
    # Yandex Disk OAuth
    YANDEX_CLIENT_ID = os.getenv('YANDEX_CLIENT_ID', '7cac02993e1f4543add1b5536baa9717')
    YANDEX_CLIENT_SECRET = os.getenv('YANDEX_CLIENT_SECRET', '4f462bd19e564442b8379f43911bdadb')
    YANDEX_REDIRECT_URI = os.getenv('YANDEX_REDIRECT_URI', 'http://localhost:5000/auth/yandex/callback')
