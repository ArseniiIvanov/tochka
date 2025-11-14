# Trading Platform API


## Архитектура


- **API Layer** (`app/api/`) - HTTP endpoints и валидация запросов
- **Service Layer** (`app/services/`) - Бизнес-логика
- **Repository Layer** (`app/repositories/`) - Доступ к данным
- **Models** (`app/models/`) - SQLAlchemy модели
- **Core** (`app/core/`) - Конфигурация, зависимости, утилиты

## Структура проекта

```
app/
├── api/              # API endpoints
│   ├── v1/
│   │   ├── admin.py  # Admin endpoints
│   │   ├── order.py  # Order endpoints
│   │   ├── public.py # Public endpoints
│   │   └── schemas/  # Pydantic schemas
├── core/             # Core functionality
│   ├── config.py     # Configuration
│   ├── database.py   # Database setup
│   ├── dependencies.py # FastAPI dependencies
│   ├── exceptions.py  # Custom exceptions
│   ├── locks.py      # Lock management
│   └── security.py   # JWT security
├── models/           # SQLAlchemy models
├── repositories/     # Data access layer
├── services/         # Business logic layer
└── main.py           # Application entry point
```

## Установка и запуск

### Требования

- Docker и Docker Compose
- Python 3.11+ (для локальной разработки)

### Запуск с Docker

```bash
docker-compose up -d
```

Приложение будет доступно по адресу `http://localhost`

## API Endpoints

### Public Endpoints

- `POST /api/v1/public/register` - Регистрация пользователя
- `GET /api/v1/public/instrument` - Список инструментов
- `GET /api/v1/public/orderbook/{ticker}` - Стакан заявок
- `GET /api/v1/public/transactions/{ticker}` - История транзакций

### Order Endpoints (требуют аутентификации)

- `GET /api/v1/order` - Список ордеров пользователя
- `GET /api/v1/order/{order_id}` - Получить ордер
- `POST /api/v1/order` - Создать ордер
- `DELETE /api/v1/order/{order_id}` - Отменить ордер

### Admin Endpoints (требуют admin прав)

- `POST /api/v1/admin/instrument` - Создать инструмент
- `POST /api/v1/admin/balance/deposit` - Пополнить баланс
- `POST /api/v1/admin/balance/withdraw` - Снять баланс
- `DELETE /api/v1/admin/user/{user_id}` - Удалить пользователя
- `DELETE /api/v1/admin/instrument/{ticker}` - Удалить инструмент

### User Endpoints (требуют аутентификации)

- `GET /api/v1/balance` - Получить баланс пользователя

## Аутентификация

Все защищенные endpoints требуют JWT токен в заголовке:

```
Authorization: TOKEN <your_jwt_token>
```

Токен получается при регистрации пользователя через `/api/v1/public/register`

## Технологии

- FastAPI - веб-фреймворк
- SQLAlchemy 2.0 - ORM
- Alembic - миграции
- Pydantic - валидация данных
- PostgreSQL - база данных
- Docker - контейнеризация
- Nginx - reverse proxy
