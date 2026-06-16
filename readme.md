# 🎮 Dota 2 Wiki — Справочник по игре

[![Render](https://img.shields.io/badge/Render-Deployed-brightgreen)](https://dota2-factory.onrender.com/)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-blue)](https://github.com/AnimalsFactory/dota2-wiki)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-red)](https://flask.palletsprojects.com/)

**Учебный MVP-проект** — полноценный справочник по вселенной Dota 2.  
Создан на **Flask** с использованием **SQLite**, с регистрацией пользователей, личным кабинетом, викториной и интересными фактами.

🌐 **Живой пример**: [https://dota2-factory.onrender.com/](https://dota2-factory.onrender.com/)

---

## 📋 Содержание

- [🎯 Функциональность](#-функциональность)
- [🛠 Технологии](#-технологии)
- [🚀 Быстрый старт (локально)](#-быстрый-старт-локально)
- [📁 Структура проекта](#-структура-проекта)
- [📦 Деплой на Render](#-деплой-на-render)
- [⏰ Keep-Alive (борьба со сном)](#-keep-alive-борьба-со-сном)
- [👨‍💻 Автор](#-автор)

---

## 🎯 Функциональность

- **Главная страница** — карточки разделов, баннер, двухколоночный блок.
- **Разделы**:
  - 📜 История Dota — от мода до современности.
  - ⚔️ Герои — список всех 126 героев с карточками и страницами с описанием, способностями и изображениями.
  - 📖 Инструкция — пошаговый план для новичков, видеоуроки, полезные ссылки.
  - 📌 Интересные факты — 50 фактов об игре, лоре, киберспорте и разработке.
- **🧠 Викторина** — 10 случайных вопросов (4 лёгких, 3 средних, 3 сложных) с гибкой проверкой ответов (регистр, раскладка, опечатки). Результаты сохраняются в заметки.
- **👤 Личный кабинет**:
  - Регистрация и вход с хешированием паролей.
  - История посещений.
  - Заметки (добавление/удаление).
  - Избранные герои (добавление/удаление).
  - Сохранение темы (светлая/тёмная) в базе данных.
- **🌓 Тёмная/светлая тема** — переключается кнопкой, сохраняется в `localStorage` и в профиле пользователя.
- **📱 Адаптивный дизайн** — корректно отображается на ПК, планшетах и телефонах.

---

## 🛠 Технологии

- **Backend**: Flask (Python 3.12), SQLite, Werkzeug (хеширование паролей).
- **Frontend**: HTML5, CSS3 (кастомный, с переменными для тем), Jinja2 (шаблонизатор).
- **Деплой**: Render (бесплатный хостинг), Gunicorn (WSGI-сервер), Whitenoise (раздача статики).
- **Keep-Alive**: cron-job.org (пинг каждые 5 минут).
- **Версионирование**: Git, GitHub.

---

## 🚀 Быстрый старт (локально)

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/AnimalsFactory/dota2-wiki.git
   cd dota2-wiki
Создайте виртуальное окружение (рекомендуется):

bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
Установите зависимости:

bash
pip install -r requirements.txt
Запустите приложение:

bash
python app.py
По умолчанию сервер запустится на http://localhost:5001

Откройте в браузере и пользуйтесь!

📁 Структура проекта
text
dota2-wiki/
├── app.py                     # Главный файл приложения
├── database.py                # Работа с SQLite (пользователи, заметки, избранное)
├── requirements.txt           # Зависимости Python
├── runtime.txt                # Версия Python для Render
├── .gitignore                 # Исключаемые файлы
├── README.md                  # Этот файл
├── data/                      # Модули с данными
│   ├── content_data.py        # Тексты разделов
│   ├── heroes_data.py         # Список героев, описания, имена файлов
│   ├── hero_abilities.py      # Способности героев
│   ├── facts_data.py          # 50 фактов
│   └── quiz_questions.py      # 50 вопросов для викторины
├── static/                    # Статические файлы
│   ├── css/
│   │   └── style.css          # Все стили (тёмная/светлая тема)
│   └── images/                # Картинки для разделов, логотип, фон
├── templates/                 # HTML-шаблоны (Jinja2)
│   ├── base.html
│   ├── index.html
│   ├── section.html
│   ├── hero_list.html
│   ├── hero_detail.html
│   ├── quiz.html
│   ├── facts.html
│   ├── guest_cabinet.html
│   ├── profile.html
│   ├── register.html
│   ├── login.html
│   ├── 404.html
│   └── 500.html
└── data/                      # Создаётся автоматически при запуске
    └── dota2.db               # SQLite база данных
📦 Деплой на Render
Проект успешно развёрнут на Render (бесплатный тариф).
Конфигурация:

Build Command: pip install -r requirements.txt

Start Command: gunicorn app:app

Python Version: 3.12.9 (задано в runtime.txt)

Статика: обслуживается через Whitenoise

При необходимости вы можете развернуть свой собственный экземпляр, используя ту же конфигурацию.

⏰ Keep-Alive (борьба со сном)
На бесплатном тарифе Render приложение засыпает после 15 минут бездействия.
Для поддержания активности используется cron-job.org — сервис, который отправляет GET-запрос на сайт каждые 5 минут.

Ссылка на задание: cron-job.org

Интервал: */5 * * * *

URL: https://dota2-factory.onrender.com/

Благодаря этому сайт всегда доступен без задержек при первом открытии.

👨‍💻 Автор
AnimalsFactory (MKeynes aka Larry, aka Lester)

GitHub: AnimalsFactory

Проект разработан в учебных целях для создания MVP (минимально жизнеспособного продукта).

🌟 Если вам понравился проект, поставьте звёздочку на GitHub!