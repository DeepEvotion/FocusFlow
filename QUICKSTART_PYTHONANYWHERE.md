# 🚀 Быстрый старт на PythonAnywhere

## Шаг 1: Клонируйте репозиторий
```bash
git clone https://github.com/DeepEvotion/FocusFlow.git
cd FocusFlow
```

## Шаг 2: Создайте виртуальное окружение
```bash
mkvirtualenv --python=/usr/bin/python3.10 focusflow-env
pip install -r requirements-pythonanywhere.txt
```

## Шаг 3: Настройте .env
```bash
cd backend
cp .env.example .env
nano .env
```

Сгенерируйте SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Шаг 4: Инициализируйте базу данных
```bash
cd ~/FocusFlow/backend
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created!')"
```

## Шаг 5: Настройте WSGI
В Web tab → WSGI configuration file замените `YOUR_USERNAME` на ваше имя пользователя (2 раза).

## Шаг 6: Настройте Static files
| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/FocusFlow/backend/static/` |
| `/uploads/` | `/home/YOUR_USERNAME/FocusFlow/backend/uploads/` |

## Шаг 7: Reload
Нажмите зеленую кнопку "Reload" на Web tab.

---

📖 **Полная инструкция**: [PYTHONANYWHERE_DEPLOYMENT.md](PYTHONANYWHERE_DEPLOYMENT.md)
