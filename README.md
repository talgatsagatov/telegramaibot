# AI RIZQ Bot

Telegram-бот агентства **AI RIZQ**: консультирует клиентов по маркетингу через ИИ и принимает заявки на сотрудничество.

---

## Возможности

* **Команда `/start`** — приветствие и главное меню.
* **«Задать вопрос ИИ»** — клиент общается с ИИ-консультантом от лица агентства. Бот помнит контекст последних сообщений в рамках сессии.
* **«Оставить заявку»** — пошаговая форма (имя → телефон → описание → подтверждение). Поддерживает кнопку «Отправить мой номер» и команду `/cancel` на любом шаге.
* **Уведомление администратора** — при поступлении новой заявки менеджер получает сообщение с кнопками «Взять в работу» / «Закрыть».
* **Защита от перерасхода** — лимит 10 запросов к ИИ в сутки на одного пользователя.

---

## Технологический стек

| Компонент | Версия | Назначение |
|---|---|---|
| Python | 3.11+ | Async-программирование |
| aiogram | 3.13.x | Telegram Bot API |
| SQLAlchemy | 2.0.x | ORM, async-режим |
| aiosqlite | 0.20.x | SQLite драйвер |
| openai | 1.54.x | SDK для OpenRouter API |
| pydantic-settings | 2.6.x | Конфигурация из `.env` |
| python-dotenv | 1.0.x | Загрузка переменных окружения |

---

## Структура проекта

```
.
├── .env.example              # Шаблон переменных окружения
├── .gitignore
├── README.md
├── ARCHITECTURE.md           # Описание модулей и потоков данных
├── requirements.txt
└── app/
    ├── main.py               # Точка входа (python -m app.main)
    ├── config.py             # Загрузка конфигурации
    ├── database/
    │   ├── engine.py         # AsyncEngine, sessionmaker, init_db
    │   ├── models.py         # Lead, UsageLimit
    │   └── crud.py           # CRUD-операции
    ├── handlers/
    │   ├── start.py          # /start, /cancel, кнопка «В меню»
    │   ├── ai_dialog.py      # Ветка ИИ-консультации
    │   ├── lead_form.py      # FSM-форма заявки
    │   └── admin.py          # Уведомления и статусы заявок
    ├── keyboards/
    │   ├── inline.py         # Inline-клавиатуры
    │   └── reply.py          # Reply-клавиатура (запрос контакта)
    ├── services/
    │   ├── openai_client.py  # Клиент OpenRouter
    │   └── rate_limiter.py   # Лимит запросов
    ├── states/
    │   └── fsm_states.py     # FSM-состояния
    └── utils/
        ├── validators.py     # Валидация имени и телефона
        └── texts.py          # Тексты сообщений
```

---

## Установка и запуск

### 1. Требования

* Python 3.11 или новее:
  ```bash
  python --version
  ```

### 2. Получите токены

#### `BOT_TOKEN` — от [@BotFather](https://t.me/BotFather)

1. Напишите `/newbot`.
2. Введите имя и username бота (username должен оканчиваться на `_bot`).
3. Скопируйте токен вида `1234567890:AA...`.

#### `OPENROUTER_API_KEY` — на [openrouter.ai/keys](https://openrouter.ai/keys)

1. Зарегистрируйтесь и создайте ключ.
2. Скопируйте ключ — он понадобится в `.env`.

#### `ADMIN_CHAT_ID` — ваш Telegram user_id

1. Напишите боту [@userinfobot](https://t.me/userinfobot) команду `/start`.
2. Скопируйте значение `Id:`.

### 3. Установите зависимости

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Если PowerShell блокирует активацию, выполните один раз:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Настройте `.env`

```powershell
# Windows
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

Откройте `.env` и заполните:

```ini
BOT_TOKEN=ваш-токен-от-BotFather
OPENROUTER_API_KEY=ваш-ключ-openrouter
ADMIN_CHAT_ID=ваш-telegram-id
OPENROUTER_MODEL=openai/gpt-4o-mini
AGENCY_NAME=AI RIZQ
DATABASE_URL=sqlite+aiosqlite:///bot.db
LOG_LEVEL=INFO
```

> ⚠️ Никогда не коммитьте `.env` в git — файл уже добавлен в `.gitignore`.

### 5. Запустите бота

```bash
python -m app.main
```

При первом запуске создастся `bot.db` и бот начнёт принимать сообщения. Для остановки — `Ctrl+C`.

---

## Проверка работоспособности

1. Откройте чат с ботом → отправьте `/start`.
2. Нажмите **«Задать вопрос ИИ»** → задайте вопрос по маркетингу.
3. Вернитесь в меню → нажмите **«Оставить заявку»** → пройдите все шаги.
4. После подтверждения администратору придёт уведомление с кнопками управления заявкой.

---

## Частые проблемы

| Симптом | Решение |
|---|---|
| `[CONFIG ERROR] Не удалось загрузить настройки` | Проверьте, что в `.env` заполнены `BOT_TOKEN`, `OPENROUTER_API_KEY`, `ADMIN_CHAT_ID`. |
| `TelegramUnauthorizedError` | Неверный `BOT_TOKEN`. Сверьте с тем, что прислал BotFather. |
| Бот не отвечает на `/start` | Убедитесь, что `python -m app.main` запущен и нет другого активного экземпляра бота. |
| ИИ возвращает 401 | Неверный `OPENROUTER_API_KEY` или недостаточно средств на счёте. |
| Уведомление админу не приходит | `ADMIN_CHAT_ID` указан неверно или администратор ни разу не писал боту первым. |
| Кириллица ломается в логах (Windows) | Выполните `chcp 65001` в PowerShell перед запуском. |

---

## Команды бота

| Команда | Действие |
|---|---|
| `/start` | Главное меню (сбрасывает текущее состояние) |
| `/cancel` | Отменить заполнение формы |
