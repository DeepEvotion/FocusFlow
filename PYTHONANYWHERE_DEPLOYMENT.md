# 🚀 Развертывание FocusFlow на PythonAnywhere

Подробная инструкция по развертыванию проекта на бесплатном хостинге PythonAnywhere.

---

## 📋 Содержание

1. [Подготовка проекта](#1-подготовка-проекта)
2. [Регистрация на PythonAnywhere](#2-регистрация-на-pythonanywhere)
3. [Загрузка кода](#3-загрузка-кода)
4. [Настройка виртуального окружения](#4-настройка-виртуального-окружения)
5. [Настройка базы данных](#5-настройка-базы-данных)
6. [Настройка WSGI](#6-настройка-wsgi)
7. [Настройка статических файлов](#7-настройка-статических-файлов)
8. [Настройка переменных окружения](#8-настройка-переменных-окружения)
9. [Запуск приложения](#9-запуск-приложения)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Подготовка проекта

### ✅ Проект уже подготовлен!

В проекте созданы необходимые файлы:
- ✅ `wsgi.py` - конфигурация WSGI
- ✅ `requirements-pythonanywhere.txt` - зависимости для PythonAnywhere
- ✅ `.gitignore` - исключения для Git

### Проверьте структуру проекта:

```
FocusFlow/
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── config.py
│   ├── templates/
│   ├── static/
│   ├── uploads/
│   └── .env.example
├── wsgi.py
├── requirements-pythonanywhere.txt
└── README.md
```

---

## 2. Регистрация на PythonAnywhere

### 2.1 Создайте аккаунт

1. Перейдите на https://www.pythonanywhere.com/
2. Нажмите **"Start running Python online in less than a minute!"**
3. Выберите **"Create a Beginner account"** (бесплатно)
4. Заполните форму регистрации:
   - Username (запомните его!)
   - Email
   - Password
5. Подтвердите email

### 2.2 Ограничения бесплатного аккаунта

- ✅ 1 веб-приложение
- ✅ 512 МБ дискового пространства
- ✅ Домен: `your-username.pythonanywhere.com`
- ⚠️ Нет HTTPS для кастомных доменов
- ⚠️ Приложение "засыпает" через 3 месяца без активности

---

## 3. Загрузка кода

### Вариант A: Через Git (рекомендуется)

1. **Откройте Bash консоль**
   - Dashboard → Consoles → Bash

2. **Клонируйте репозиторий**
   ```bash
   git clone https://github.com/DeepEvotion/FocusFlow.git
   cd FocusFlow
   ```

3. **Проверьте файлы**
   ```bash
   ls -la
   ```

### Вариант B: Через загрузку файлов

1. **Откройте Files**
   - Dashboard → Files

2. **Создайте папку**
   - Нажмите "New directory"
   - Имя: `FocusFlow`

3. **Загрузите файлы**
   - Перейдите в папку `FocusFlow`
   - Нажмите "Upload a file"
   - Загрузите все файлы проекта

---

## 4. Настройка виртуального окружения

### 4.1 Откройте Bash консоль

Dashboard → Consoles → Bash

### 4.2 Создайте виртуальное окружение

```bash
# Перейдите в папку проекта
cd ~/FocusFlow

# Создайте виртуальное окружение
mkvirtualenv --python=/usr/bin/python3.10 focusflow-env

# Виртуальное окружение автоматически активируется
# Вы увидите (focusflow-env) в начале строки
```

### 4.3 Установите зависимости

```bash
# Убедитесь, что вы в папке проекта
cd ~/FocusFlow

# Установите зависимости
pip install -r requirements-pythonanywhere.txt

# Проверьте установку
pip list
```

### 4.4 Если возникли ошибки

```bash
# Обновите pip
pip install --upgrade pip

# Установите зависимости по одной
pip install Flask==2.3.3
pip install Flask-SQLAlchemy==3.0.5
pip install Flask-Login==0.6.2
pip install Flask-Bcrypt==1.0.1
pip install Flask-CORS==4.0.0
pip install Authlib==1.2.1
pip install requests==2.31.0
pip install python-dotenv==1.0.0
pip install mutagen==1.47.0
pip install Werkzeug==2.3.7
```

---

## 5. Настройка базы данных

### 5.1 Создайте файл .env

```bash
cd ~/FocusFlow/backend
nano .env
```

### 5.2 Добавьте конфигурацию

```env
# Сгенерируйте секретный ключ
SECRET_KEY=your-super-secret-key-here

# База данных (SQLite)
DATABASE_URL=sqlite:///focus_app.db

# OAuth (опционально)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
YANDEX_CLIENT_ID=your-yandex-client-id
YANDEX_CLIENT_SECRET=your-yandex-client-secret
```

**Сохраните**: `Ctrl+O`, `Enter`, `Ctrl+X`

### 5.3 Сгенерируйте SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Скопируйте результат и вставьте в `.env`

### 5.4 Инициализируйте базу данных

```bash
cd ~/FocusFlow/backend
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created!')"
```

Вы должны увидеть: `Database created!`

---

## 6. Настройка WSGI

### 6.1 Откройте Web tab

Dashboard → Web → Add a new web app

### 6.2 Создайте веб-приложение

1. Нажмите **"Add a new web app"**
2. Выберите **"Manual configuration"**
3. Выберите **"Python 3.10"**
4. Нажмите **"Next"**

### 6.3 Настройте WSGI файл

1. В разделе **"Code"** найдите **"WSGI configuration file"**
2. Нажмите на ссылку (например: `/var/www/your_username_pythonanywhere_com_wsgi.py`)
3. **Удалите всё содержимое** файла
4. Вставьте следующий код:

```python
import sys
import os

# Замените YOUR_USERNAME на ваше имя пользователя
path = '/home/YOUR_USERNAME/FocusFlow'
if path not in sys.path:
    sys.path.insert(0, path)

backend_path = os.path.join(path, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Активируйте виртуальное окружение
activate_this = '/home/YOUR_USERNAME/.virtualenvs/focusflow-env/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Импортируйте приложение
from app import app as application
```

5. **Замените `YOUR_USERNAME`** на ваше имя пользователя PythonAnywhere (2 раза!)
6. Нажмите **"Save"** (зеленая кнопка вверху)

### 6.4 Настройте виртуальное окружение

1. В разделе **"Virtualenv"** найдите поле **"Enter path to a virtualenv"**
2. Введите: `/home/YOUR_USERNAME/.virtualenvs/focusflow-env`
3. Замените `YOUR_USERNAME` на ваше имя
4. Нажмите галочку ✓

---

## 7. Настройка статических файлов

### 7.1 Настройте Static files

В разделе **"Static files"** добавьте:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/FocusFlow/backend/static/` |
| `/uploads/` | `/home/YOUR_USERNAME/FocusFlow/backend/uploads/` |

**Замените `YOUR_USERNAME`** на ваше имя!

### 7.2 Создайте необходимые папки

```bash
cd ~/FocusFlow/backend
mkdir -p uploads/music
mkdir -p uploads/avatars
mkdir -p instance
chmod 755 uploads
chmod 755 uploads/music
chmod 755 uploads/avatars
chmod 755 instance
```

---

## 8. Настройка переменных окружения

### 8.1 Обновите config.py

```bash
cd ~/FocusFlow/backend
nano config.py
```

Убедитесь, что есть:

```python
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'instance', 'focus_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    YANDEX_CLIENT_ID = os.environ.get('YANDEX_CLIENT_ID')
    YANDEX_CLIENT_SECRET = os.environ.get('YANDEX_CLIENT_SECRET')
```

---

## 9. Запуск приложения

### 9.1 Перезагрузите веб-приложение

1. Вернитесь на вкладку **Web**
2. Нажмите большую зеленую кнопку **"Reload your-username.pythonanywhere.com"**
3. Подождите 10-15 секунд

### 9.2 Откройте сайт

Перейдите на: `https://your-username.pythonanywhere.com`

### 9.3 Проверьте работу

- ✅ Главная страница загружается
- ✅ Можно зарегистрироваться
- ✅ Можно войти
- ✅ Dashboard работает

---

## 10. Troubleshooting

### Ошибка: "Something went wrong"

**Проверьте логи:**

1. Web tab → Log files
2. Откройте **Error log**
3. Найдите последнюю ошибку

**Частые проблемы:**

#### 1. ModuleNotFoundError

```bash
# Активируйте виртуальное окружение
workon focusflow-env

# Переустановите зависимости
cd ~/FocusFlow
pip install -r requirements-pythonanywhere.txt
```

#### 2. Database error

```bash
# Пересоздайте базу данных
cd ~/FocusFlow/backend
rm -f ../instance/focus_app.db
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### 3. Static files не загружаются

```bash
# Проверьте права доступа
cd ~/FocusFlow/backend
chmod -R 755 static
chmod -R 755 uploads
```

#### 4. WSGI ошибка

- Проверьте, что `YOUR_USERNAME` заменен на ваше имя
- Проверьте пути в WSGI файле
- Убедитесь, что виртуальное окружение активировано

### Просмотр логов в реальном времени

```bash
# Error log
tail -f /var/log/your-username.pythonanywhere.com.error.log

# Server log
tail -f /var/log/your-username.pythonanywhere.com.server.log
```

### Перезапуск приложения

```bash
# Через консоль
touch /var/www/your_username_pythonanywhere_com_wsgi.py
```

Или нажмите **"Reload"** на Web tab

---

## 📊 Проверка статуса

### Команды для проверки

```bash
# Проверка виртуального окружения
workon focusflow-env
which python
pip list

# Проверка файлов
ls -la ~/FocusFlow/
ls -la ~/FocusFlow/backend/

# Проверка базы данных
ls -la ~/FocusFlow/instance/

# Проверка прав доступа
ls -la ~/FocusFlow/backend/uploads/
```

---

## 🔄 Обновление приложения

### Если вы обновили код на GitHub:

```bash
# Перейдите в папку проекта
cd ~/FocusFlow

# Получите последние изменения
git pull origin main

# Активируйте виртуальное окружение
workon focusflow-env

# Обновите зависимости (если нужно)
pip install -r requirements-pythonanywhere.txt

# Перезагрузите приложение
touch /var/www/your_username_pythonanywhere_com_wsgi.py
```

Или нажмите **"Reload"** на Web tab

---

## 🎯 Оптимизация

### Увеличение производительности

1. **Включите gzip сжатие** (в config.py):
```python
COMPRESS_MIMETYPES = ['text/html', 'text/css', 'application/javascript']
COMPRESS_LEVEL = 6
```

2. **Настройте кэширование** статических файлов

3. **Оптимизируйте базу данных**:
```bash
cd ~/FocusFlow/backend
python3 -c "from app import app, db; app.app_context().push(); db.session.execute('VACUUM')"
```

---

## 📞 Поддержка

### Если ничего не помогло:

1. **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/
2. **GitHub Issues**: https://github.com/DeepEvotion/FocusFlow/issues
3. **Email**: support@focusflow.app

---

## ✅ Checklist развертывания

- [ ] Зарегистрировались на PythonAnywhere
- [ ] Клонировали репозиторий
- [ ] Создали виртуальное окружение
- [ ] Установили зависимости
- [ ] Создали файл .env
- [ ] Инициализировали базу данных
- [ ] Настроили WSGI файл
- [ ] Настроили статические файлы
- [ ] Настроили виртуальное окружение в Web tab
- [ ] Перезагрузили приложение
- [ ] Проверили работу сайта

---

<p align="center">
  <strong>🎉 Готово! Ваш сайт развернут на PythonAnywhere!</strong>
</p>

<p align="center">
  Ссылка: https://your-username.pythonanywhere.com
</p>
