#!/usr/bin/env python3
"""
🔍 Скрипт проверки готовности FocusFlow к развертыванию на PythonAnywhere
"""

import os
import sys
from pathlib import Path

# Цвета для вывода
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def success(msg):
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")

def warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}")

def error(msg):
    print(f"{Colors.RED}✗{Colors.NC} {msg}")

def info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.NC} {msg}")

def check_file(filepath, description):
    """Проверка существования файла"""
    if Path(filepath).exists():
        success(f"{description}: {filepath}")
        return True
    else:
        error(f"{description} не найден: {filepath}")
        return False

def check_directory(dirpath, description):
    """Проверка существования директории"""
    if Path(dirpath).is_dir():
        success(f"{description}: {dirpath}")
        return True
    else:
        warning(f"{description} не найдена: {dirpath}")
        return False

def check_env_file():
    """Проверка .env файла"""
    env_path = Path("backend/.env")
    if not env_path.exists():
        error(".env файл не найден в backend/")
        info("Создайте его: cp backend/.env.example backend/.env")
        return False
    
    # Проверяем содержимое
    with open(env_path, 'r') as f:
        content = f.read()
    
    if 'your-secret-key-here' in content:
        warning(".env содержит дефолтный SECRET_KEY")
        info("Сгенерируйте новый: python3 -c \"import secrets; print(secrets.token_hex(32))\"")
        return False
    
    success(".env файл настроен")
    return True

def check_requirements():
    """Проверка файла зависимостей"""
    req_path = Path("requirements-pythonanywhere.txt")
    if not req_path.exists():
        error("requirements-pythonanywhere.txt не найден")
        return False
    
    with open(req_path, 'r') as f:
        lines = f.readlines()
    
    required_packages = ['Flask', 'SQLAlchemy', 'Flask-Login', 'Flask-Bcrypt']
    found_packages = []
    
    for line in lines:
        for pkg in required_packages:
            if pkg.lower() in line.lower():
                found_packages.append(pkg)
    
    if len(found_packages) == len(required_packages):
        success(f"requirements-pythonanywhere.txt содержит все необходимые пакеты")
        return True
    else:
        warning(f"Найдено {len(found_packages)}/{len(required_packages)} пакетов")
        return False

def check_wsgi():
    """Проверка WSGI файла"""
    wsgi_path = Path("wsgi.py")
    if not wsgi_path.exists():
        error("wsgi.py не найден")
        return False
    
    with open(wsgi_path, 'r') as f:
        content = f.read()
    
    if 'YOUR_USERNAME' in content:
        warning("wsgi.py содержит YOUR_USERNAME - нужно заменить на реальный username")
        info("Или используйте setup_pythonanywhere.sh для автоматической настройки")
        return False
    
    success("wsgi.py готов")
    return True

def check_database():
    """Проверка базы данных"""
    db_path = Path("instance/focus_app.db")
    if db_path.exists():
        success("База данных существует")
        return True
    else:
        warning("База данных не инициализирована")
        info("Создайте её: cd backend && python3 -c \"from app import app, db; app.app_context().push(); db.create_all()\"")
        return False

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        success(f"Python версия: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        error(f"Python версия {version.major}.{version.minor} не поддерживается")
        info("Требуется Python 3.10+")
        return False

def check_imports():
    """Проверка возможности импорта основных модулей"""
    try:
        sys.path.insert(0, 'backend')
        import flask
        success(f"Flask установлен (версия {flask.__version__})")
        return True
    except ImportError:
        error("Flask не установлен")
        info("Установите зависимости: pip install -r requirements-pythonanywhere.txt")
        return False

def main():
    print("=" * 60)
    print("🔍 Проверка готовности FocusFlow к развертыванию")
    print("=" * 60)
    print()
    
    checks = []
    
    # Проверка Python
    print("📌 Проверка окружения:")
    checks.append(check_python_version())
    checks.append(check_imports())
    print()
    
    # Проверка файлов конфигурации
    print("📌 Проверка файлов конфигурации:")
    checks.append(check_file("wsgi.py", "WSGI конфигурация"))
    checks.append(check_file("requirements-pythonanywhere.txt", "Зависимости"))
    checks.append(check_requirements())
    checks.append(check_env_file())
    print()
    
    # Проверка структуры проекта
    print("📌 Проверка структуры проекта:")
    checks.append(check_file("backend/app.py", "Основное приложение"))
    checks.append(check_file("backend/models.py", "Модели БД"))
    checks.append(check_file("backend/config.py", "Конфигурация"))
    checks.append(check_directory("backend/templates", "Шаблоны"))
    checks.append(check_directory("backend/static", "Статические файлы"))
    print()
    
    # Проверка директорий для загрузок
    print("📌 Проверка директорий для загрузок:")
    checks.append(check_directory("backend/uploads/music", "Музыка"))
    checks.append(check_directory("backend/uploads/avatars", "Аватары"))
    print()
    
    # Проверка базы данных
    print("📌 Проверка базы данных:")
    checks.append(check_database())
    print()
    
    # Проверка документации
    print("📌 Проверка документации:")
    checks.append(check_file("PYTHONANYWHERE_DEPLOYMENT.md", "Полное руководство"))
    checks.append(check_file("QUICKSTART_PYTHONANYWHERE.md", "Быстрый старт"))
    checks.append(check_file("DEPLOYMENT_CHECKLIST.md", "Чеклист"))
    print()
    
    # Итоги
    print("=" * 60)
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total) * 100
    
    print(f"Результат: {passed}/{total} проверок пройдено ({percentage:.1f}%)")
    print()
    
    if percentage == 100:
        success("🎉 Проект полностью готов к развертыванию!")
        print()
        info("Следующие шаги:")
        print("  1. Зарегистрируйтесь на https://www.pythonanywhere.com/")
        print("  2. Следуйте инструкции: QUICKSTART_PYTHONANYWHERE.md")
        print("  3. Или используйте автоматический скрипт: bash setup_pythonanywhere.sh")
    elif percentage >= 80:
        warning("⚠️  Проект почти готов, но есть несколько предупреждений")
        print()
        info("Исправьте предупреждения выше и запустите проверку снова")
    else:
        error("❌ Проект не готов к развертыванию")
        print()
        info("Исправьте ошибки выше и запустите проверку снова")
    
    print("=" * 60)
    
    return 0 if percentage == 100 else 1

if __name__ == "__main__":
    sys.exit(main())
