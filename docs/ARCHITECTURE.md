# Архитектура системы

## Сервисы

1. **TG Bot Gateway** (Aiogram)
   - Обработка всех сообщений от пользователей
   - Регистрация, показ анкет, лайки/дизлайки, мэтчи
   - Получение уведомлений от Matching Service

2. **Profile Service** (FastAPI)
   - CRUD анкет (возраст, пол, интересы, город, фото)
   - Хранение и отдача фотографий через MinIO

3. **Rating & Matching Service** (FastAPI)
   - Обработка лайков, расчёт матчей, поведенческий и комбинированный рейтинг
   - Background tasks (пересчёт рейтингов, подготовка очередей рекомендаций)

4. **Data & Storage Layer**
   - **PostgreSQL** - Основная БД
   - **Redis** - Кэширование предварительно отранжированных списков анкет
   - **MinIO** - Хранение фотографий пользователей

## Схема архитектуры системы

```mermaid
flowchart TD
    TG["Telegram Client"] <--> Bot["Aiogram"]
    
    subgraph Backend ["FastAPI Services"]
        Profile["Profile Service"]
        Matching["Matching & Rating Service"]
    end
    
    subgraph Storage ["Data & Storage"]
        PG[("PostgreSQL")]
        Redis[("Redis")]
        MinIO[("MinIO")]
    end

    Bot --> Profile
    Profile --> Bot
    
    Bot --> Matching
    Matching --> Bot
    
    Profile <--> PG
    Profile --> MinIO
    Matching <--> PG
    Matching <--> Redis
