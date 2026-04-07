# LeoMadzhBot — Telegram-бот для настоящих маджей

## Описание проекта
Telegram-бот для дейтинга.  
Пользователи регистрируются через `/start`, заполняют анкету, загружают фото и получают персонализированные рекомендации.  

## Tech Stack
- **Python 3.11+**
- **Aiogram 3.x** — асинхронный Telegram Bot
- **FastAPI** 
- **PostgreSQL** + SQLAlchemy 2.0 + Alembic
- **Redis** — кэширование предранжированных анкет
- **MinIO** — S3-совместимое хранилище фотографий
- **Docker**

## Этапы разработки
[docs/ROADMAP.md](docs/ROADMAP.md).

## Архитектура проекта
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Схема базы данных
[docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md).

## Как запустить (локально)
```bash
docker-compose up --build
