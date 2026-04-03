# Схема базы данных

## Основные таблицы

- **users** — Telegram ID, username, created_at
- **profiles** — полная анкета (возраст, пол, город, интересы, bio, is_active)
- **profile_photos** — ссылки на MinIO + порядок фото
- **ratings** — отдельная таблица (profile_id, primary_score, behavioral_score, final_score, last_calculated)
- **likes** — from_user → to_user, created_at, is_mutual
- **matches** — пара пользователей + timestamp
- **chats** — match_id, last_message_at
- **referrals** — реферальная система (кто кого пригласил)

## ER-диаграмма (Mermaid)

```mermaid
erDiagram
    USERS ||--o{ PROFILES : "has"
    PROFILES ||--o{ PROFILE_PHOTOS : "has many"
    PROFILES ||--o{ RATINGS : "has one"
    PROFILES ||--o{ LIKES : "sent"
    PROFILES ||--o{ LIKES : "received"
    LIKES ||--o{ MATCHES : "creates"
    MATCHES ||--o{ CHATS : "has"
    USERS ||--o{ REFERRALS : "invited"
