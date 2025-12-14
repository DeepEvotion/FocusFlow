from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Таблица связи пользователей (друзья)
friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

# Участники чата (устаревшая таблица, используется ChatMember)
chat_members = db.Table('chat_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('chat_id', db.Integer, db.ForeignKey('chats.id'), primary_key=True)
)


class ChatMember(db.Model):
    """Участники чата с ролями и настройками"""
    __tablename__ = 'chat_members_v2'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # owner, admin, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_muted = db.Column(db.Boolean, default=False)  # Уведомления отключены
    muted_until = db.Column(db.DateTime, nullable=True)  # Мут до определённого времени
    can_send_messages = db.Column(db.Boolean, default=True)  # Может отправлять сообщения
    can_send_media = db.Column(db.Boolean, default=True)  # Может отправлять медиа
    
    chat = db.relationship('Chat', backref=db.backref('members_v2', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('chat_memberships', lazy='dynamic'))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # None для Google OAuth
    name = db.Column(db.String(100), default='')
    bio = db.Column(db.Text, default='')
    avatar_url = db.Column(db.String(500), default='')
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)  # Онлайн-статус
    
    # Закреплённый плейлист (виден другим)
    pinned_playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id', use_alter=True), nullable=True)
    
    # Настройки конфиденциальности
    privacy_last_seen = db.Column(db.String(20), default='everyone')  # everyone, contacts, nobody
    privacy_bio = db.Column(db.String(20), default='everyone')
    privacy_avatar = db.Column(db.String(20), default='everyone')
    privacy_playlists = db.Column(db.String(20), default='everyone')
    
    # Связи
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    playlists = db.relationship('Playlist', backref='user', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='Playlist.user_id')
    notes = db.relationship('Note', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    pinned_playlist = db.relationship('Playlist', foreign_keys=[pinned_playlist_id], post_update=True)
    
    friends = db.relationship(
        'User', secondary=friendships,
        primaryjoin=(friendships.c.user_id == id),
        secondaryjoin=(friendships.c.friend_id == id),
        backref='friend_of'
    )


# Таблица блокировок
class BlockedUser(db.Model):
    __tablename__ = 'blocked_users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocked_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='blocked_users')
    blocked_user = db.relationship('User', foreign_keys=[blocked_user_id])


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    priority = db.Column(db.Integer, default=1)  # 1-3
    timer_minutes = db.Column(db.Integer, default=25)  # Время работы
    break_minutes = db.Column(db.Integer, default=5)  # Время перерыва
    sessions_count = db.Column(db.Integer, default=4)  # Количество сессий
    focus_preset = db.Column(db.String(20), default='pomodoro')  # pomodoro, deep, short, custom
    ambient_sound = db.Column(db.String(50), default='none')  # Фоновый звук
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)


class Playlist(db.Model):
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tracks = db.relationship('Track', backref='playlist', lazy='dynamic', cascade='all, delete-orphan')


class Track(db.Model):
    __tablename__ = 'tracks'
    
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), default='')
    url = db.Column(db.String(500), nullable=False)  # YouTube/Spotify URL
    duration = db.Column(db.Integer, default=0)  # секунды
    order = db.Column(db.Integer, default=0)


class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='')
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(20), default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)  # None для личных чатов
    description = db.Column(db.Text, default='')  # Описание группы/канала
    avatar_url = db.Column(db.String(500), default='')  # Аватар группы/канала
    
    # Тип чата
    chat_type = db.Column(db.String(20), default='private')  # private, group, channel
    is_group = db.Column(db.Boolean, default=False)  # Для обратной совместимости
    is_work_chat = db.Column(db.Boolean, default=False)  # Рабочий чат (исключение из режима фокуса)
    
    # Настройки группы/канала
    is_public = db.Column(db.Boolean, default=False)  # Публичный (можно найти в поиске)
    username = db.Column(db.String(50), unique=True, nullable=True)  # @username для публичных
    invite_link = db.Column(db.String(100), unique=True, nullable=True)  # Пригласительная ссылка
    
    # Права по умолчанию для участников
    members_can_send = db.Column(db.Boolean, default=True)  # Участники могут писать
    members_can_add = db.Column(db.Boolean, default=False)  # Участники могут добавлять людей
    members_can_pin = db.Column(db.Boolean, default=False)  # Участники могут закреплять
    slow_mode = db.Column(db.Integer, default=0)  # Медленный режим (секунды между сообщениями)
    
    # Владелец
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    members = db.relationship('User', secondary=chat_members, backref='chats')
    messages = db.relationship('Message', backref='chat', lazy='dynamic', cascade='all, delete-orphan')
    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_chats')


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime, nullable=True)  # Время редактирования
    is_read = db.Column(db.Boolean, default=False)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)  # Ответ на сообщение
    
    sender = db.relationship('User', backref='messages')
    reply_to = db.relationship('Message', remote_side=[id], backref='replies')


class FocusSession(db.Model):
    """Сессия фокусировки (работа с таймером)"""
    __tablename__ = 'focus_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    distractions = db.Column(db.Integer, default=0)  # Количество отвлечений
    tree_growth = db.Column(db.Integer, default=0)  # Рост дерева за сессию
    
    user = db.relationship('User', backref='focus_sessions')
    task = db.relationship('Task', backref='focus_sessions')
    playlist = db.relationship('Playlist', backref='focus_sessions')


class FocusTree(db.Model):
    """Дерево концентрации пользователя"""
    __tablename__ = 'focus_trees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    level = db.Column(db.Integer, default=1)  # Уровень дерева 1-10
    experience = db.Column(db.Integer, default=0)  # Опыт для роста
    health = db.Column(db.Integer, default=100)  # Здоровье 0-100
    total_focus_minutes = db.Column(db.Integer, default=0)  # Всего минут фокуса
    total_sessions = db.Column(db.Integer, default=0)  # Всего сессий
    streak_days = db.Column(db.Integer, default=0)  # Дней подряд
    last_session_date = db.Column(db.Date, nullable=True)  # Дата последней сессии
    tree_type = db.Column(db.String(20), default='oak')  # Тип дерева
    garden_level = db.Column(db.Integer, default=0)  # Уровень сада (растения вокруг дерева)
    garden_exp = db.Column(db.Integer, default=0)  # Опыт сада
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('focus_tree', uselist=False))


class FocusSettings(db.Model):
    """Настройки режима фокусировки"""
    __tablename__ = 'focus_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Pomodoro настройки
    work_duration = db.Column(db.Integer, default=25)  # Минуты работы
    short_break = db.Column(db.Integer, default=5)  # Короткий перерыв
    long_break = db.Column(db.Integer, default=15)  # Длинный перерыв
    sessions_before_long_break = db.Column(db.Integer, default=4)
    
    # Настройки блокировки
    block_notifications = db.Column(db.Boolean, default=True)
    fullscreen_mode = db.Column(db.Boolean, default=False)
    
    # Звуки
    ambient_sound = db.Column(db.String(50), default='none')  # rain, forest, waves, cafe, none
    ambient_volume = db.Column(db.Integer, default=50)  # 0-100
    
    # Настройки темы
    theme = db.Column(db.String(20), default='dark')  # dark, light
    
    # Напоминания о здоровье
    water_reminder = db.Column(db.Boolean, default=True)  # Напоминание о воде
    water_interval = db.Column(db.Integer, default=30)  # Интервал в минутах
    eye_reminder = db.Column(db.Boolean, default=True)  # Напоминание для глаз
    eye_interval = db.Column(db.Integer, default=20)  # Интервал в минутах (правило 20-20-20)
    
    user = db.relationship('User', backref=db.backref('focus_settings', uselist=False))


class Subtask(db.Model):
    """Подзадачи для задач"""
    __tablename__ = 'subtasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task = db.relationship('Task', backref=db.backref('subtasks', lazy='dynamic', cascade='all, delete-orphan'))


class MoodEntry(db.Model):
    """Журнал настроения"""
    __tablename__ = 'mood_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood = db.Column(db.Integer, nullable=False)  # 1-5 (очень плохо - отлично)
    energy = db.Column(db.Integer, default=3)  # 1-5 уровень энергии
    note = db.Column(db.Text, default='')  # Заметка о дне
    tags = db.Column(db.String(500), default='')  # Теги через запятую
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, default=datetime.utcnow)  # Дата записи
    
    user = db.relationship('User', backref=db.backref('mood_entries', lazy='dynamic'))


class TaskTemplate(db.Model):
    """Шаблоны задач/проектов"""
    __tablename__ = 'task_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    icon = db.Column(db.String(10), default='📋')  # Эмодзи иконка
    color = db.Column(db.String(20), default='primary')  # Цвет шаблона
    timer_minutes = db.Column(db.Integer, default=25)
    break_minutes = db.Column(db.Integer, default=5)
    sessions_count = db.Column(db.Integer, default=4)
    focus_preset = db.Column(db.String(20), default='pomodoro')
    ambient_sound = db.Column(db.String(50), default='none')
    subtasks_json = db.Column(db.Text, default='[]')  # JSON массив подзадач
    is_default = db.Column(db.Boolean, default=False)  # Системный шаблон
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('task_templates', lazy='dynamic'))


class TaskTimeLog(db.Model):
    """Детальный лог времени по задачам"""
    __tablename__ = 'task_time_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('focus_sessions.id'), nullable=True)
    minutes = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    hour = db.Column(db.Integer, default=0)  # Час дня (0-23) для почасовой статистики
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('time_logs', lazy='dynamic'))
    task = db.relationship('Task', backref=db.backref('time_logs', lazy='dynamic'))
    session = db.relationship('FocusSession', backref=db.backref('time_logs', lazy='dynamic'))


class Achievement(db.Model):
    """Достижения пользователя (геймификация)"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_type = db.Column(db.String(50), nullable=False)  # first_session, streak_7, etc.
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('achievements', lazy='dynamic'))


class GratitudeEntry(db.Model):
    """Журнал благодарности"""
    __tablename__ = 'gratitude_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)  # За что благодарен
    category = db.Column(db.String(50), default='general')  # work, health, relationships, etc.
    date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('gratitude_entries', lazy='dynamic'))


class MemoryGameScore(db.Model):
    """Результаты игр на память"""
    __tablename__ = 'memory_game_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)  # sequence, cards, numbers
    score = db.Column(db.Integer, nullable=False)
    level = db.Column(db.Integer, default=1)
    played_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('game_scores', lazy='dynamic'))


class YandexDiskToken(db.Model):
    """Токены Яндекс.Диска для пользователей"""
    __tablename__ = 'yandex_disk_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('yandex_token', uselist=False))


class CloudFile(db.Model):
    """Файлы пользователей на Яндекс.Диске"""
    __tablename__ = 'cloud_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Оригинальное имя файла
    cloud_path = db.Column(db.String(500), nullable=False)  # Путь на Яндекс.Диске
    file_type = db.Column(db.String(50), default='music')  # music, image, document
    size = db.Column(db.Integer, default=0)  # Размер в байтах
    mime_type = db.Column(db.String(100), default='')
    # Метаданные для музыки
    title = db.Column(db.String(255), default='')
    artist = db.Column(db.String(255), default='')
    duration = db.Column(db.Integer, default=0)  # Длительность в секундах
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('cloud_files', lazy='dynamic'))
