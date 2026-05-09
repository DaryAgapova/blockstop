# МИР ПОЖАРНОЙ БЕЗОПАСНОСТИ — Интернет-магазин

Flask-сайт для магазина противопожарного оборудования (blockstop.ru).

## Стек

- **Python 3.10+** / Flask 3.0
- **PostgreSQL** — основная БД
- **Flask-SQLAlchemy** — ORM
- **Flask-Login** — авторизация (email + пароль)
- **ReportLab** — генерация PDF-счётов
- **Bootstrap 5.3** + FontAwesome 6 — фронтенд

---

## Быстрый старт

### 1. Установка зависимостей

```bash
cd blockstop
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2. База данных PostgreSQL

```sql
-- В psql
CREATE DATABASE fire_safety_db;
CREATE USER fire_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fire_safety_db TO fire_user;
```

### 3. Настройка окружения

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```
SECRET_KEY=сгенерируйте-случайный-ключ-50-символов
DATABASE_URL=postgresql://fire_user:your_password@localhost/fire_safety_db
```

### 4. Заполнение БД начальными данными

```bash
python seed.py
```

Создаёт:
- 18 категорий товаров
- 30+ товаров
- Администратора: `admin@blockstop.ru` / `admin123`

### 5. Запуск

```bash
python run.py
```

Открыть: [http://localhost:5000](http://localhost:5000)

---

## Роли пользователей

| Роль | Доступ |
|------|--------|
| `user` | Каталог, корзина, личный кабинет, скачивание счетов |
| `admin` | Панель управления `/admin/`, управление товарами, заявками, генерация PDF |

---

## Основные маршруты

| URL | Описание |
|-----|----------|
| `/` | Главная страница |
| `/catalog` | Каталог (фильтрация по категориям, поиск) |
| `/product/<id>` | Страница товара |
| `/cart` | Корзина |
| `/checkout` | Оформление заявки (только для авторизованных) |
| `/auth/login` | Вход |
| `/auth/register` | Регистрация |
| `/cabinet/` | Личный кабинет — мои заказы |
| `/cabinet/orders/<id>` | Детали заказа + скачать счёт |
| `/cabinet/profile` | Профиль и реквизиты |
| `/admin/` | Панель управления |
| `/admin/orders` | Все заявки |
| `/admin/orders/<id>` | Детали заявки + формирование счёта |
| `/admin/products` | Товары CRUD |
| `/admin/categories` | Категории CRUD |

---

## Флоу счёта на оплату

```
Клиент → корзина → checkout → Order(status='new')
                                      ↓
Менеджер открывает /admin/orders/<id>
Вводит цены для позиций "по запросу" (если нужно)
Нажимает "Сформировать и отправить счёт"
                                      ↓
PDF генерируется через ReportLab → uploads/invoices/
Order.status = 'invoice_sent'
Order.invoice_pdf_filename = 'invoice_<id>_<timestamp>.pdf'
                                      ↓
Клиент заходит в /cabinet/orders/<id>
Нажимает "Скачать PDF"
```

---

## Структура проекта

```
blockstop/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # User, Category, Product, Order, OrderItem
│   ├── routes/
│   │   ├── main.py          # Каталог, корзина, checkout
│   │   ├── auth.py          # Login, register, logout
│   │   ├── cabinet.py       # Личный кабинет
│   │   └── admin.py         # Панель управления
│   ├── utils/
│   │   └── pdf_generator.py # Генерация PDF-счёта (ReportLab)
│   ├── templates/           # Jinja2-шаблоны
│   └── static/              # CSS, JS, uploads
├── config.py                # Конфигурация + реквизиты компании
├── run.py                   # Точка входа
├── seed.py                  # Начальные данные
├── requirements.txt
└── .env.example
```

---

## PDF-шрифты

При первом запуске генерации счёта скрипт автоматически скачивает шрифты DejaVuSans (поддержка кириллицы) из GitHub в `app/static/fonts/`. Если сервер без интернета — положите `DejaVuSans.ttf` и `DejaVuSans-Bold.ttf` вручную в эту папку.

---

## Деплой (Railway / VPS)

- Установите `gunicorn`: `pip install gunicorn`
- Запуск: `gunicorn -w 4 -b 0.0.0.0:5000 run:app`
- Установите `DATABASE_URL` в переменных среды
- Статику раздаёт Flask (для продакшена — настройте Nginx)
