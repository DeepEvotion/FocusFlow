"""
WSGI configuration for PythonAnywhere deployment
"""
import sys
import os

# Добавьте путь к вашему проекту
path = '/home/YOUR_USERNAME/FocusFlow'
if path not in sys.path:
    sys.path.insert(0, path)

# Добавьте путь к backend
backend_path = os.path.join(path, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Устанавливаем рабочую директорию на backend
os.chdir(backend_path)

# Импортируйте приложение
from app import app as application

# Для совместимости
app = application
