from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
from models import db, User, Task, Playlist, Track, Note, Chat, Message, FocusSession, BlockedUser, FocusTree, FocusSettings, Subtask, MoodEntry, TaskTemplate, TaskTimeLog, Achievement, GratitudeEntry, MemoryGameScore, YandexDiskToken, CloudFile
from config import Config
from datetime import datetime
from werkzeug.utils import secure_filename
from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from yandex_disk import YandexDiskAPI
import os
import uuid
import json
import tempfile

# Абсолютный путь к папке uploads относительно директории приложения
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'music')
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}

def extract_audio_metadata(filepath):
    """Извлекает метаданные из аудиофайла"""
    try:
        audio = MutagenFile(filepath, easy=True)
        if audio is None:
            return None, None, 0
        
        title = None
        artist = None
        duration = 0
        
        # Получаем длительность
        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            duration = int(audio.info.length)
        
        # Получаем теги
        if audio:
            title = audio.get('title', [None])[0]
            artist = audio.get('artist', [None])[0]
        
        return title, artist, duration
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None, None, 0

app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Создаём папку для загрузок
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Инициализация расширений
db.init_app(app)
CORS(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

# Google OAuth
oauth = OAuth(app)
if app.config['GOOGLE_CLIENT_ID']:
    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'openid email profile'},
        jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    )

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

# Создание таблиц
with app.app_context():
    db.create_all()

# ==================== СТРАНИЦЫ ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('dashboard'))
    return render_template('auth.html', mode='login', next_url=request.args.get('next', ''))

@app.route('/register')
def register_page():
    if current_user.is_authenticated:
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('dashboard'))
    return render_template('auth.html', mode='register', next_url=request.args.get('next', ''))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')

@app.route('/profile/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('public_profile.html', profile_user=user)

@app.route('/playlist/<int:user_id>/<int:playlist_id>')
def view_playlist(user_id, playlist_id):
    user = User.query.get_or_404(user_id)
    playlist = Playlist.query.get_or_404(playlist_id)
    return render_template('view_playlist.html', owner=user, playlist=playlist)

@app.route('/join/<invite_link>')
def join_chat_page(invite_link):
    """Страница присоединения к группе/каналу по ссылке"""
    chat = Chat.query.filter_by(invite_link=invite_link).first_or_404()
    
    if current_user.is_authenticated:
        # Если пользователь авторизован, присоединяем и редиректим
        if current_user not in chat.members:
            chat.members.append(current_user)
            from models import ChatMember
            member = ChatMember(chat_id=chat.id, user_id=current_user.id, role='member')
            db.session.add(member)
            db.session.commit()
        return redirect(url_for('dashboard') + f'#chat-{chat.id}')
    else:
        # Если не авторизован, показываем страницу с информацией о чате
        return render_template('join_chat.html', chat=chat, invite_link=invite_link)

# ==================== API: АВТОРИЗАЦИЯ ====================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email уже зарегистрирован'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username уже занят'}), 400
    
    password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    user = User(
        email=data['email'],
        username=data['username'],
        password_hash=password_hash,
        name=data.get('name', data['username'])
    )
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return jsonify({'success': True, 'user': {'id': user.id, 'username': user.username}})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.password_hash and bcrypt.check_password_hash(user.password_hash, data['password']):
        login_user(user)
        return jsonify({'success': True, 'user': {'id': user.id, 'username': user.username}})
    
    return jsonify({'error': 'Неверный email или пароль'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})

@app.route('/api/me')
@login_required
def get_current_user():
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'username': current_user.username,
        'name': current_user.name,
        'bio': current_user.bio,
        'avatar_url': current_user.avatar_url
    })

# Google OAuth
@app.route('/auth/google')
def google_login():
    if not app.config['GOOGLE_CLIENT_ID']:
        return jsonify({'error': 'Google OAuth не настроен'}), 400
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    
    user = User.query.filter_by(google_id=user_info['id']).first()
    
    if not user:
        user = User.query.filter_by(email=user_info['email']).first()
        if user:
            user.google_id = user_info['id']
        else:
            username = user_info['email'].split('@')[0]
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User(
                email=user_info['email'],
                username=username,
                name=user_info.get('name', username),
                google_id=user_info['id'],
                avatar_url=user_info.get('picture', '')
            )
            db.session.add(user)
    
    db.session.commit()
    login_user(user)
    return redirect(url_for('dashboard'))


# ==================== YANDEX DISK ====================

@app.route('/auth/yandex')
@login_required
def yandex_login():
    """Начать авторизацию Яндекс.Диска"""
    auth_url = YandexDiskAPI.get_auth_url(
        app.config['YANDEX_CLIENT_ID'],
        app.config['YANDEX_REDIRECT_URI']
    )
    return redirect(auth_url)


@app.route('/auth/yandex/callback')
@login_required
def yandex_callback():
    """Callback после авторизации Яндекс.Диска"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return redirect(url_for('dashboard') + '?yandex_error=' + error)
    
    if not code:
        return redirect(url_for('dashboard') + '?yandex_error=no_code')
    
    # Обмениваем код на токен
    token_data = YandexDiskAPI.exchange_code_for_token(
        code,
        app.config['YANDEX_CLIENT_ID'],
        app.config['YANDEX_CLIENT_SECRET']
    )
    
    if not token_data:
        return redirect(url_for('dashboard') + '?yandex_error=token_exchange_failed')
    
    # Сохраняем токен в БД
    yandex_token = YandexDiskToken.query.filter_by(user_id=current_user.id).first()
    if yandex_token:
        yandex_token.access_token = token_data['access_token']
        yandex_token.refresh_token = token_data.get('refresh_token')
        yandex_token.expires_at = token_data.get('expires_at')
    else:
        yandex_token = YandexDiskToken(
            user_id=current_user.id,
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            expires_at=token_data.get('expires_at')
        )
        db.session.add(yandex_token)
    
    db.session.commit()
    
    # Создаём папку приложения на диске
    yadisk = YandexDiskAPI(token_data['access_token'])
    yadisk.ensure_app_folder()
    
    return redirect(url_for('dashboard') + '?yandex_connected=1')


@app.route('/api/yandex/status')
@login_required
def yandex_status():
    """Проверить статус подключения Яндекс.Диска"""
    try:
        token = YandexDiskToken.query.filter_by(user_id=current_user.id).first()
        
        if not token:
            print("[YandexDisk] No token found for user", current_user.id)
            return jsonify({'connected': False})
        
        print(f"[YandexDisk] Token found, checking validity...")
        
        # Проверяем валидность токена
        yadisk = YandexDiskAPI(token.access_token)
        disk_info = yadisk.get_disk_info()
        
        print(f"[YandexDisk] Disk info response: {disk_info}")
        
        if disk_info:
            return jsonify({
                'connected': True,
                'total_space': disk_info.get('total_space', 0),
                'used_space': disk_info.get('used_space', 0),
                'user': disk_info.get('user', {})
            })
        
        return jsonify({'connected': False, 'error': 'invalid_token'})
    except Exception as e:
        print(f"[YandexDisk] Error checking status: {e}")
        return jsonify({'connected': False, 'error': str(e)})


@app.route('/api/yandex/disconnect', methods=['POST'])
@login_required
def yandex_disconnect():
    """Отключить Яндекс.Диск"""
    token = YandexDiskToken.query.filter_by(user_id=current_user.id).first()
    if token:
        db.session.delete(token)
        db.session.commit()
    return jsonify({'success': True})


@app.route('/api/yandex/upload', methods=['POST'])
@login_required
def yandex_upload():
    """Загрузить файл на Яндекс.Диск"""
    token = YandexDiskToken.query.filter_by(user_id=current_user.id).first()
    if not token:
        return jsonify({'error': 'Яндекс.Диск не подключен'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    # Определяем тип файла по расширению
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    
    music_exts = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac', 'wma'}
    image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}
    doc_exts = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf'}
    video_exts = {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'webm'}
    archive_exts = {'zip', 'rar', '7z', 'tar', 'gz'}
    
    if ext in music_exts:
        file_type = 'music'
    elif ext in image_exts:
        file_type = 'image'
    elif ext in doc_exts:
        file_type = 'document'
    elif ext in video_exts:
        file_type = 'video'
    elif ext in archive_exts:
        file_type = 'archive'
    else:
        file_type = 'other'
    
    # Генерируем уникальное имя
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    cloud_path = f"app:/FocusFlow/{file_type}/{unique_name}"
    
    # Сохраняем временно для извлечения метаданных
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, unique_name)
    file.save(temp_path)
    
    # Извлекаем метаданные для музыки
    title, artist, duration = None, None, 0
    if file_type == 'music':
        title, artist, duration = extract_audio_metadata(temp_path)
    
    # Загружаем на Яндекс.Диск
    yadisk = YandexDiskAPI(token.access_token)
    
    if not yadisk.upload_file(temp_path, cloud_path):
        os.remove(temp_path)
        return jsonify({'error': 'Ошибка загрузки на Яндекс.Диск'}), 500
    
    # Удаляем временный файл
    os.remove(temp_path)
    
    # Получаем размер файла
    file_info = yadisk.get_resource_info(cloud_path)
    file_size = file_info.get('size', 0) if file_info else 0
    
    # Сохраняем информацию в БД
    cloud_file = CloudFile(
        user_id=current_user.id,
        filename=filename,
        cloud_path=cloud_path,
        file_type=file_type,
        size=file_size,
        title=title or filename.rsplit('.', 1)[0],
        artist=artist or '',
        duration=duration
    )
    db.session.add(cloud_file)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'file': {
            'id': cloud_file.id,
            'filename': cloud_file.filename,
            'title': cloud_file.title,
            'artist': cloud_file.artist,
            'duration': cloud_file.duration,
            'size': cloud_file.size
        }
    })


@app.route('/api/yandex/files')
@login_required
def yandex_files():
    """Получить список файлов пользователя"""
    file_type = request.args.get('type', 'all')
    
    if file_type == 'all':
        files = CloudFile.query.filter_by(user_id=current_user.id).order_by(CloudFile.created_at.desc()).all()
    else:
        files = CloudFile.query.filter_by(user_id=current_user.id, file_type=file_type).order_by(CloudFile.created_at.desc()).all()
    
    return jsonify([{
        'id': f.id,
        'filename': f.filename,
        'title': f.title,
        'artist': f.artist,
        'duration': f.duration,
        'size': f.size,
        'file_type': f.file_type,
        'created_at': f.created_at.isoformat()
    } for f in files])


@app.route('/api/yandex/stream/<int:file_id>')
@login_required
def yandex_stream(file_id):
    """Получить ссылку для стриминга файла"""
    cloud_file = CloudFile.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not cloud_file:
        return jsonify({'error': 'Файл не найден'}), 404
    
    token = YandexDiskToken.query.filter_by(user_id=current_user.id).first()
    if not token:
        return jsonify({'error': 'Яндекс.Диск не подключен'}), 401
    
    yadisk = YandexDiskAPI(token.access_token)
    download_url = yadisk.get_download_url(cloud_file.cloud_path)
    
    if not download_url:
        return jsonify({'error': 'Не удалось получить ссылку'}), 500
    
    return jsonify({'url': download_url})


@app.route('/api/yandex/download/<int:file_id>')
@login_required
def yandex_download(file_id):
    """Скачать файл с Яндекс.Диска (проксирование)"""
    import requests
    from flask import Response
    
    cloud_file = CloudFile.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not cloud_file:
        return jsonify({'error': 'Файл не найден'}), 404
    
    token = YandexDiskToken.query.filter_by(user_id=current_user.id).first()
    if not token:
        return jsonify({'error': 'Яндекс.Диск не подключен'}), 401
    
    yadisk = YandexDiskAPI(token.access_token)
    download_url = yadisk.get_download_url(cloud_file.cloud_path)
    
    if not download_url:
        return jsonify({'error': 'Не удалось получить ссылку'}), 500
    
    # Скачиваем файл и отдаём пользователю
    response = requests.get(download_url, stream=True)
    
    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            yield chunk
    
    return Response(
        generate(),
        headers={
            'Content-Disposition': f'attachment; filename="{cloud_file.filename}"',
            'Content-Type': response.headers.get('Content-Type', 'application/octet-stream')
        }
    )


@app.route('/api/yandex/delete/<int:file_id>', methods=['DELETE'])
@login_required
def yandex_delete(file_id):
    """Удалить файл с Яндекс.Диска"""
    cloud_file = CloudFile.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not cloud_file:
        return jsonify({'error': 'Файл не найден'}), 404
    
    token = YandexDiskToken.query.filter_by(user_id=current_user.id).first()
    if not token:
        return jsonify({'error': 'Яндекс.Диск не подключен'}), 401
    
    yadisk = YandexDiskAPI(token.access_token)
    yadisk.delete_resource(cloud_file.cloud_path)
    
    db.session.delete(cloud_file)
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== API: ЗАДАЧИ ====================

@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    result = []
    for t in tasks:
        subtasks = Subtask.query.filter_by(task_id=t.id).order_by(Subtask.order).all()
        result.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'timer_minutes': t.timer_minutes,
            'break_minutes': getattr(t, 'break_minutes', 5),
            'sessions_count': getattr(t, 'sessions_count', 4),
            'focus_preset': getattr(t, 'focus_preset', 'pomodoro'),
            'ambient_sound': getattr(t, 'ambient_sound', 'none'),
            'playlist_id': t.playlist_id,
            'created_at': t.created_at.isoformat(),
            'subtasks': [{
                'id': s.id,
                'title': s.title,
                'is_completed': s.is_completed,
                'order': s.order
            } for s in subtasks],
            'subtasks_completed': sum(1 for s in subtasks if s.is_completed),
            'subtasks_total': len(subtasks)
        })
    return jsonify(result)

@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.json
    
    # Защита от дублирования: проверяем, не создавалась ли задача с таким же названием в последние 5 секунд
    from datetime import timedelta
    title = data.get('title', '')
    five_seconds_ago = datetime.utcnow() - timedelta(seconds=5)
    recent_duplicate = Task.query.filter(
        Task.user_id == current_user.id,
        Task.title == title,
        Task.created_at >= five_seconds_ago
    ).first()
    
    if recent_duplicate:
        return jsonify({'success': True, 'id': recent_duplicate.id, 'duplicate': True})
    
    # Обработка playlist_id
    playlist_id = data.get('playlist_id')
    if playlist_id == '' or playlist_id is None:
        playlist_id = None
    else:
        playlist_id = int(playlist_id) if playlist_id else None
    
    task = Task(
        user_id=current_user.id,
        title=title,
        description=data.get('description', ''),
        priority=data.get('priority', 1),
        timer_minutes=int(data.get('timer_minutes', 25)),
        break_minutes=int(data.get('break_minutes', 5)),
        sessions_count=int(data.get('sessions_count', 4)),
        focus_preset=data.get('focus_preset', 'pomodoro'),
        ambient_sound=data.get('ambient_sound', 'none'),
        playlist_id=playlist_id
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'success': True, 'id': task.id})

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    data = request.json
    
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.status = data.get('status', task.status)
    task.priority = data.get('priority', task.priority)
    task.timer_minutes = data.get('timer_minutes', task.timer_minutes)
    
    if task.status == 'completed' and not task.completed_at:
        task.completed_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})


# ==================== API: ПОДЗАДАЧИ ====================

@app.route('/api/tasks/<int:task_id>/subtasks', methods=['GET'])
@login_required
def get_subtasks(task_id):
    """Получить подзадачи задачи"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    subtasks = Subtask.query.filter_by(task_id=task_id).order_by(Subtask.order).all()
    return jsonify([{
        'id': s.id,
        'title': s.title,
        'is_completed': s.is_completed,
        'order': s.order
    } for s in subtasks])


@app.route('/api/tasks/<int:task_id>/subtasks', methods=['POST'])
@login_required
def create_subtask(task_id):
    """Создать подзадачу"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    data = request.json
    
    # Получаем максимальный order
    max_order = db.session.query(db.func.max(Subtask.order)).filter_by(task_id=task_id).scalar() or 0
    
    subtask = Subtask(
        task_id=task_id,
        title=data['title'],
        order=max_order + 1
    )
    db.session.add(subtask)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'id': subtask.id,
        'title': subtask.title,
        'is_completed': subtask.is_completed,
        'order': subtask.order
    })


@app.route('/api/subtasks/<int:subtask_id>', methods=['PUT'])
@login_required
def update_subtask(subtask_id):
    """Обновить подзадачу"""
    subtask = Subtask.query.get_or_404(subtask_id)
    task = Task.query.filter_by(id=subtask.task_id, user_id=current_user.id).first_or_404()
    
    data = request.json
    if 'title' in data:
        subtask.title = data['title']
    if 'is_completed' in data:
        subtask.is_completed = data['is_completed']
    if 'order' in data:
        subtask.order = data['order']
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/subtasks/<int:subtask_id>', methods=['DELETE'])
@login_required
def delete_subtask(subtask_id):
    """Удалить подзадачу"""
    subtask = Subtask.query.get_or_404(subtask_id)
    task = Task.query.filter_by(id=subtask.task_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(subtask)
    db.session.commit()
    return jsonify({'success': True})


# ==================== API: ПЛЕЙЛИСТЫ ====================

@app.route('/api/playlists', methods=['GET'])
@login_required
def get_playlists():
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'tracks_count': p.tracks.count()
    } for p in playlists])

@app.route('/api/playlists', methods=['POST'])
@login_required
def create_playlist():
    data = request.json
    playlist = Playlist(
        user_id=current_user.id,
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(playlist)
    db.session.commit()
    return jsonify({'success': True, 'id': playlist.id})

@app.route('/api/playlists/<int:playlist_id>/tracks', methods=['GET'])
@login_required
def get_playlist_tracks(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
    tracks = Track.query.filter_by(playlist_id=playlist_id).order_by(Track.order).all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'artist': t.artist,
        'url': t.url,
        'duration': t.duration
    } for t in tracks])

@app.route('/api/playlists/<int:playlist_id>/tracks', methods=['POST'])
@login_required
def add_track(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
    
    # Поддержка множественной загрузки файлов
    files = request.files.getlist('files') or request.files.getlist('file')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Файлы не выбраны'}), 400
    
    added_tracks = []
    errors = []
    max_order = db.session.query(db.func.max(Track.order)).filter_by(playlist_id=playlist_id).scalar() or 0
    
    for file in files:
        if file.filename == '':
            continue
            
        if not allowed_file(file.filename):
            errors.append(f'{file.filename}: недопустимый формат')
            continue
        
        # Генерируем уникальное имя файла
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Извлекаем метаданные из файла
        meta_title, meta_artist, duration = extract_audio_metadata(filepath)
        
        # Для множественной загрузки используем метаданные или имя файла
        title = meta_title or file.filename.rsplit('.', 1)[0]
        artist = meta_artist or 'Неизвестный исполнитель'
        
        max_order += 1
        track = Track(
            playlist_id=playlist_id,
            title=title,
            artist=artist,
            url=f'/uploads/music/{filename}',
            duration=duration,
            order=max_order
        )
        db.session.add(track)
        added_tracks.append({'id': None, 'title': title, 'artist': artist})
    
    db.session.commit()
    
    # Обновляем ID после коммита
    for i, track_data in enumerate(added_tracks):
        track_data['id'] = Track.query.filter_by(playlist_id=playlist_id, order=max_order - len(added_tracks) + i + 1).first().id
    
    return jsonify({
        'success': True,
        'tracks': added_tracks,
        'errors': errors,
        'added_count': len(added_tracks)
    })

# Отдача загруженных файлов
@app.route('/uploads/music/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/playlists/<int:playlist_id>/tracks/from-cloud', methods=['POST'])
@login_required
def add_tracks_from_cloud(playlist_id):
    """Добавить треки из Яндекс.Диска в плейлист"""
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    
    if not file_ids:
        return jsonify({'error': 'Не выбраны файлы'}), 400
    
    # Проверяем подключение Яндекс.Диска
    token = YandexDiskToken.query.filter_by(user_id=current_user.id).first()
    if not token:
        return jsonify({'error': 'Яндекс.Диск не подключен'}), 401
    
    added_count = 0
    max_order = db.session.query(db.func.max(Track.order)).filter_by(playlist_id=playlist_id).scalar() or 0
    
    for file_id in file_ids:
        cloud_file = CloudFile.query.filter_by(id=file_id, user_id=current_user.id).first()
        if not cloud_file:
            continue
        
        max_order += 1
        
        # Создаём трек с ссылкой на облачный файл
        track = Track(
            playlist_id=playlist_id,
            title=cloud_file.title or cloud_file.filename,
            artist=cloud_file.artist or 'Неизвестный исполнитель',
            url=f'cloud:{cloud_file.id}',  # Специальный формат для облачных файлов
            duration=cloud_file.duration or 0,
            order=max_order
        )
        db.session.add(track)
        added_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'added': added_count
    })

@app.route('/api/tracks/<int:track_id>', methods=['PUT'])
@login_required
def update_track(track_id):
    track = Track.query.get_or_404(track_id)
    playlist = Playlist.query.filter_by(id=track.playlist_id, user_id=current_user.id).first_or_404()
    
    data = request.json
    if 'title' in data:
        track.title = data['title']
    if 'artist' in data:
        track.artist = data['artist']
    
    db.session.commit()
    return jsonify({'success': True, 'track': {
        'id': track.id,
        'title': track.title,
        'artist': track.artist
    }})

@app.route('/api/tracks/<int:track_id>', methods=['DELETE'])
@login_required
def delete_track(track_id):
    track = Track.query.get_or_404(track_id)
    playlist = Playlist.query.filter_by(id=track.playlist_id, user_id=current_user.id).first_or_404()
    
    # Удаляем файл
    if track.url and track.url.startswith('/uploads/music/'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], track.url.split('/')[-1])
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.delete(track)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
    Track.query.filter_by(playlist_id=playlist_id).delete()
    db.session.delete(playlist)
    db.session.commit()
    return jsonify({'success': True})

# ==================== API: ЗАМЕТКИ ====================

@app.route('/api/notes', methods=['GET'])
@login_required
def get_notes():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'content': n.content,
        'is_pinned': n.is_pinned,
        'color': n.color,
        'updated_at': n.updated_at.isoformat()
    } for n in notes])

@app.route('/api/notes', methods=['POST'])
@login_required
def create_note():
    data = request.json
    note = Note(
        user_id=current_user.id,
        title=data.get('title', ''),
        content=data['content'],
        color=data.get('color', 'default')
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({'success': True, 'id': note.id})

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    data = request.json
    
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.is_pinned = data.get('is_pinned', note.is_pinned)
    note.color = data.get('color', note.color)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    return jsonify({'success': True})

# ==================== API: ПРОФИЛЬ ====================

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.json
    
    if 'username' in data and data['username'] != current_user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username уже занят'}), 400
        current_user.username = data['username']
    
    current_user.name = data.get('name', current_user.name)
    current_user.bio = data.get('bio', current_user.bio)
    current_user.avatar_url = data.get('avatar_url', current_user.avatar_url)
    
    db.session.commit()
    return jsonify({'success': True})

# ==================== API: ФОКУС СЕССИЯ ====================

@app.route('/api/focus/start', methods=['POST'])
@login_required
def start_focus():
    data = request.json
    session = FocusSession(
        user_id=current_user.id,
        task_id=data.get('task_id'),
        playlist_id=data.get('playlist_id'),
        duration_minutes=data['duration_minutes']
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({'success': True, 'session_id': session.id})

@app.route('/api/focus/<int:session_id>/end', methods=['POST'])
@login_required
def end_focus(session_id):
    focus = FocusSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    focus.ended_at = datetime.utcnow()
    focus.is_completed = request.json.get('completed', False)
    db.session.commit()
    return jsonify({'success': True})

# ==================== API: ПОИСК ПОЛЬЗОВАТЕЛЕЙ ====================

@app.route('/api/users/search')
@login_required
def search_users():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
        (User.username.ilike(f'%{query}%')) | (User.name.ilike(f'%{query}%'))
    ).filter(User.id != current_user.id).limit(10).all()
    
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'name': u.name,
        'avatar_url': u.avatar_url
    } for u in users])

# ==================== API: ЧАТЫ ====================

@app.route('/api/chats', methods=['GET'])
@login_required
def get_chats():
    """Получить все чаты пользователя"""
    chats = Chat.query.filter(Chat.members.any(id=current_user.id)).all()
    result = []
    
    for chat in chats:
        # Получаем последнее сообщение
        last_message = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at.desc()).first()
        
        # Считаем непрочитанные
        unread_count = Message.query.filter(
            Message.chat_id == chat.id,
            Message.sender_id != current_user.id,
            Message.is_read == False
        ).count()
        
        # Для личных чатов получаем собеседника
        other_user = None
        if not chat.is_group:
            for member in chat.members:
                if member.id != current_user.id:
                    other_user = member
                    break
        
        result.append({
            'id': chat.id,
            'name': chat.name if chat.is_group else (other_user.name or other_user.username if other_user else 'Чат'),
            'is_group': chat.is_group,
            'chat_type': chat.chat_type or ('group' if chat.is_group else 'private'),
            'avatar': other_user.avatar_url if other_user else (chat.avatar_url or None),
            'avatar_letter': (other_user.name or other_user.username)[0].upper() if other_user else (chat.name[0].upper() if chat.name else 'Г'),
            'members_count': len(chat.members),
            'last_message': {
                'content': last_message.content if last_message else None,
                'sender_id': last_message.sender_id if last_message else None,
                'created_at': last_message.created_at.isoformat() if last_message else None,
                'is_mine': last_message.sender_id == current_user.id if last_message else False
            } if last_message else None,
            'unread_count': unread_count,
            'other_user_id': other_user.id if other_user else None,
            'other_username': other_user.username if other_user else None
        })
    
    # Сортируем по последнему сообщению
    result.sort(key=lambda x: x['last_message']['created_at'] if x['last_message'] else '', reverse=True)
    return jsonify(result)

@app.route('/api/chats', methods=['POST'])
@login_required
def create_chat():
    """Создать новый чат (личный, групповой или канал)"""
    data = request.json
    chat_type = data.get('chat_type', 'private')
    
    if chat_type == 'channel':
        # Создание канала
        chat = Chat(
            name=data['name'],
            description=data.get('description', ''),
            chat_type='channel',
            is_group=True,
            is_public=data.get('is_public', False),
            owner_id=current_user.id,
            members_can_send=False,  # В каналах только админы пишут
            members_can_add=False,
            members_can_pin=False
        )
        # Генерируем invite link
        import secrets
        chat.invite_link = secrets.token_urlsafe(16)
        if data.get('username'):
            # Проверяем уникальность username
            existing = Chat.query.filter_by(username=data['username']).first()
            if not existing:
                chat.username = data['username']
        
        chat.members.append(current_user)
        db.session.add(chat)
        db.session.flush()
        
        # Добавляем владельца как админа
        from models import ChatMember
        member = ChatMember(chat_id=chat.id, user_id=current_user.id, role='owner')
        db.session.add(member)
        
    elif chat_type == 'group' or data.get('is_group'):
        # Групповой чат
        chat = Chat(
            name=data['name'],
            description=data.get('description', ''),
            chat_type='group',
            is_group=True,
            is_public=data.get('is_public', False),
            owner_id=current_user.id,
            members_can_send=data.get('members_can_send', True),
            members_can_add=data.get('members_can_add', False),
            members_can_pin=data.get('members_can_pin', False),
            slow_mode=data.get('slow_mode', 0)
        )
        # Генерируем invite link
        import secrets
        chat.invite_link = secrets.token_urlsafe(16)
        if data.get('username'):
            existing = Chat.query.filter_by(username=data['username']).first()
            if not existing:
                chat.username = data['username']
        
        chat.members.append(current_user)
        for user_id in data.get('member_ids', []):
            user = User.query.get(user_id)
            if user:
                chat.members.append(user)
        
        db.session.add(chat)
        db.session.flush()
        
        # Добавляем владельца
        from models import ChatMember
        member = ChatMember(chat_id=chat.id, user_id=current_user.id, role='owner')
        db.session.add(member)
        
        # Добавляем остальных участников
        for user_id in data.get('member_ids', []):
            m = ChatMember(chat_id=chat.id, user_id=user_id, role='member')
            db.session.add(m)
    else:
        # Личный чат - проверяем, нет ли уже такого
        other_user_id = data['user_id']
        other_user = User.query.get_or_404(other_user_id)
        
        # Ищем существующий личный чат
        existing_chat = Chat.query.filter(
            Chat.is_group == False,
            Chat.members.any(id=current_user.id),
            Chat.members.any(id=other_user_id)
        ).first()
        
        if existing_chat:
            return jsonify({'success': True, 'id': existing_chat.id, 'existing': True})
        
        chat = Chat(is_group=False, chat_type='private')
        chat.members.append(current_user)
        chat.members.append(other_user)
        db.session.add(chat)
    
    db.session.commit()
    return jsonify({'success': True, 'id': chat.id})


@app.route('/api/chats/<int:chat_id>/settings', methods=['PUT'])
@login_required
def update_chat_settings(chat_id):
    """Обновить настройки группы/канала"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Проверяем права (только владелец или админ)
    from models import ChatMember
    membership = ChatMember.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    if not membership or membership.role not in ['owner', 'admin']:
        if chat.owner_id != current_user.id:
            return jsonify({'error': 'Нет прав'}), 403
    
    data = request.json
    
    if 'name' in data:
        chat.name = data['name']
    if 'description' in data:
        chat.description = data['description']
    if 'is_public' in data:
        chat.is_public = data['is_public']
    if 'is_work_chat' in data:
        chat.is_work_chat = data['is_work_chat']
    if 'username' in data:
        if data['username']:
            existing = Chat.query.filter(Chat.username == data['username'], Chat.id != chat_id).first()
            if existing:
                return jsonify({'error': 'Username занят'}), 400
        chat.username = data['username'] or None
    if 'members_can_send' in data:
        chat.members_can_send = data['members_can_send']
    if 'members_can_add' in data:
        chat.members_can_add = data['members_can_add']
    if 'members_can_pin' in data:
        chat.members_can_pin = data['members_can_pin']
    if 'slow_mode' in data:
        chat.slow_mode = data['slow_mode']
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/chats/<int:chat_id>/avatar', methods=['POST'])
@login_required
def upload_chat_avatar(chat_id):
    """Загрузить аватар группы/канала"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Проверяем права
    from models import ChatMember
    membership = ChatMember.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    if not membership or membership.role not in ['owner', 'admin']:
        if chat.owner_id != current_user.id:
            return jsonify({'error': 'Нет прав'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не выбран'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    # Проверяем расширение
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return jsonify({'error': 'Недопустимый формат файла'}), 400
    
    # Создаём папку для аватаров чатов
    chat_avatar_folder = os.path.join(BASE_DIR, 'uploads', 'chat_avatars')
    os.makedirs(chat_avatar_folder, exist_ok=True)
    
    # Сохраняем файл
    filename = f"chat_{chat_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(chat_avatar_folder, filename)
    file.save(filepath)
    
    # Удаляем старый аватар если есть
    if chat.avatar_url and chat.avatar_url.startswith('/uploads/chat_avatars/'):
        old_path = os.path.join(BASE_DIR, chat.avatar_url.lstrip('/'))
        if os.path.exists(old_path):
            os.remove(old_path)
    
    # Обновляем URL аватара
    avatar_url = f'/uploads/chat_avatars/{filename}'
    chat.avatar_url = avatar_url
    db.session.commit()
    
    return jsonify({'success': True, 'avatar_url': avatar_url})


@app.route('/uploads/chat_avatars/<filename>')
def uploaded_chat_avatar(filename):
    """Отдача аватаров чатов"""
    chat_avatar_folder = os.path.join(BASE_DIR, 'uploads', 'chat_avatars')
    return send_from_directory(chat_avatar_folder, filename)


@app.route('/api/chats/<int:chat_id>/members', methods=['GET'])
@login_required
def get_chat_members(chat_id):
    """Получить список участников чата"""
    chat = Chat.query.get_or_404(chat_id)
    if current_user not in chat.members:
        return jsonify({'error': 'Нет доступа'}), 403
    
    from models import ChatMember
    members = []
    for user in chat.members:
        membership = ChatMember.query.filter_by(chat_id=chat_id, user_id=user.id).first()
        members.append({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'avatar_url': user.avatar_url,
            'role': membership.role if membership else 'member',
            'can_send_messages': membership.can_send_messages if membership else True
        })
    
    return jsonify(members)


@app.route('/api/chats/<int:chat_id>/members', methods=['POST'])
@login_required
def add_chat_member(chat_id):
    """Добавить участника в группу/канал"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Проверяем права
    from models import ChatMember
    membership = ChatMember.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    can_add = (membership and membership.role in ['owner', 'admin']) or chat.members_can_add or chat.owner_id == current_user.id
    
    if not can_add:
        return jsonify({'error': 'Нет прав добавлять участников'}), 403
    
    data = request.json
    user = User.query.get_or_404(data['user_id'])
    
    if user in chat.members:
        return jsonify({'error': 'Пользователь уже в чате'}), 400
    
    chat.members.append(user)
    member = ChatMember(chat_id=chat_id, user_id=user.id, role='member')
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/chats/<int:chat_id>/members/<int:user_id>', methods=['DELETE'])
@login_required
def remove_chat_member(chat_id, user_id):
    """Удалить участника из группы/канала"""
    chat = Chat.query.get_or_404(chat_id)
    
    from models import ChatMember
    membership = ChatMember.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    
    # Можно удалить себя или если есть права
    if user_id != current_user.id:
        if not membership or membership.role not in ['owner', 'admin']:
            if chat.owner_id != current_user.id:
                return jsonify({'error': 'Нет прав'}), 403
    
    user = User.query.get_or_404(user_id)
    if user in chat.members:
        chat.members.remove(user)
        ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id).delete()
        db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/chats/<int:chat_id>/members/<int:user_id>/role', methods=['PUT'])
@login_required
def update_member_role(chat_id, user_id):
    """Изменить роль участника"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Только владелец может менять роли
    if chat.owner_id != current_user.id:
        return jsonify({'error': 'Только владелец может менять роли'}), 403
    
    from models import ChatMember
    membership = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Участник не найден'}), 404
    
    data = request.json
    if data['role'] in ['admin', 'member']:
        membership.role = data['role']
        db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/chats/join/<invite_link>', methods=['POST'])
@login_required
def join_chat_by_link(invite_link):
    """Присоединиться к чату по пригласительной ссылке"""
    chat = Chat.query.filter_by(invite_link=invite_link).first_or_404()
    
    if current_user in chat.members:
        return jsonify({'success': True, 'id': chat.id, 'already_member': True})
    
    chat.members.append(current_user)
    from models import ChatMember
    member = ChatMember(chat_id=chat.id, user_id=current_user.id, role='member')
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'success': True, 'id': chat.id})


@app.route('/api/chats/<int:chat_id>/invite-link', methods=['POST'])
@login_required
def regenerate_invite_link(chat_id):
    """Перегенерировать пригласительную ссылку"""
    chat = Chat.query.get_or_404(chat_id)
    
    from models import ChatMember
    membership = ChatMember.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    if not membership or membership.role not in ['owner', 'admin']:
        if chat.owner_id != current_user.id:
            return jsonify({'error': 'Нет прав'}), 403
    
    import secrets
    chat.invite_link = secrets.token_urlsafe(16)
    db.session.commit()
    
    return jsonify({'success': True, 'invite_link': chat.invite_link})

@app.route('/api/chats/<int:chat_id>', methods=['GET'])
@login_required
def get_chat(chat_id):
    """Получить информацию о чате"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Проверяем, что пользователь участник чата
    if current_user not in chat.members:
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    other_user = None
    if not chat.is_group:
        for member in chat.members:
            if member.id != current_user.id:
                other_user = member
                break
    
    # Получаем роль текущего пользователя
    from models import ChatMember
    membership = ChatMember.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    user_role = membership.role if membership else 'member'
    
    return jsonify({
        'id': chat.id,
        'name': chat.name if chat.is_group else (other_user.name or other_user.username if other_user else 'Чат'),
        'description': chat.description or '',
        'avatar_url': chat.avatar_url or '',
        'chat_type': chat.chat_type or ('group' if chat.is_group else 'private'),
        'is_group': chat.is_group,
        'is_public': chat.is_public or False,
        'is_work_chat': chat.is_work_chat or False,
        'username': chat.username,
        'invite_link': chat.invite_link,
        'members_can_send': chat.members_can_send if chat.members_can_send is not None else True,
        'members_can_add': chat.members_can_add or False,
        'members_can_pin': chat.members_can_pin or False,
        'slow_mode': chat.slow_mode or 0,
        'owner_id': chat.owner_id,
        'user_role': user_role,
        'members': [{
            'id': m.id,
            'username': m.username,
            'name': m.name,
            'avatar_url': m.avatar_url
        } for m in chat.members],
        'other_user': {
            'id': other_user.id,
            'username': other_user.username,
            'name': other_user.name,
            'avatar_url': other_user.avatar_url
        } if other_user else None
    })

@app.route('/api/chats/<int:chat_id>/messages', methods=['GET'])
@login_required
def get_messages(chat_id):
    """Получить сообщения чата"""
    chat = Chat.query.get_or_404(chat_id)
    
    if current_user not in chat.members:
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    # Пагинация
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    messages = Message.query.filter_by(chat_id=chat_id)\
        .order_by(Message.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Помечаем сообщения как прочитанные
    Message.query.filter(
        Message.chat_id == chat_id,
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).update({'is_read': True})
    db.session.commit()
    
    def format_message(m):
        msg_data = {
            'id': m.id,
            'content': m.content,
            'sender_id': m.sender_id,
            'sender_name': m.sender.name or m.sender.username,
            'sender_username': m.sender.username,
            'sender_avatar': m.sender.avatar_url,
            'created_at': m.created_at.isoformat(),
            'edited_at': m.edited_at.isoformat() if m.edited_at else None,
            'is_read': m.is_read,
            'is_mine': m.sender_id == current_user.id,
            'reply_to': None
        }
        if m.reply_to:
            msg_data['reply_to'] = {
                'id': m.reply_to.id,
                'content': m.reply_to.content[:100],
                'sender_name': m.reply_to.sender.name or m.reply_to.sender.username
            }
        return msg_data
    
    return jsonify({
        'messages': [format_message(m) for m in reversed(messages.items)],
        'has_more': messages.has_next,
        'total': messages.total
    })

@app.route('/api/chats/<int:chat_id>/messages', methods=['POST'])
@login_required
def send_message(chat_id):
    """Отправить сообщение"""
    chat = Chat.query.get_or_404(chat_id)
    
    if current_user not in chat.members:
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    data = request.json
    content = data.get('content', '').strip()
    reply_to_id = data.get('reply_to_id')
    
    if not content:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    message = Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=content,
        reply_to_id=reply_to_id
    )
    db.session.add(message)
    db.session.commit()
    
    response_data = {
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender_id,
            'sender_name': current_user.name or current_user.username,
            'created_at': message.created_at.isoformat(),
            'is_mine': True,
            'reply_to': None
        }
    }
    
    if message.reply_to:
        response_data['message']['reply_to'] = {
            'id': message.reply_to.id,
            'content': message.reply_to.content[:100],
            'sender_name': message.reply_to.sender.name or message.reply_to.sender.username
        }
    
    return jsonify(response_data)

@app.route('/api/chats/<int:chat_id>/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(chat_id, message_id):
    """Удалить сообщение"""
    message = Message.query.filter_by(id=message_id, chat_id=chat_id, sender_id=current_user.id).first_or_404()
    db.session.delete(message)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/chats/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """Удалить чат (или выйти из группового)"""
    chat = Chat.query.get_or_404(chat_id)
    
    if current_user not in chat.members:
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    if chat.is_group:
        # Выходим из группы
        chat.members.remove(current_user)
        if len(chat.members) == 0:
            Message.query.filter_by(chat_id=chat_id).delete()
            db.session.delete(chat)
    else:
        # Удаляем личный чат полностью
        Message.query.filter_by(chat_id=chat_id).delete()
        db.session.delete(chat)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/chats/<int:chat_id>/read', methods=['POST'])
@login_required
def mark_chat_read(chat_id):
    """Пометить все сообщения чата как прочитанные"""
    chat = Chat.query.get_or_404(chat_id)
    
    if current_user not in chat.members:
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    Message.query.filter(
        Message.chat_id == chat_id,
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/chats/<int:chat_id>/messages/<int:message_id>', methods=['PUT'])
@login_required
def edit_message(chat_id, message_id):
    """Редактировать сообщение"""
    message = Message.query.filter_by(id=message_id, chat_id=chat_id, sender_id=current_user.id).first_or_404()
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    message.content = content
    message.edited_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'edited_at': message.edited_at.isoformat()
        }
    })

@app.route('/api/users/<int:user_id>/profile', methods=['GET'])
@login_required
def get_user_profile(user_id):
    """Получить профиль пользователя"""
    user = User.query.get_or_404(user_id)
    
    # Проверяем онлайн-статус (онлайн если был активен в последние 5 минут)
    is_online = False
    last_seen_text = ''
    if user.last_seen:
        diff = (datetime.utcnow() - user.last_seen).total_seconds()
        is_online = diff < 300  # 5 минут
        if not is_online:
            if diff < 3600:
                last_seen_text = f'был(а) {int(diff // 60)} мин. назад'
            elif diff < 86400:
                last_seen_text = f'был(а) {int(diff // 3600)} ч. назад'
            else:
                last_seen_text = f'был(а) {user.last_seen.strftime("%d.%m.%Y")}'
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'bio': user.bio,
        'avatar_url': user.avatar_url,
        'created_at': user.created_at.isoformat(),
        'is_online': is_online,
        'last_seen_text': last_seen_text if not is_online else 'в сети'
    })

@app.route('/api/ping', methods=['POST'])
@login_required
def ping_online():
    """Обновить онлайн-статус пользователя"""
    current_user.last_seen = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/chats/<int:chat_id>/typing', methods=['POST'])
@login_required
def set_typing(chat_id):
    """Установить статус 'печатает' (хранится в памяти, не в БД)"""
    # В реальном приложении это делается через WebSocket
    # Здесь просто возвращаем успех
    return jsonify({'success': True})

# ==================== API: НАСТРОЙКИ ПРОФИЛЯ ====================

@app.route('/api/profile/settings', methods=['GET'])
@login_required
def get_profile_settings():
    """Получить настройки профиля"""
    return jsonify({
        'username': current_user.username,
        'name': current_user.name,
        'bio': current_user.bio,
        'email': current_user.email,
        'avatar_url': current_user.avatar_url,
        'pinned_playlist_id': current_user.pinned_playlist_id,
        'privacy': {
            'last_seen': getattr(current_user, 'privacy_last_seen', 'everyone'),
            'bio': getattr(current_user, 'privacy_bio', 'everyone'),
            'avatar': getattr(current_user, 'privacy_avatar', 'everyone'),
            'playlists': getattr(current_user, 'privacy_playlists', 'everyone')
        }
    })

@app.route('/api/profile/settings', methods=['PUT'])
@login_required
def update_profile_settings():
    """Обновить настройки профиля"""
    data = request.json
    
    if 'username' in data and data['username'] != current_user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username уже занят'}), 400
        current_user.username = data['username']
    
    if 'name' in data:
        current_user.name = data['name']
    if 'bio' in data:
        current_user.bio = data['bio']
    if 'avatar_url' in data:
        current_user.avatar_url = data['avatar_url']
    if 'pinned_playlist_id' in data:
        current_user.pinned_playlist_id = data['pinned_playlist_id']
    
    # Настройки конфиденциальности
    if 'privacy' in data:
        privacy = data['privacy']
        if 'last_seen' in privacy:
            current_user.privacy_last_seen = privacy['last_seen']
        if 'bio' in privacy:
            current_user.privacy_bio = privacy['bio']
        if 'avatar' in privacy:
            current_user.privacy_avatar = privacy['avatar']
        if 'playlists' in privacy:
            current_user.privacy_playlists = privacy['playlists']
    
    db.session.commit()
    return jsonify({'success': True})

# ==================== API: БЛОКИРОВКА ПОЛЬЗОВАТЕЛЕЙ ====================

@app.route('/api/users/<int:user_id>/block', methods=['POST'])
@login_required
def block_user(user_id):
    """Заблокировать пользователя"""
    if user_id == current_user.id:
        return jsonify({'error': 'Нельзя заблокировать себя'}), 400
    
    user = User.query.get_or_404(user_id)
    
    # Проверяем, не заблокирован ли уже
    existing = BlockedUser.query.filter_by(user_id=current_user.id, blocked_user_id=user_id).first()
    if existing:
        return jsonify({'error': 'Пользователь уже заблокирован'}), 400
    
    block = BlockedUser(user_id=current_user.id, blocked_user_id=user_id)
    db.session.add(block)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/unblock', methods=['POST'])
@login_required
def unblock_user(user_id):
    """Разблокировать пользователя"""
    block = BlockedUser.query.filter_by(user_id=current_user.id, blocked_user_id=user_id).first_or_404()
    db.session.delete(block)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/blocked-users', methods=['GET'])
@login_required
def get_blocked_users():
    """Получить список заблокированных пользователей"""
    blocked = BlockedUser.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': b.blocked_user.id,
        'username': b.blocked_user.username,
        'name': b.blocked_user.name,
        'avatar_url': b.blocked_user.avatar_url,
        'blocked_at': b.created_at.isoformat()
    } for b in blocked])

# ==================== API: ЗАКРЕПЛЁННЫЙ ПЛЕЙЛИСТ ====================

@app.route('/api/profile/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Загрузить аватар"""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не выбран'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    # Проверяем расширение
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return jsonify({'error': 'Недопустимый формат файла'}), 400
    
    # Создаём папку для аватаров
    avatar_folder = os.path.join(BASE_DIR, 'uploads', 'avatars')
    os.makedirs(avatar_folder, exist_ok=True)
    
    # Сохраняем файл
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(avatar_folder, filename)
    file.save(filepath)
    
    # Обновляем URL аватара
    avatar_url = f'/uploads/avatars/{filename}'
    current_user.avatar_url = avatar_url
    db.session.commit()
    
    return jsonify({'success': True, 'avatar_url': avatar_url})

@app.route('/uploads/avatars/<filename>')
def uploaded_avatar(filename):
    avatar_folder = os.path.join(BASE_DIR, 'uploads', 'avatars')
    return send_from_directory(avatar_folder, filename)

@app.route('/api/profile/pinned-playlist', methods=['PUT'])
@login_required
def set_pinned_playlist():
    """Установить закреплённый плейлист"""
    data = request.json
    playlist_id = data.get('playlist_id')
    
    if playlist_id:
        playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first_or_404()
        current_user.pinned_playlist_id = playlist_id
    else:
        current_user.pinned_playlist_id = None
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/pinned-playlist', methods=['GET'])
def get_user_pinned_playlist(user_id):
    """Получить закреплённый плейлист пользователя"""
    user = User.query.get_or_404(user_id)
    
    # Проверяем настройки приватности
    if user.privacy_playlists == 'nobody':
        return jsonify({'error': 'Плейлисты скрыты'}), 403
    
    if user.privacy_playlists == 'contacts':
        # Проверяем, являемся ли мы контактом
        if not current_user.is_authenticated:
            return jsonify({'error': 'Плейлисты доступны только контактам'}), 403
    
    if not user.pinned_playlist_id:
        return jsonify({'playlist': None})
    
    playlist = Playlist.query.get(user.pinned_playlist_id)
    if not playlist:
        return jsonify({'playlist': None})
    
    tracks = Track.query.filter_by(playlist_id=playlist.id).order_by(Track.order).all()
    
    return jsonify({
        'playlist': {
            'id': playlist.id,
            'name': playlist.name,
            'description': playlist.description,
            'tracks_count': len(tracks),
            'tracks': [{
                'id': t.id,
                'title': t.title,
                'artist': t.artist,
                'url': t.url,
                'duration': t.duration
            } for t in tracks]
        }
    })

# ==================== API: РЕЖИМ ФОКУСИРОВКИ ====================

@app.route('/api/focus/tree', methods=['GET'])
@login_required
def get_focus_tree():
    """Получить дерево концентрации"""
    tree = FocusTree.query.filter_by(user_id=current_user.id).first()
    if not tree:
        tree = FocusTree(user_id=current_user.id)
        db.session.add(tree)
        db.session.commit()
    
    # Проверяем, сколько дней прошло без сессий - дерево чахнет
    health_changed = False
    if tree.last_session_date:
        today = datetime.utcnow().date()
        days_without_session = (today - tree.last_session_date).days
        
        if days_without_session > 1:
            # Уменьшаем здоровье за каждый пропущенный день (кроме первого)
            health_loss = (days_without_session - 1) * 5  # -5 HP за каждый день без сессии
            new_health = max(10, tree.health - health_loss)  # Минимум 10 HP
            
            if new_health != tree.health:
                tree.health = new_health
                health_changed = True
            
            # Сбрасываем streak если пропущено больше 1 дня
            if days_without_session > 1 and tree.streak_days > 0:
                tree.streak_days = 0
                health_changed = True
        
        if health_changed:
            db.session.commit()
    
    # Рассчитываем опыт до следующего уровня
    exp_for_next = tree.level * 100
    
    return jsonify({
        'level': tree.level,
        'experience': tree.experience,
        'exp_for_next_level': exp_for_next,
        'health': tree.health,
        'total_focus_minutes': tree.total_focus_minutes,
        'total_sessions': tree.total_sessions,
        'streak_days': tree.streak_days,
        'tree_type': tree.tree_type,
        'garden_level': getattr(tree, 'garden_level', 0),
        'garden_exp': getattr(tree, 'garden_exp', 0),
        'health_changed': health_changed  # Флаг для анимации увядания
    })

@app.route('/api/focus/settings', methods=['GET'])
@login_required
def get_focus_settings():
    """Получить настройки фокусировки"""
    settings = FocusSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = FocusSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    
    return jsonify({
        'work_duration': settings.work_duration,
        'short_break': settings.short_break,
        'long_break': settings.long_break,
        'sessions_before_long_break': settings.sessions_before_long_break,
        'block_notifications': settings.block_notifications,
        'fullscreen_mode': settings.fullscreen_mode,
        'ambient_sound': settings.ambient_sound,
        'ambient_volume': settings.ambient_volume,
        'theme': getattr(settings, 'theme', 'dark'),
        'water_reminder': getattr(settings, 'water_reminder', True),
        'water_interval': getattr(settings, 'water_interval', 30),
        'eye_reminder': getattr(settings, 'eye_reminder', True),
        'eye_interval': getattr(settings, 'eye_interval', 20)
    })

@app.route('/api/focus/settings', methods=['PUT'])
@login_required
def update_focus_settings():
    """Обновить настройки фокусировки"""
    settings = FocusSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = FocusSettings(user_id=current_user.id)
        db.session.add(settings)
    
    data = request.json
    if 'work_duration' in data:
        settings.work_duration = max(1, min(120, data['work_duration']))
    if 'short_break' in data:
        settings.short_break = max(1, min(30, data['short_break']))
    if 'long_break' in data:
        settings.long_break = max(5, min(60, data['long_break']))
    if 'sessions_before_long_break' in data:
        settings.sessions_before_long_break = max(2, min(10, data['sessions_before_long_break']))
    if 'block_notifications' in data:
        settings.block_notifications = data['block_notifications']
    if 'fullscreen_mode' in data:
        settings.fullscreen_mode = data['fullscreen_mode']
    if 'ambient_sound' in data:
        settings.ambient_sound = data['ambient_sound']
    if 'ambient_volume' in data:
        settings.ambient_volume = max(0, min(100, data['ambient_volume']))
    if 'theme' in data:
        settings.theme = data['theme']
    if 'water_reminder' in data:
        settings.water_reminder = data['water_reminder']
    if 'water_interval' in data:
        settings.water_interval = max(10, min(120, data['water_interval']))
    if 'eye_reminder' in data:
        settings.eye_reminder = data['eye_reminder']
    if 'eye_interval' in data:
        settings.eye_interval = max(10, min(60, data['eye_interval']))
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/focus/session/start', methods=['POST'])
@login_required
def start_focus_session():
    """Начать сессию фокусировки"""
    data = request.json
    
    session = FocusSession(
        user_id=current_user.id,
        task_id=data.get('task_id'),
        playlist_id=data.get('playlist_id'),
        duration_minutes=data.get('duration_minutes', 25)
    )
    db.session.add(session)
    db.session.commit()
    
    return jsonify({'success': True, 'session_id': session.id})

@app.route('/api/focus/session/<int:session_id>/end', methods=['POST'])
@login_required
def end_focus_session(session_id):
    """Завершить сессию фокусировки"""
    session = FocusSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    data = request.json
    
    session.ended_at = datetime.utcnow()
    session.is_completed = data.get('completed', False)
    session.distractions = data.get('distractions', 0)
    
    # Обновляем дерево
    tree = FocusTree.query.filter_by(user_id=current_user.id).first()
    if not tree:
        tree = FocusTree(user_id=current_user.id)
        db.session.add(tree)
    
    # Рассчитываем время сессии
    if session.started_at and session.ended_at:
        actual_minutes = int((session.ended_at - session.started_at).total_seconds() / 60)
    else:
        actual_minutes = session.duration_minutes
    
    if session.is_completed:
        # Успешная сессия - дерево растёт
        exp_gained = actual_minutes * 2
        if session.distractions == 0:
            exp_gained = int(exp_gained * 1.5)  # Бонус за отсутствие отвлечений
        
        tree.experience += exp_gained
        tree.total_focus_minutes += actual_minutes
        tree.total_sessions += 1
        session.tree_growth = exp_gained
        
        # Восстанавливаем здоровье
        tree.health = min(100, tree.health + 5)
        
        # Проверяем повышение уровня
        exp_for_next = tree.level * 100
        while tree.experience >= exp_for_next and tree.level < 10:
            tree.experience -= exp_for_next
            tree.level += 1
            exp_for_next = tree.level * 100
        
        # Если дерево на макс уровне - растим сад
        if tree.level >= 10:
            garden_level = getattr(tree, 'garden_level', 0) or 0
            garden_exp = getattr(tree, 'garden_exp', 0) or 0
            garden_exp += exp_gained
            # Каждые 200 XP - новый уровень сада (новое растение)
            garden_exp_needed = (garden_level + 1) * 200
            while garden_exp >= garden_exp_needed and garden_level < 20:
                garden_exp -= garden_exp_needed
                garden_level += 1
                garden_exp_needed = (garden_level + 1) * 200
            tree.garden_level = garden_level
            tree.garden_exp = garden_exp
        
        # Обновляем streak
        today = datetime.utcnow().date()
        if tree.last_session_date:
            days_diff = (today - tree.last_session_date).days
            if days_diff == 1:
                tree.streak_days += 1
            elif days_diff > 1:
                tree.streak_days = 1
        else:
            tree.streak_days = 1
        tree.last_session_date = today
    else:
        # Незавершённая сессия - дерево страдает
        tree.health = max(0, tree.health - 10 - session.distractions * 5)
    
    db.session.commit()
    
    # Проверяем достижения
    unlocked = []
    if session.is_completed:
        unlocked = check_and_unlock_achievements(current_user.id)
        
        # Проверяем специальные достижения
        hour = datetime.utcnow().hour
        existing = {a.achievement_type for a in Achievement.query.filter_by(user_id=current_user.id).all()}
        
        if session.distractions == 0 and 'perfect_session' not in existing:
            achievement = Achievement(user_id=current_user.id, achievement_type='perfect_session')
            db.session.add(achievement)
            unlocked.append({'type': 'perfect_session', 'name': 'Идеальная сессия', 'icon': '✨'})
        
        if hour < 7 and 'early_bird' not in existing:
            achievement = Achievement(user_id=current_user.id, achievement_type='early_bird')
            db.session.add(achievement)
            unlocked.append({'type': 'early_bird', 'name': 'Ранняя пташка', 'icon': '🌅'})
        
        if hour >= 23 and 'night_owl' not in existing:
            achievement = Achievement(user_id=current_user.id, achievement_type='night_owl')
            db.session.add(achievement)
            unlocked.append({'type': 'night_owl', 'name': 'Ночная сова', 'icon': '🦉'})
        
        if unlocked:
            db.session.commit()
    
    return jsonify({
        'success': True,
        'tree': {
            'level': tree.level,
            'experience': tree.experience,
            'health': tree.health,
            'exp_gained': session.tree_growth if session.is_completed else 0
        },
        'unlocked': unlocked
    })

@app.route('/api/focus/session/<int:session_id>/distraction', methods=['POST'])
@login_required
def report_distraction(session_id):
    """Зафиксировать отвлечение"""
    session = FocusSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    session.distractions += 1
    
    # Дерево немного страдает
    tree = FocusTree.query.filter_by(user_id=current_user.id).first()
    if tree:
        tree.health = max(0, tree.health - 2)
    
    db.session.commit()
    return jsonify({'success': True, 'distractions': session.distractions})

@app.route('/api/focus/stats', methods=['GET'])
@login_required
def get_focus_stats():
    """Получить статистику фокусировки"""
    from sqlalchemy import func
    
    # Статистика за сегодня
    today = datetime.utcnow().date()
    today_sessions = FocusSession.query.filter(
        FocusSession.user_id == current_user.id,
        func.date(FocusSession.started_at) == today,
        FocusSession.is_completed == True
    ).all()
    
    today_minutes = sum(s.duration_minutes for s in today_sessions)
    today_count = len(today_sessions)
    
    # Статистика за неделю
    from datetime import timedelta
    week_ago = today - timedelta(days=7)
    week_sessions = FocusSession.query.filter(
        FocusSession.user_id == current_user.id,
        func.date(FocusSession.started_at) >= week_ago,
        FocusSession.is_completed == True
    ).all()
    
    # Группируем по дням
    daily_stats = {}
    for s in week_sessions:
        day = s.started_at.date().isoformat()
        if day not in daily_stats:
            daily_stats[day] = {'minutes': 0, 'sessions': 0}
        daily_stats[day]['minutes'] += s.duration_minutes
        daily_stats[day]['sessions'] += 1
    
    # Дерево
    tree = FocusTree.query.filter_by(user_id=current_user.id).first()
    
    return jsonify({
        'today': {
            'minutes': today_minutes,
            'sessions': today_count
        },
        'week': {
            'total_minutes': sum(s.duration_minutes for s in week_sessions),
            'total_sessions': len(week_sessions),
            'daily': daily_stats
        },
        'all_time': {
            'total_minutes': tree.total_focus_minutes if tree else 0,
            'total_sessions': tree.total_sessions if tree else 0,
            'streak_days': tree.streak_days if tree else 0
        }
    })

# ==================== API: РАСШИРЕННАЯ АНАЛИТИКА ====================

@app.route('/api/focus/stats/extended', methods=['GET'])
@login_required
def get_extended_focus_stats():
    """Расширенная статистика: месяц, год, по часам"""
    from sqlalchemy import func
    from datetime import timedelta
    import json
    
    today = datetime.utcnow().date()
    period = request.args.get('period', 'month')  # month, year
    
    if period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    sessions = FocusSession.query.filter(
        FocusSession.user_id == current_user.id,
        func.date(FocusSession.started_at) >= start_date,
        FocusSession.is_completed == True
    ).all()
    
    # Группируем по дням
    daily_stats = {}
    hourly_stats = {i: 0 for i in range(24)}  # Статистика по часам
    task_stats = {}  # Статистика по задачам
    
    for s in sessions:
        day = s.started_at.date().isoformat()
        hour = s.started_at.hour
        
        if day not in daily_stats:
            daily_stats[day] = {'minutes': 0, 'sessions': 0}
        daily_stats[day]['minutes'] += s.duration_minutes
        daily_stats[day]['sessions'] += 1
        
        hourly_stats[hour] += s.duration_minutes
        
        # Статистика по задачам
        if s.task_id:
            if s.task_id not in task_stats:
                task = Task.query.get(s.task_id)
                task_stats[s.task_id] = {
                    'title': task.title if task else 'Удалённая задача',
                    'minutes': 0,
                    'sessions': 0
                }
            task_stats[s.task_id]['minutes'] += s.duration_minutes
            task_stats[s.task_id]['sessions'] += 1
    
    # Лучший день
    best_day = max(daily_stats.items(), key=lambda x: x[1]['minutes']) if daily_stats else (None, {'minutes': 0})
    
    # Самый продуктивный час
    best_hour = max(hourly_stats.items(), key=lambda x: x[1])
    
    return jsonify({
        'period': period,
        'daily': daily_stats,
        'hourly': hourly_stats,
        'tasks': list(task_stats.values()),
        'summary': {
            'total_minutes': sum(s.duration_minutes for s in sessions),
            'total_sessions': len(sessions),
            'avg_daily_minutes': sum(d['minutes'] for d in daily_stats.values()) // max(len(daily_stats), 1),
            'best_day': {'date': best_day[0], 'minutes': best_day[1]['minutes']},
            'best_hour': {'hour': best_hour[0], 'minutes': best_hour[1]}
        }
    })


# ==================== API: ЖУРНАЛ НАСТРОЕНИЯ ====================

@app.route('/api/mood', methods=['GET'])
@login_required
def get_mood_entries():
    """Получить записи настроения"""
    from sqlalchemy import func
    from datetime import timedelta
    
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= start_date
    ).order_by(MoodEntry.date.desc()).all()
    
    return jsonify([{
        'id': e.id,
        'mood': e.mood,
        'energy': e.energy,
        'note': e.note,
        'tags': e.tags.split(',') if e.tags else [],
        'date': e.date.isoformat(),
        'created_at': e.created_at.isoformat()
    } for e in entries])


@app.route('/api/mood', methods=['POST'])
@login_required
def create_mood_entry():
    """Создать запись настроения"""
    data = request.json
    today = datetime.utcnow().date()
    
    # Проверяем, есть ли уже запись за сегодня
    existing = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date == today
    ).first()
    
    if existing:
        # Обновляем существующую
        existing.mood = data.get('mood', existing.mood)
        existing.energy = data.get('energy', existing.energy)
        existing.note = data.get('note', existing.note)
        existing.tags = ','.join(data.get('tags', []))
        db.session.commit()
        return jsonify({'success': True, 'id': existing.id, 'updated': True})
    
    entry = MoodEntry(
        user_id=current_user.id,
        mood=data['mood'],
        energy=data.get('energy', 3),
        note=data.get('note', ''),
        tags=','.join(data.get('tags', [])),
        date=today
    )
    db.session.add(entry)
    db.session.commit()
    
    return jsonify({'success': True, 'id': entry.id})


@app.route('/api/mood/stats', methods=['GET'])
@login_required
def get_mood_stats():
    """Статистика настроения"""
    from sqlalchemy import func
    from datetime import timedelta
    
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= start_date
    ).all()
    
    if not entries:
        return jsonify({
            'avg_mood': 0,
            'avg_energy': 0,
            'entries_count': 0,
            'mood_trend': [],
            'common_tags': []
        })
    
    # Средние значения
    avg_mood = sum(e.mood for e in entries) / len(entries)
    avg_energy = sum(e.energy for e in entries) / len(entries)
    
    # Тренд настроения по дням
    mood_trend = [{
        'date': e.date.isoformat(),
        'mood': e.mood,
        'energy': e.energy
    } for e in sorted(entries, key=lambda x: x.date)]
    
    # Популярные теги
    all_tags = []
    for e in entries:
        if e.tags:
            all_tags.extend(e.tags.split(','))
    
    tag_counts = {}
    for tag in all_tags:
        tag = tag.strip()
        if tag:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    common_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:10]
    
    return jsonify({
        'avg_mood': round(avg_mood, 1),
        'avg_energy': round(avg_energy, 1),
        'entries_count': len(entries),
        'mood_trend': mood_trend,
        'common_tags': [{'tag': t[0], 'count': t[1]} for t in common_tags]
    })


# ==================== API: ШАБЛОНЫ ЗАДАЧ ====================

@app.route('/api/templates', methods=['GET'])
@login_required
def get_task_templates():
    """Получить шаблоны задач"""
    templates = TaskTemplate.query.filter(
        (TaskTemplate.user_id == current_user.id) | (TaskTemplate.is_default == True)
    ).order_by(TaskTemplate.created_at.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'description': t.description,
        'icon': t.icon,
        'color': t.color,
        'timer_minutes': t.timer_minutes,
        'break_minutes': t.break_minutes,
        'sessions_count': t.sessions_count,
        'focus_preset': t.focus_preset,
        'ambient_sound': t.ambient_sound,
        'subtasks': json.loads(t.subtasks_json) if t.subtasks_json else [],
        'is_default': t.is_default,
        'is_own': t.user_id == current_user.id
    } for t in templates])


@app.route('/api/templates', methods=['POST'])
@login_required
def create_task_template():
    """Создать шаблон задачи"""
    import json
    data = request.json
    
    template = TaskTemplate(
        user_id=current_user.id,
        name=data['name'],
        description=data.get('description', ''),
        icon=data.get('icon', '📋'),
        color=data.get('color', 'primary'),
        timer_minutes=data.get('timer_minutes', 25),
        break_minutes=data.get('break_minutes', 5),
        sessions_count=data.get('sessions_count', 4),
        focus_preset=data.get('focus_preset', 'pomodoro'),
        ambient_sound=data.get('ambient_sound', 'none'),
        subtasks_json=json.dumps(data.get('subtasks', []))
    )
    db.session.add(template)
    db.session.commit()
    
    return jsonify({'success': True, 'id': template.id})


@app.route('/api/templates/<int:template_id>', methods=['PUT'])
@login_required
def update_task_template(template_id):
    """Обновить шаблон"""
    import json
    template = TaskTemplate.query.filter_by(id=template_id, user_id=current_user.id).first_or_404()
    data = request.json
    
    template.name = data.get('name', template.name)
    template.description = data.get('description', template.description)
    template.icon = data.get('icon', template.icon)
    template.color = data.get('color', template.color)
    template.timer_minutes = data.get('timer_minutes', template.timer_minutes)
    template.break_minutes = data.get('break_minutes', template.break_minutes)
    template.sessions_count = data.get('sessions_count', template.sessions_count)
    template.focus_preset = data.get('focus_preset', template.focus_preset)
    template.ambient_sound = data.get('ambient_sound', template.ambient_sound)
    if 'subtasks' in data:
        template.subtasks_json = json.dumps(data['subtasks'])
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
@login_required
def delete_task_template(template_id):
    """Удалить шаблон"""
    template = TaskTemplate.query.filter_by(id=template_id, user_id=current_user.id).first_or_404()
    db.session.delete(template)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/tasks/from-template', methods=['POST'])
@login_required
def create_task_from_template():
    """Создать задачу из шаблона"""
    import json
    from datetime import timedelta
    data = request.json
    template_id = data.get('template_id')
    
    template = TaskTemplate.query.get_or_404(template_id)
    
    # Защита от дублирования: проверяем, не создавалась ли задача из этого шаблона в последние 5 секунд
    title = data.get('title', template.name)
    five_seconds_ago = datetime.utcnow() - timedelta(seconds=5)
    recent_duplicate = Task.query.filter(
        Task.user_id == current_user.id,
        Task.title == title,
        Task.created_at >= five_seconds_ago
    ).first()
    
    if recent_duplicate:
        return jsonify({'success': True, 'task_id': recent_duplicate.id, 'duplicate': True})
    
    # Создаём задачу
    task = Task(
        user_id=current_user.id,
        title=title,
        description=data.get('description', template.description),
        timer_minutes=template.timer_minutes,
        break_minutes=template.break_minutes,
        sessions_count=template.sessions_count,
        focus_preset=template.focus_preset,
        ambient_sound=template.ambient_sound
    )
    db.session.add(task)
    db.session.flush()  # Получаем ID задачи
    
    # Создаём подзадачи из шаблона
    subtasks = json.loads(template.subtasks_json) if template.subtasks_json else []
    for i, st_title in enumerate(subtasks):
        subtask = Subtask(
            task_id=task.id,
            title=st_title,
            order=i
        )
        db.session.add(subtask)
    
    db.session.commit()
    return jsonify({'success': True, 'task_id': task.id})


# ==================== API: ДОСТИЖЕНИЯ (ГЕЙМИФИКАЦИЯ) ====================

# Определение всех достижений
ACHIEVEMENTS = {
    'first_session': {'name': 'Первый шаг', 'icon': '🌱', 'desc': 'Завершите первую сессию фокуса'},
    'sessions_10': {'name': 'Начинающий', 'icon': '🌿', 'desc': 'Завершите 10 сессий'},
    'sessions_50': {'name': 'Практик', 'icon': '🌳', 'desc': 'Завершите 50 сессий'},
    'sessions_100': {'name': 'Мастер фокуса', 'icon': '🏆', 'desc': 'Завершите 100 сессий'},
    'streak_3': {'name': 'Три дня подряд', 'icon': '🔥', 'desc': '3 дня подряд с сессиями'},
    'streak_7': {'name': 'Неделя силы', 'icon': '💪', 'desc': '7 дней подряд с сессиями'},
    'streak_30': {'name': 'Месяц дисциплины', 'icon': '⭐', 'desc': '30 дней подряд'},
    'hours_10': {'name': '10 часов фокуса', 'icon': '⏰', 'desc': 'Накопите 10 часов фокуса'},
    'hours_50': {'name': '50 часов фокуса', 'icon': '🎯', 'desc': 'Накопите 50 часов фокуса'},
    'hours_100': {'name': 'Центурион', 'icon': '👑', 'desc': 'Накопите 100 часов фокуса'},
    'perfect_session': {'name': 'Идеальная сессия', 'icon': '✨', 'desc': 'Сессия без отвлечений'},
    'early_bird': {'name': 'Ранняя пташка', 'icon': '🌅', 'desc': 'Сессия до 7 утра'},
    'night_owl': {'name': 'Ночная сова', 'icon': '🦉', 'desc': 'Сессия после 23:00'},
    'tree_level_5': {'name': 'Садовник', 'icon': '🌲', 'desc': 'Дерево достигло 5 уровня'},
    'tree_level_10': {'name': 'Лесник', 'icon': '🌴', 'desc': 'Дерево достигло 10 уровня'},
    'tasks_10': {'name': 'Продуктивный', 'icon': '📋', 'desc': 'Завершите 10 задач'},
    'tasks_50': {'name': 'Машина', 'icon': '🚀', 'desc': 'Завершите 50 задач'},
    'gratitude_7': {'name': 'Благодарный', 'icon': '🙏', 'desc': '7 записей благодарности'},
    'mood_streak_7': {'name': 'Самопознание', 'icon': '💭', 'desc': '7 дней записей настроения'},
    'memory_master': {'name': 'Острый ум', 'icon': '🧠', 'desc': 'Достигните 10 уровня в игре на память'},
}


@app.route('/api/achievements', methods=['GET'])
@login_required
def get_achievements():
    """Получить все достижения пользователя"""
    unlocked = Achievement.query.filter_by(user_id=current_user.id).all()
    unlocked_types = {a.achievement_type: a.unlocked_at.isoformat() for a in unlocked}
    
    result = []
    for key, data in ACHIEVEMENTS.items():
        result.append({
            'type': key,
            'name': data['name'],
            'icon': data['icon'],
            'description': data['desc'],
            'unlocked': key in unlocked_types,
            'unlocked_at': unlocked_types.get(key)
        })
    
    return jsonify({
        'achievements': result,
        'unlocked_count': len(unlocked),
        'total_count': len(ACHIEVEMENTS)
    })


def check_and_unlock_achievements(user_id):
    """Проверить и разблокировать достижения"""
    unlocked = []
    existing = {a.achievement_type for a in Achievement.query.filter_by(user_id=user_id).all()}
    
    tree = FocusTree.query.filter_by(user_id=user_id).first()
    if not tree:
        return unlocked
    
    # Проверяем достижения по сессиям
    checks = [
        ('first_session', tree.total_sessions >= 1),
        ('sessions_10', tree.total_sessions >= 10),
        ('sessions_50', tree.total_sessions >= 50),
        ('sessions_100', tree.total_sessions >= 100),
        ('streak_3', tree.streak_days >= 3),
        ('streak_7', tree.streak_days >= 7),
        ('streak_30', tree.streak_days >= 30),
        ('hours_10', tree.total_focus_minutes >= 600),
        ('hours_50', tree.total_focus_minutes >= 3000),
        ('hours_100', tree.total_focus_minutes >= 6000),
        ('tree_level_5', tree.level >= 5),
        ('tree_level_10', tree.level >= 10),
    ]
    
    # Проверяем задачи
    completed_tasks = Task.query.filter_by(user_id=user_id, status='completed').count()
    checks.append(('tasks_10', completed_tasks >= 10))
    checks.append(('tasks_50', completed_tasks >= 50))
    
    # Проверяем благодарности
    gratitude_count = GratitudeEntry.query.filter_by(user_id=user_id).count()
    checks.append(('gratitude_7', gratitude_count >= 7))
    
    # Проверяем настроение
    mood_count = MoodEntry.query.filter_by(user_id=user_id).count()
    checks.append(('mood_streak_7', mood_count >= 7))
    
    # Проверяем игры на память
    best_memory = db.session.query(db.func.max(MemoryGameScore.level)).filter_by(user_id=user_id).scalar() or 0
    checks.append(('memory_master', best_memory >= 10))
    
    for achievement_type, condition in checks:
        if condition and achievement_type not in existing:
            achievement = Achievement(user_id=user_id, achievement_type=achievement_type)
            db.session.add(achievement)
            unlocked.append({
                'type': achievement_type,
                'name': ACHIEVEMENTS[achievement_type]['name'],
                'icon': ACHIEVEMENTS[achievement_type]['icon']
            })
    
    if unlocked:
        db.session.commit()
    
    return unlocked


@app.route('/api/achievements/check', methods=['POST'])
@login_required
def check_achievements():
    """Проверить новые достижения"""
    unlocked = check_and_unlock_achievements(current_user.id)
    return jsonify({'unlocked': unlocked})


# ==================== API: ЖУРНАЛ БЛАГОДАРНОСТИ ====================

@app.route('/api/gratitude', methods=['GET'])
@login_required
def get_gratitude_entries():
    """Получить записи благодарности"""
    from datetime import timedelta
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    entries = GratitudeEntry.query.filter(
        GratitudeEntry.user_id == current_user.id,
        GratitudeEntry.date >= start_date
    ).order_by(GratitudeEntry.date.desc()).all()
    
    return jsonify([{
        'id': e.id,
        'content': e.content,
        'category': e.category,
        'date': e.date.isoformat(),
        'created_at': e.created_at.isoformat()
    } for e in entries])


@app.route('/api/gratitude', methods=['POST'])
@login_required
def create_gratitude_entry():
    """Создать запись благодарности"""
    data = request.json
    today = datetime.utcnow().date()
    
    entry = GratitudeEntry(
        user_id=current_user.id,
        content=data['content'],
        category=data.get('category', 'general'),
        date=today
    )
    db.session.add(entry)
    db.session.commit()
    
    # Проверяем достижения
    unlocked = check_and_unlock_achievements(current_user.id)
    
    return jsonify({'success': True, 'id': entry.id, 'unlocked': unlocked})


@app.route('/api/gratitude/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_gratitude_entry(entry_id):
    """Удалить запись благодарности"""
    entry = GratitudeEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'success': True})


# ==================== API: ИГРЫ НА ПАМЯТЬ ====================

@app.route('/api/memory-game/scores', methods=['GET'])
@login_required
def get_memory_scores():
    """Получить лучшие результаты игр"""
    game_type = request.args.get('type', 'sequence')
    
    # Лучший результат пользователя
    best = MemoryGameScore.query.filter_by(
        user_id=current_user.id,
        game_type=game_type
    ).order_by(MemoryGameScore.level.desc()).first()
    
    # Топ-10 всех пользователей
    top_scores = db.session.query(
        MemoryGameScore.user_id,
        User.username,
        db.func.max(MemoryGameScore.level).label('best_level')
    ).join(User).filter(
        MemoryGameScore.game_type == game_type
    ).group_by(MemoryGameScore.user_id, User.username).order_by(
        db.desc('best_level')
    ).limit(10).all()
    
    return jsonify({
        'personal_best': {
            'level': best.level if best else 0,
            'score': best.score if best else 0
        },
        'leaderboard': [{
            'username': s.username,
            'level': s.best_level,
            'is_me': s.user_id == current_user.id
        } for s in top_scores]
    })


@app.route('/api/memory-game/scores', methods=['POST'])
@login_required
def save_memory_score():
    """Сохранить результат игры"""
    data = request.json
    
    score = MemoryGameScore(
        user_id=current_user.id,
        game_type=data['game_type'],
        score=data['score'],
        level=data['level']
    )
    db.session.add(score)
    db.session.commit()
    
    # Проверяем достижения
    unlocked = check_and_unlock_achievements(current_user.id)
    
    return jsonify({'success': True, 'unlocked': unlocked})


# ==================== API: ПРОГРЕСС ЗАДАЧ ====================

@app.route('/api/tasks/progress', methods=['GET'])
@login_required
def get_tasks_progress():
    """Получить прогресс выполнения задач"""
    from sqlalchemy import func
    from datetime import timedelta
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Статистика по статусам
    status_counts = db.session.query(
        Task.status,
        func.count(Task.id)
    ).filter(Task.user_id == current_user.id).group_by(Task.status).all()
    
    status_dict = {s[0]: s[1] for s in status_counts}
    
    # Завершённые за неделю по дням
    weekly_completed = db.session.query(
        func.date(Task.completed_at),
        func.count(Task.id)
    ).filter(
        Task.user_id == current_user.id,
        Task.status == 'completed',
        Task.completed_at >= week_ago
    ).group_by(func.date(Task.completed_at)).all()
    
    weekly_dict = {str(d[0]): d[1] for d in weekly_completed}
    
    # Заполняем пропущенные дни
    weekly_data = []
    for i in range(7):
        day = (today - timedelta(days=6-i)).isoformat()
        weekly_data.append({
            'date': day,
            'completed': weekly_dict.get(day, 0)
        })
    
    # Статистика по приоритетам
    priority_stats = db.session.query(
        Task.priority,
        Task.status,
        func.count(Task.id)
    ).filter(Task.user_id == current_user.id).group_by(Task.priority, Task.status).all()
    
    priority_dict = {}
    for p, s, c in priority_stats:
        if p not in priority_dict:
            priority_dict[p] = {'total': 0, 'completed': 0}
        priority_dict[p]['total'] += c
        if s == 'completed':
            priority_dict[p]['completed'] += c
    
    return jsonify({
        'status': {
            'pending': status_dict.get('pending', 0),
            'in_progress': status_dict.get('in_progress', 0),
            'completed': status_dict.get('completed', 0)
        },
        'weekly': weekly_data,
        'by_priority': priority_dict,
        'completion_rate': round(
            status_dict.get('completed', 0) / max(sum(status_dict.values()), 1) * 100, 1
        )
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
