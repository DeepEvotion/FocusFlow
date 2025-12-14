<p align="center">
  <img src="https://img.icons8.com/fluency/96/000000/focus.png" alt="FocusFlow Logo"/>
</p>

<h1 align="center">🚀 FocusFlow</h1>

<p align="center">
  <strong>Современное веб-приложение для продуктивности и управления временем</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-2.0+-green?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/SQLite-3-blue?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License"/>
</p>

<p align="center">
  <a href="#-возможности">Возможности</a> •
  <a href="#-быстрый-старт">Быстрый старт</a> •
  <a href="#-технологии">Технологии</a> •
  <a href="#-структура">Структура</a>
</p>

---

## ✨ Возможности

<table>
  <tr>
    <td align="center" width="33%">
      <img src="https://img.icons8.com/fluency/48/000000/task.png" alt="Tasks"/><br/>
      <strong>📋 Задачи</strong><br/>
      <sub>Создание задач с подзадачами, приоритетами и дедлайнами</sub>
    </td>
    <td align="center" width="33%">
      <img src="https://img.icons8.com/fluency/48/000000/timer.png" alt="Timer"/><br/>
      <strong>⏱️ Pomodoro</strong><br/>
      <sub>Таймер фокусировки с настраиваемыми интервалами</sub>
    </td>
    <td align="center" width="33%">
      <img src="https://img.icons8.com/fluency/48/000000/deciduous-tree.png" alt="Tree"/><br/>
      <strong>🌳 Дерево роста</strong><br/>
      <sub>Геймификация — выращивай дерево концентрации</sub>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/music.png" alt="Music"/><br/>
      <strong>🎵 Музыка</strong><br/>
      <sub>Плейлисты для работы и концентрации</sub>
    </td>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/chat.png" alt="Chat"/><br/>
      <strong>💬 Чаты</strong><br/>
      <sub>Личные и групповые сообщения</sub>
    </td>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/cloud.png" alt="Cloud"/><br/>
      <strong>☁️ Облако</strong><br/>
      <sub>Интеграция с Яндекс.Диском</sub>
    </td>
  </tr>
</table>

### Дополнительно

- 📝 **Заметки** — быстрые записи с цветовой маркировкой
- 📊 **Статистика** — отслеживание настроения и продуктивности  
- 🎮 **Мини-игры** — тренировка памяти в перерывах
- 🌙 **Темы** — тёмная и светлая тема интерфейса
- 🔐 **OAuth** — вход через Google и Яндекс

---

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- pip

### Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/focusflow.git
cd focusflow

# Создайте виртуальное окружение
python -m venv venv

# Активируйте его
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Установите зависимости
cd backend
pip install -r requirements.txt

# Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env — добавьте свои ключи OAuth

# Запустите приложение
python app.py
```

### 🌐 Откройте в браузере

```
http://127.0.0.1:5000
```

---

## 🛠️ Технологии

| Категория | Технологии |
|-----------|------------|
| **Backend** | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat&logo=python&logoColor=white) ![Flask](https://img.shields.io/badge/-Flask-000000?style=flat&logo=flask&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-red?style=flat) |
| **Frontend** | ![HTML5](https://img.shields.io/badge/-HTML5-E34F26?style=flat&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/-CSS3-1572B6?style=flat&logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/-JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black) |
| **Database** | ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat&logo=sqlite&logoColor=white) |
| **Auth** | ![Google](https://img.shields.io/badge/-Google_OAuth-4285F4?style=flat&logo=google&logoColor=white) ![Yandex](https://img.shields.io/badge/-Yandex_OAuth-FF0000?style=flat&logo=yandex&logoColor=white) |

---

## 📁 Структура проекта

```
focusflow/
├── 📂 backend/
│   ├── 📂 templates/        # HTML шаблоны
│   │   ├── index.html       # Главная страница
│   │   ├── auth.html        # Авторизация
│   │   ├── dashboard.html   # Основной интерфейс
│   │   └── ...
│   ├── 📂 uploads/          # Загруженные файлы
│   ├── 📄 app.py            # Основное приложение Flask
│   ├── 📄 models.py         # SQLAlchemy модели
│   ├── 📄 config.py         # Конфигурация
│   ├── 📄 yandex_disk.py    # API Яндекс.Диска
│   ├── 📄 migrate_db.py     # Миграции базы данных
│   ├── 📄 requirements.txt  # Python зависимости
│   └── 📄 .env.example      # Пример переменных окружения
├── 📄 .gitignore
└── 📄 README.md
```

---

## ⚙️ Конфигурация

Создайте файл `backend/.env`:

```env
SECRET_KEY=your-super-secret-key

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Yandex OAuth  
YANDEX_CLIENT_ID=your-yandex-client-id
YANDEX_CLIENT_SECRET=your-yandex-client-secret
```

<details>
<summary>📖 Как получить OAuth ключи</summary>

### Google OAuth
1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект
3. Включите Google+ API
4. Создайте OAuth 2.0 credentials
5. Добавьте redirect URI: `http://localhost:5000/auth/google/callback`

### Yandex OAuth
1. Перейдите на [Yandex OAuth](https://oauth.yandex.ru/)
2. Создайте приложение
3. Выберите права: `cloud_api:disk.read`, `cloud_api:disk.write`
4. Добавьте redirect URI: `http://localhost:5000/auth/yandex/callback`

</details>

---

## 📸 Скриншоты

<p align="center">
  <i>Скриншоты будут добавлены позже</i>
</p>

---

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

---

<p align="center">
  Сделано с ❤️ для хакатона
</p>
