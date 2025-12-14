"""
Скрипт миграции базы данных
"""
import sqlite3
import os

# Путь к базе данных
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'focus_app.db')


def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # === Миграция таблицы chats ===
    chat_columns = [
        ('description', 'TEXT DEFAULT ""'),
        ('avatar_url', 'VARCHAR(500) DEFAULT ""'),
        ('chat_type', 'VARCHAR(20) DEFAULT "private"'),
        ('is_work_chat', 'BOOLEAN DEFAULT 0'),
        ('is_public', 'BOOLEAN DEFAULT 0'),
        ('username', 'VARCHAR(50)'),
        ('invite_link', 'VARCHAR(100)'),
        ('members_can_send', 'BOOLEAN DEFAULT 1'),
        ('members_can_add', 'BOOLEAN DEFAULT 0'),
        ('members_can_pin', 'BOOLEAN DEFAULT 0'),
        ('slow_mode', 'INTEGER DEFAULT 0'),
        ('owner_id', 'INTEGER'),
    ]
    
    cursor.execute("PRAGMA table_info(chats)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    print("=== Миграция таблицы chats ===")
    for col_name, col_type in chat_columns:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE chats ADD COLUMN {col_name} {col_type}")
                print(f"✓ chats.{col_name}")
            except sqlite3.OperationalError as e:
                print(f"✗ chats.{col_name}: {e}")
    
    # === Создание таблицы yandex_disk_tokens ===
    print("\n=== Создание таблицы yandex_disk_tokens ===")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS yandex_disk_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        print("✓ Таблица yandex_disk_tokens создана")
    except sqlite3.OperationalError as e:
        print(f"- yandex_disk_tokens: {e}")
    
    # === Создание таблицы cloud_files ===
    print("\n=== Создание таблицы cloud_files ===")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cloud_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                cloud_path VARCHAR(500) NOT NULL,
                file_type VARCHAR(50) DEFAULT 'music',
                size INTEGER DEFAULT 0,
                mime_type VARCHAR(100) DEFAULT '',
                title VARCHAR(255) DEFAULT '',
                artist VARCHAR(255) DEFAULT '',
                duration INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        print("✓ Таблица cloud_files создана")
    except sqlite3.OperationalError as e:
        print(f"- cloud_files: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Миграция завершена!")


if __name__ == '__main__':
    migrate()
