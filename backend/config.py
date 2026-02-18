import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///focus_app.db?timeout=30')
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
