# 🔌 API Examples - Примеры использования API

Этот документ содержит примеры использования REST API FocusFlow.

## 📋 Содержание

- [Аутентификация](#аутентификация)
- [Задачи](#задачи)
- [Плейлисты и музыка](#плейлисты-и-музыка)
- [Чаты и сообщения](#чаты-и-сообщения)
- [Фокус-сессии](#фокус-сессии)
- [Профиль пользователя](#профиль-пользователя)

---

## 🔐 Аутентификация

### Регистрация

```bash
curl -X POST https://your-username.pythonanywhere.com/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePassword123",
    "name": "John Doe"
  }'
```

**Ответ:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "johndoe"
  }
}
```

### Вход

```bash
curl -X POST https://your-username.pythonanywhere.com/api/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

**Ответ:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "johndoe"
  }
}
```

### Получение текущего пользователя

```bash
curl https://your-username.pythonanywhere.com/api/me \
  -b cookies.txt
```

**Ответ:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "name": "John Doe",
  "bio": "Productivity enthusiast",
  "avatar_url": "/uploads/avatars/abc123.jpg"
}
```

---

## ✅ Задачи

### Получить все задачи

```bash
curl https://your-username.pythonanywhere.com/api/tasks \
  -b cookies.txt
```

**Ответ:**
```json
[
  {
    "id": 1,
    "title": "Написать отчет",
    "description": "Квартальный отчет по продажам",
    "status": "in_progress",
    "priority": 2,
    "timer_minutes": 25,
    "break_minutes": 5,
    "sessions_count": 4,
    "focus_preset": "pomodoro",
    "ambient_sound": "rain",
    "playlist_id": 1,
    "created_at": "2024-02-18T10:00:00",
    "subtasks": [
      {
        "id": 1,
        "title": "Собрать данные",
        "is_completed": true,
        "order": 0
      },
      {
        "id": 2,
        "title": "Написать текст",
        "is_completed": false,
        "order": 1
      }
    ],
    "subtasks_completed": 1,
    "subtasks_total": 2
  }
]
```

### Создать задачу

```bash
curl -X POST https://your-username.pythonanywhere.com/api/tasks \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "title": "Изучить Python",
    "description": "Пройти курс по Flask",
    "priority": 1,
    "timer_minutes": 50,
    "break_minutes": 10,
    "sessions_count": 3,
    "focus_preset": "deep_work",
    "ambient_sound": "forest",
    "playlist_id": 2
  }'
```

**Ответ:**
```json
{
  "success": true,
  "id": 2
}
```

### Обновить задачу

```bash
curl -X PUT https://your-username.pythonanywhere.com/api/tasks/2 \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "status": "completed",
    "title": "Изучить Python (завершено)"
  }'
```

### Удалить задачу

```bash
curl -X DELETE https://your-username.pythonanywhere.com/api/tasks/2 \
  -b cookies.txt
```

### Создать подзадачу

```bash
curl -X POST https://your-username.pythonanywhere.com/api/tasks/1/subtasks \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "title": "Проверить грамматику"
  }'
```

---

## 🎵 Плейлисты и музыка

### Получить все плейлисты

```bash
curl https://your-username.pythonanywhere.com/api/playlists \
  -b cookies.txt
```

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Фокус",
    "description": "Музыка для концентрации",
    "tracks_count": 5
  }
]
```

### Создать плейлист

```bash
curl -X POST https://your-username.pythonanywhere.com/api/playlists \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Релакс",
    "description": "Спокойная музыка для отдыха"
  }'
```

### Получить треки плейлиста

```bash
curl https://your-username.pythonanywhere.com/api/playlists/1/tracks \
  -b cookies.txt
```

**Ответ:**
```json
[
  {
    "id": 1,
    "title": "Ambient Track 1",
    "artist": "Focus Music",
    "url": "/uploads/music/abc123.mp3",
    "duration": 180
  }
]
```

### Загрузить трек

```bash
curl -X POST https://your-username.pythonanywhere.com/api/playlists/1/tracks \
  -b cookies.txt \
  -F "file=@music.mp3"
```

### Загрузить несколько треков

```bash
curl -X POST https://your-username.pythonanywhere.com/api/playlists/1/tracks \
  -b cookies.txt \
  -F "files=@track1.mp3" \
  -F "files=@track2.mp3" \
  -F "files=@track3.mp3"
```

---

## 💬 Чаты и сообщения

### Получить все чаты

```bash
curl https://your-username.pythonanywhere.com/api/chats \
  -b cookies.txt
```

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Команда разработки",
    "is_group": true,
    "chat_type": "group",
    "avatar": null,
    "avatar_letter": "К",
    "members_count": 5,
    "last_message": {
      "content": "Привет всем!",
      "sender_id": 2,
      "created_at": "2024-02-18T15:30:00",
      "is_mine": false
    },
    "unread_count": 3
  }
]
```

### Создать личный чат

```bash
curl -X POST https://your-username.pythonanywhere.com/api/chats \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "user_id": 2,
    "chat_type": "private"
  }'
```

### Создать группу

```bash
curl -X POST https://your-username.pythonanywhere.com/api/chats \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Проект X",
    "description": "Обсуждение проекта",
    "chat_type": "group",
    "is_public": false,
    "member_ids": [2, 3, 4]
  }'
```

### Получить сообщения чата

```bash
curl https://your-username.pythonanywhere.com/api/chats/1/messages \
  -b cookies.txt
```

**Ответ:**
```json
{
  "messages": [
    {
      "id": 1,
      "content": "Привет!",
      "sender_id": 1,
      "sender_name": "John Doe",
      "sender_username": "johndoe",
      "sender_avatar": "/uploads/avatars/abc.jpg",
      "created_at": "2024-02-18T15:00:00",
      "edited_at": null,
      "is_read": true,
      "is_mine": true,
      "reply_to": null
    }
  ],
  "has_more": false,
  "total": 1
}
```

### Отправить сообщение

```bash
curl -X POST https://your-username.pythonanywhere.com/api/chats/1/messages \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "content": "Привет всем! 👋"
  }'
```

### Ответить на сообщение

```bash
curl -X POST https://your-username.pythonanywhere.com/api/chats/1/messages \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "content": "Согласен!",
    "reply_to_id": 5
  }'
```

---

## ⏱️ Фокус-сессии

### Начать сессию

```bash
curl -X POST https://your-username.pythonanywhere.com/api/focus/session/start \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "task_id": 1,
    "playlist_id": 1,
    "duration_minutes": 25
  }'
```

**Ответ:**
```json
{
  "success": true,
  "session_id": 1
}
```

### Завершить сессию

```bash
curl -X POST https://your-username.pythonanywhere.com/api/focus/session/1/end \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "completed": true,
    "distractions": 0
  }'
```

**Ответ:**
```json
{
  "success": true,
  "tree": {
    "level": 3,
    "experience": 150,
    "health": 95,
    "exp_gained": 50
  },
  "unlocked": [
    {
      "type": "sessions_10",
      "name": "Начинающий",
      "icon": "🌿"
    }
  ]
}
```

### Получить дерево концентрации

```bash
curl https://your-username.pythonanywhere.com/api/focus/tree \
  -b cookies.txt
```

**Ответ:**
```json
{
  "level": 3,
  "experience": 150,
  "exp_for_next_level": 300,
  "health": 95,
  "total_focus_minutes": 250,
  "total_sessions": 10,
  "streak_days": 5,
  "tree_type": "oak",
  "garden_level": 0,
  "garden_exp": 0,
  "health_changed": false
}
```

### Получить статистику

```bash
curl https://your-username.pythonanywhere.com/api/focus/stats \
  -b cookies.txt
```

**Ответ:**
```json
{
  "today": {
    "minutes": 75,
    "sessions": 3
  },
  "week": {
    "total_minutes": 350,
    "total_sessions": 14,
    "daily": {
      "2024-02-18": {"minutes": 75, "sessions": 3},
      "2024-02-17": {"minutes": 50, "sessions": 2}
    }
  },
  "all_time": {
    "total_minutes": 1250,
    "total_sessions": 50,
    "streak_days": 5
  }
}
```

---

## 👤 Профиль пользователя

### Обновить профиль

```bash
curl -X PUT https://your-username.pythonanywhere.com/api/profile/settings \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "John Doe Updated",
    "bio": "Productivity expert and developer",
    "privacy": {
      "last_seen": "everyone",
      "bio": "everyone",
      "avatar": "everyone",
      "playlists": "contacts"
    }
  }'
```

### Загрузить аватар

```bash
curl -X POST https://your-username.pythonanywhere.com/api/profile/avatar \
  -b cookies.txt \
  -F "file=@avatar.jpg"
```

**Ответ:**
```json
{
  "success": true,
  "avatar_url": "/uploads/avatars/xyz789.jpg"
}
```

### Поиск пользователей

```bash
curl "https://your-username.pythonanywhere.com/api/users/search?q=john" \
  -b cookies.txt
```

**Ответ:**
```json
[
  {
    "id": 2,
    "username": "johndoe",
    "name": "John Doe",
    "avatar_url": "/uploads/avatars/abc.jpg"
  }
]
```

---

## 🎮 Яндекс.Диск

### Проверить статус подключения

```bash
curl https://your-username.pythonanywhere.com/api/yandex/status \
  -b cookies.txt
```

**Ответ:**
```json
{
  "connected": true,
  "total_space": 10737418240,
  "used_space": 1073741824,
  "user": {
    "display_name": "John Doe"
  }
}
```

### Загрузить файл на Яндекс.Диск

```bash
curl -X POST https://your-username.pythonanywhere.com/api/yandex/upload \
  -b cookies.txt \
  -F "file=@music.mp3"
```

### Получить список файлов

```bash
curl "https://your-username.pythonanywhere.com/api/yandex/files?type=music" \
  -b cookies.txt
```

**Ответ:**
```json
[
  {
    "id": 1,
    "filename": "track.mp3",
    "title": "Ambient Music",
    "artist": "Focus Sounds",
    "duration": 180,
    "size": 5242880,
    "file_type": "music",
    "created_at": "2024-02-18T10:00:00"
  }
]
```

---

## 📊 Достижения

### Получить все достижения

```bash
curl https://your-username.pythonanywhere.com/api/achievements \
  -b cookies.txt
```

**Ответ:**
```json
{
  "achievements": [
    {
      "type": "first_session",
      "name": "Первый шаг",
      "icon": "🌱",
      "description": "Завершите первую сессию фокуса",
      "unlocked": true,
      "unlocked_at": "2024-02-15T10:00:00"
    },
    {
      "type": "sessions_10",
      "name": "Начинающий",
      "icon": "🌿",
      "description": "Завершите 10 сессий",
      "unlocked": true,
      "unlocked_at": "2024-02-18T15:00:00"
    }
  ],
  "unlocked_count": 2,
  "total_count": 20
}
```

---

## 🔧 Настройки фокусировки

### Получить настройки

```bash
curl https://your-username.pythonanywhere.com/api/focus/settings \
  -b cookies.txt
```

**Ответ:**
```json
{
  "work_duration": 25,
  "short_break": 5,
  "long_break": 15,
  "sessions_before_long_break": 4,
  "block_notifications": true,
  "fullscreen_mode": false,
  "ambient_sound": "rain",
  "ambient_volume": 50,
  "theme": "dark",
  "water_reminder": true,
  "water_interval": 30,
  "eye_reminder": true,
  "eye_interval": 20
}
```

### Обновить настройки

```bash
curl -X PUT https://your-username.pythonanywhere.com/api/focus/settings \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "work_duration": 50,
    "short_break": 10,
    "ambient_sound": "forest",
    "ambient_volume": 70
  }'
```

---

## 📝 Примечания

### Аутентификация
Все запросы (кроме `/api/register` и `/api/login`) требуют аутентификации через cookies.

### Формат даты
Все даты в формате ISO 8601: `YYYY-MM-DDTHH:MM:SS`

### Коды ответов
- `200` - Успех
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Не найдено
- `500` - Ошибка сервера

### Rate Limiting
На бесплатном плане PythonAnywhere есть ограничения на CPU time. Избегайте слишком частых запросов.

---

<p align="center">
  <strong>Больше примеров в документации API</strong><br>
  <a href="https://github.com/DeepEvotion/FocusFlow">GitHub Repository</a>
</p>
