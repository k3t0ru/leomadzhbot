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

## Схема архитектуры системы

```mermaid
flowchart LR
    User[Пользователь] --> Bot[Aiogram Bot]
    
    Bot <--> FastAPI[FastAPI Service]
    Bot <--> Redis[Redis Cache]
    Bot --> RabbitMQ[RabbitMQ]
    
    FastAPI <--> PostgreSQL[(PostgreSQL)]
    FastAPI --> MinIO[MinIO]
    
    RabbitMQ --> CeleryWorkers[Celery Workers]
    CeleryBeat[Celery Beat] --> RabbitMQ
    
    CeleryWorkers <--> PostgreSQL
    CeleryWorkers <--> Redis
    
    subgraph Rating
        RatingService[Rating & Matching Logic]
    end
    
    FastAPI <--> RatingService
    RatingService <--> PostgreSQL
