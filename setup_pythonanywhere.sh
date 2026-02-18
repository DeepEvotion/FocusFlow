#!/bin/bash

# 🚀 Автоматическая настройка FocusFlow на PythonAnywhere
# Этот скрипт автоматизирует большинство шагов развертывания

set -e  # Остановка при ошибке

echo "🚀 FocusFlow - Автоматическая настройка для PythonAnywhere"
echo "============================================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Функция для вывода предупреждения
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Функция для вывода ошибки
error() {
    echo -e "${RED}✗${NC} $1"
}

# Проверка, что мы в правильной директории
if [ ! -f "wsgi.py" ]; then
    error "Ошибка: wsgi.py не найден. Убедитесь, что вы в корневой директории FocusFlow"
    exit 1
fi

success "Найдена корневая директория проекта"

# Шаг 1: Создание виртуального окружения
echo ""
echo "📦 Шаг 1: Создание виртуального окружения..."
if [ -d "$HOME/.virtualenvs/focusflow-env" ]; then
    warning "Виртуальное окружение уже существует, пропускаем"
else
    mkvirtualenv --python=/usr/bin/python3.10 focusflow-env
    success "Виртуальное окружение создано"
fi

# Активация виртуального окружения
source $HOME/.virtualenvs/focusflow-env/bin/activate

# Шаг 2: Установка зависимостей
echo ""
echo "📚 Шаг 2: Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements-pythonanywhere.txt
success "Зависимости установлены"

# Шаг 3: Настройка .env
echo ""
echo "🔧 Шаг 3: Настройка переменных окружения..."
cd backend

if [ -f ".env" ]; then
    warning ".env файл уже существует"
    read -p "Перезаписать? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        warning "Пропускаем создание .env"
        cd ..
    else
        cp .env.example .env
        success ".env файл создан"
        cd ..
    fi
else
    cp .env.example .env
    success ".env файл создан"
    cd ..
fi

# Генерация SECRET_KEY
echo ""
echo "🔑 Генерация SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "Ваш SECRET_KEY: $SECRET_KEY"
echo ""
warning "ВАЖНО: Сохраните этот ключ и добавьте его в backend/.env"
echo "Откройте файл: nano backend/.env"
echo "Замените 'your-secret-key-here' на сгенерированный ключ"
echo ""
read -p "Нажмите Enter после того, как добавите SECRET_KEY в .env..."

# Шаг 4: Создание необходимых директорий
echo ""
echo "📁 Шаг 4: Создание директорий..."
mkdir -p backend/uploads/music
mkdir -p backend/uploads/avatars
mkdir -p backend/uploads/chat_avatars
mkdir -p instance

chmod 755 backend/uploads
chmod 755 backend/uploads/music
chmod 755 backend/uploads/avatars
chmod 755 backend/uploads/chat_avatars
chmod 755 instance

success "Директории созданы"

# Шаг 5: Инициализация базы данных
echo ""
echo "🗄️  Шаг 5: Инициализация базы данных..."
cd backend

if [ -f "../instance/focus_app.db" ]; then
    warning "База данных уже существует"
    read -p "Пересоздать? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f ../instance/focus_app.db
        python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created!')"
        success "База данных пересоздана"
    else
        warning "Пропускаем инициализацию БД"
    fi
else
    python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created!')"
    success "База данных создана"
fi

cd ..

# Шаг 6: Получение username
echo ""
echo "👤 Шаг 6: Настройка WSGI..."
echo ""
echo "Для настройки WSGI нужно знать ваш username на PythonAnywhere"
read -p "Введите ваш username: " PA_USERNAME

if [ -z "$PA_USERNAME" ]; then
    error "Username не может быть пустым"
    exit 1
fi

# Создание настроенного WSGI файла
cat > wsgi_configured.py << EOF
"""
WSGI configuration for PythonAnywhere deployment
Configured for user: $PA_USERNAME
"""
import sys
import os

# Добавьте путь к вашему проекту
path = '/home/$PA_USERNAME/FocusFlow'
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
EOF

success "Создан настроенный WSGI файл: wsgi_configured.py"

# Шаг 7: Вывод инструкций для Web tab
echo ""
echo "============================================================"
echo "🎉 Автоматическая настройка завершена!"
echo "============================================================"
echo ""
echo "📋 Следующие шаги (выполните вручную в Web tab):"
echo ""
echo "1. Откройте Web tab на PythonAnywhere"
echo "2. Нажмите 'Add a new web app'"
echo "3. Выберите 'Manual configuration' → 'Python 3.10'"
echo ""
echo "4. В разделе 'Code' → 'WSGI configuration file':"
echo "   - Откройте файл"
echo "   - Удалите всё содержимое"
echo "   - Скопируйте содержимое из: ~/FocusFlow/wsgi_configured.py"
echo "   - Сохраните"
echo ""
echo "5. В разделе 'Virtualenv':"
echo "   Введите: /home/$PA_USERNAME/.virtualenvs/focusflow-env"
echo ""
echo "6. В разделе 'Static files' добавьте:"
echo "   URL: /static/"
echo "   Directory: /home/$PA_USERNAME/FocusFlow/backend/static/"
echo ""
echo "   URL: /uploads/"
echo "   Directory: /home/$PA_USERNAME/FocusFlow/backend/uploads/"
echo ""
echo "7. Нажмите зеленую кнопку 'Reload'"
echo ""
echo "============================================================"
echo ""
echo "📖 Полная документация: PYTHONANYWHERE_DEPLOYMENT.md"
echo "✅ Чеклист: DEPLOYMENT_CHECKLIST.md"
echo ""
echo "🌐 Ваш сайт будет доступен по адресу:"
echo "   https://$PA_USERNAME.pythonanywhere.com"
echo ""
success "Готово! Удачи! 🚀"
