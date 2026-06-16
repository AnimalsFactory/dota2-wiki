from flask import Flask, render_template, request, session, redirect, url_for, abort, flash
import json
import uuid
import os
import database
from werkzeug.security import check_password_hash
from whitenoise import WhiteNoise

from data.heroes_data import HEROES_LIST, get_hero_description, get_hero_image_name
from data.hero_abilities import HERO_ABILITIES
from data.content_data import CONTENT
from data.facts_data import get_all_facts
from data.quiz_questions import QUESTIONS, get_questions_by_category, is_answer_correct

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dota2_secret_key_2026')

# Настройка Whitenoise для раздачи статики
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

database.init_db()

# ---------- КОНСТАНТЫ ВИКТОРИНЫ ----------
QUESTIONS_PER_QUIZ = 10
EASY_COUNT = 4
MEDIUM_COUNT = 3
HARD_COUNT = 3

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def get_hero_image(hero_name, size="lg"):
    formatted = get_hero_image_name(hero_name)
    base_url = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes"
    return f"{base_url}/{formatted}.png"

def get_user_data():
    if 'user_id' in session:
        return database.get_user_by_id(session['user_id'])
    return None

def save_note(section, text, hero_name=None):
    if 'user_id' in session:
        database.add_user_note(session['user_id'], section, text, hero_name)
    else:
        notes = session.get('notes', [])
        from datetime import datetime
        notes.append({
            'text': text,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'section': section,
            'hero_name': hero_name
        })
        session['notes'] = notes
        database.save_session(
            session['guest_id'],
            json.dumps(session.get('history', [])),
            json.dumps(notes)
        )

# ---------- МАРШРУТЫ ----------
@app.route('/')
def index():
    if 'guest_id' not in session:
        session['guest_id'] = str(uuid.uuid4())
        session['history'] = []
        session['notes'] = []
    return render_template('index.html', content=CONTENT, user=get_user_data())

@app.route('/section/<section_name>')
def section(section_name):
    if section_name not in CONTENT:
        return redirect(url_for('index'))
    if section_name == "heroes":
        return render_template('hero_list.html',
                               section=CONTENT[section_name],
                               heroes=HEROES_LIST,
                               get_image_url=get_hero_image,
                               user=get_user_data())
    history = session.get('history', [])
    if section_name not in history:
        history.append(section_name)
        session['history'] = history
        if 'user_id' not in session:
            database.save_session(
                session['guest_id'],
                json.dumps(history),
                json.dumps(session.get('notes', []))
            )
    return render_template('section.html',
                           section=CONTENT[section_name],
                           section_name=section_name,
                           user=get_user_data())

@app.route('/hero/<hero_name>')
def hero_detail(hero_name):
    hero_found = None
    for h in HEROES_LIST:
        if h.lower() == hero_name.lower():
            hero_found = h
            break
    if not hero_found:
        abort(404)
    history = session.get('history', [])
    if "heroes" not in history:
        history.append("heroes")
        session['history'] = history
        if 'user_id' not in session:
            database.save_session(
                session['guest_id'],
                json.dumps(history),
                json.dumps(session.get('notes', []))
            )
    official_url = f"https://www.dota2.com/hero/{hero_found.lower().replace(' ', '-')}"
    description = get_hero_description(hero_found)
    image_url = get_hero_image(hero_found, "lg")
    abilities = HERO_ABILITIES.get(hero_found, [])
    is_fav = False
    if 'user_id' in session:
        is_fav = database.is_favorite(session['user_id'], hero_found)
    return render_template('hero_detail.html',
                           hero_name=hero_found,
                           description=description,
                           official_url=official_url,
                           image_url=image_url,
                           abilities=abilities,
                           is_favorite=is_fav,
                           user=get_user_data())

@app.route('/guest_cabinet')
def guest_cabinet():
    user = get_user_data()
    if user:
        favorites = database.get_favorites(user['id'])
        notes = database.get_user_notes(user['id'])
        history = session.get('history', [])
        section_names = {
            "history": "История Dota",
            "heroes": "Герои Dota 2",
            "guide": "Инструкция",
            "quiz": "Викторина",
            "facts": "Интересные факты"
        }
        history_with_names = [(item, section_names.get(item, item)) for item in history]
        return render_template('profile.html',
                               user=user,
                               history=history_with_names,
                               favorites=favorites,
                               notes=notes)
    else:
        history = session.get('history', [])
        notes = session.get('notes', [])
        section_names = {
            "history": "История Dota",
            "heroes": "Герои Dota 2",
            "guide": "Инструкция",
            "quiz": "Викторина",
            "facts": "Интересные факты"
        }
        history_with_names = [(item, section_names.get(item, item)) for item in history]
        return render_template('guest_cabinet.html',
                               history=history_with_names,
                               notes=notes,
                               user=None)

@app.route('/add_note', methods=['POST'])
def add_note():
    note = request.form.get('note', '').strip()
    section = request.form.get('section', 'general')
    hero_name = request.form.get('hero_name', None)
    if note:
        save_note(section, note, hero_name)
    return redirect(request.referrer or url_for('index'))

@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' in session:
        database.delete_user_note(note_id, session['user_id'])
    return redirect(request.referrer or url_for('guest_cabinet'))

@app.route('/toggle_favorite/<hero_name>', methods=['POST'])
def toggle_favorite(hero_name):
    if 'user_id' not in session:
        flash('Войдите, чтобы добавлять героев в избранное', 'warning')
        return redirect(url_for('login'))
    user_id = session['user_id']
    if database.is_favorite(user_id, hero_name):
        database.remove_favorite(user_id, hero_name)
    else:
        database.add_favorite(user_id, hero_name)
    return redirect(request.referrer or url_for('hero_detail', hero_name=hero_name))

# ---------- ВИКТОРИНА ----------
@app.route('/quiz')
def quiz():
    if 'quiz_questions' in session:
        questions = session['quiz_questions']
        return render_template('quiz.html', questions=questions, user=get_user_data())
    return render_template('quiz.html', show_rules=True, user=get_user_data())

@app.route('/quiz/start', methods=['POST'])
def quiz_start():
    import random
    easy = get_questions_by_category('easy')
    medium = get_questions_by_category('medium')
    hard = get_questions_by_category('hard')
    selected = []
    selected.extend(random.sample(easy, min(EASY_COUNT, len(easy))))
    selected.extend(random.sample(medium, min(MEDIUM_COUNT, len(medium))))
    selected.extend(random.sample(hard, min(HARD_COUNT, len(hard))))
    random.shuffle(selected)
    session['quiz_questions'] = selected
    return redirect(url_for('quiz'))

@app.route('/quiz_result', methods=['POST'])
def quiz_result():
    questions = session.get('quiz_questions', [])
    if not questions:
        return redirect(url_for('quiz'))
    score = 0
    results = []
    for idx, q in enumerate(questions):
        user_ans = request.form.get(f'q{idx}', '').strip()
        correct = is_answer_correct(user_ans, q['answers'])
        if correct:
            score += 1
        results.append({
            'question': q['question'],
            'user_answer': user_ans,
            'correct': correct,
            'correct_answers': q['answers'][0] if q['answers'] else ''
        })
    total = len(questions)
    result_text = f"🎯 Результат викторины: {score} из {total} правильных ответов"
    if 'user_id' in session:
        database.add_user_note(session['user_id'], 'quiz', result_text)
    else:
        notes = session.get('notes', [])
        from datetime import datetime
        notes.append({
            'text': result_text,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'section': 'quiz',
            'hero_name': None
        })
        session['notes'] = notes
        database.save_session(
            session['guest_id'],
            json.dumps(session.get('history', [])),
            json.dumps(notes)
        )
    session.pop('quiz_questions', None)
    return render_template('quiz.html', quiz_result=score, total=total, results=results, user=get_user_data())

@app.route('/facts')
def facts():
    facts_list = get_all_facts()
    return render_template('facts.html', facts=facts_list, user=get_user_data())

# ---------- АУТЕНТИФИКАЦИЯ ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if not username or not password:
            flash('Заполните все поля', 'danger')
        elif password != confirm:
            flash('Пароли не совпадают', 'danger')
        elif len(password) < 6:
            flash('Пароль должен быть не менее 6 символов', 'danger')
        else:
            user_id = database.create_user(username, password)
            if user_id:
                flash('Регистрация успешна! Теперь войдите.', 'success')
                if 'guest_id' in session:
                    database.migrate_guest_data(session['guest_id'], user_id)
                    session.pop('guest_id', None)
                    session.pop('history', None)
                    session.pop('notes', None)
                return redirect(url_for('login'))
            else:
                flash('Пользователь с таким именем уже существует', 'danger')
    return render_template('register.html', user=get_user_data())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = database.get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            if 'history' not in session:
                session['history'] = []
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html', user=get_user_data())

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/profile/update_theme', methods=['POST'])
def update_theme():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    theme = request.form.get('theme', 'dark')
    if theme in ('dark', 'light'):
        database.update_user_theme(session['user_id'], theme)
    return redirect(request.referrer or url_for('guest_cabinet'))

# ---------- ОБРАБОТЧИКИ ОШИБОК ----------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)