import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "dota2.db")

def init_db():
    """Инициализация базы данных"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guest_session (
            session_id TEXT PRIMARY KEY,
            history TEXT,
            notes TEXT,
            last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            theme TEXT DEFAULT 'dark'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            hero_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, hero_name),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            section TEXT,
            hero_name TEXT,
            note_text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

# ---------- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ----------
def create_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash, theme FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'password_hash': row[2], 'theme': row[3]}
    return None

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, theme FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'theme': row[2]}
    return None

def update_user_theme(user_id, theme):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET theme = ? WHERE id = ?', (theme, user_id))
    conn.commit()
    conn.close()

# ---------- ИЗБРАННОЕ ----------
def add_favorite(user_id, hero_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO favorites (user_id, hero_name) VALUES (?, ?)', (user_id, hero_name))
    conn.commit()
    conn.close()

def remove_favorite(user_id, hero_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE user_id = ? AND hero_name = ?', (user_id, hero_name))
    conn.commit()
    conn.close()

def get_favorites(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT hero_name FROM favorites WHERE user_id = ? ORDER BY added_at DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def is_favorite(user_id, hero_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM favorites WHERE user_id = ? AND hero_name = ?', (user_id, hero_name))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# ---------- ЗАМЕТКИ ПОЛЬЗОВАТЕЛЯ ----------
def add_user_note(user_id, section, note_text, hero_name=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_notes (user_id, section, hero_name, note_text)
        VALUES (?, ?, ?, ?)
    ''', (user_id, section, hero_name, note_text))
    conn.commit()
    conn.close()

def get_user_notes(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, section, hero_name, note_text, timestamp
        FROM user_notes
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    notes = []
    for row in rows:
        notes.append({
            'id': row[0],
            'section': row[1],
            'hero_name': row[2],
            'text': row[3],
            'timestamp': row[4]
        })
    return notes

def delete_user_note(note_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_notes WHERE id = ? AND user_id = ?', (note_id, user_id))
    conn.commit()
    conn.close()

# ---------- ПЕРЕНОС ГОСТЕВЫХ ДАННЫХ ----------
def migrate_guest_data(session_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT history, notes FROM guest_session WHERE session_id = ?', (session_id,))
    row = cursor.fetchone()
    if not row:
        return
    history_json, notes_json = row[0], row[1]
    if notes_json:
        import json
        notes = json.loads(notes_json)
        for note in notes:
            section = note.get('section', 'general')
            text = note.get('text', '')
            hero_name = note.get('hero_name', None)
            cursor.execute('''
                INSERT INTO user_notes (user_id, section, hero_name, note_text)
                VALUES (?, ?, ?, ?)
            ''', (user_id, section, hero_name, text))
    cursor.execute('DELETE FROM guest_session WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()

# ---------- ГОСТЕВЫЕ ФУНКЦИИ ----------
def save_session(session_id, history, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO guest_session (session_id, history, notes)
        VALUES (?, ?, ?)
    ''', (session_id, history, notes))
    conn.commit()
    conn.close()

def load_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT history, notes FROM guest_session WHERE session_id = ?', (session_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    return "[]", "[]"