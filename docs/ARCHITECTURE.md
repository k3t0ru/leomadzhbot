# Архитектура системы

## Сервисы

1. **Telegram Bot Service** (Aiogram)
   - Обработка всех сообщений и callback’ов от пользователей
   - Регистрация, показ анкет, лайки/дизлайки, чат после мэтча
   - При старте сессии запрашивает 1 анкету по полному пути + предзагружает 10 следующих в Redis

2. **Profile Service** (FastAPI)
   - CRUD анкет (возраст, пол, интересы, город, фото)
   - Хранение и отдача фотографий через MinIO

3. **Rating & Matching Service** (FastAPI + Celery)
   - **Уровень 1** — первичный рейтинг (данные анкеты + полнота профиля)
   - **Уровень 2** — поведенческий рейтинг (лайки, мэтчи, инициация чатов)
   - **Уровень 3** — комбинированный рейтинг (весовая модель)
   - Отдельная таблица `ratings` + периодический пересчёт через Celery Beat
   - Redis-кэш: для каждого пользователя хранится очередь из 10–15 заранее отранжированных анкет

4. **Event Bus (RabbitMQ)**
   - Все события (like, match, message_sent) публикуются в очередь
   - Rating Service и Bot Service подписываются на события и обновляют данные асинхронно

5. **Storage Service (MinIO)**
   - Хранение всех фотографий пользователей

## Схема архитектуры (Mermaid)

```mermaid
flowchart TD
    subgraph "Telegram"
        User[Пользователь Telegram]
        Bot[Telegram Bot Service Aiogram]
    end

    subgraph "Backend"
        API[FastAPI Profile Service]
        Rating[Rating & Matching Service]
        Celery[Celery Beat + Workers]
    end

    subgraph "Хранилища"
        DB[(PostgreSQL)]
        Redis[(Redis Cache)]
        MQ[RabbitMQ]
        MinIO[MinIO S3]
    end

    User --> Bot
    Bot <--> API
    Bot --> MQ
    API --> DB
    API --> MinIO
    Rating <--> DB
    Rating <--> Redis
    Rating <--> MQ
    Celery --> Rating
    Bot <--> Redis
