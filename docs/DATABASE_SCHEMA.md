# Схема базы данных

## Основные таблицы

* **users** — основная информация о пользователе из Telegram
  - id — первичный ключ
  - telegram_id — уникальный ID пользователя из Telegram
  - username — username в Telegram
  - first_name — имя пользователя
  - last_name — фамилия пользователя
  - created_at — дата регистрации
  - is_active — флаг активности аккаунта

* **profiles** — полная анкета пользователя
  - id — первичный ключ
  - user_id — ссылка на таблицу users (один к одному)
  - age — возраст
  - gender — пол (male / female / other)
  - city — город проживания
  - bio — описание о себе
  - looking_for — кого ищет (male / female / both)
  - age_min — минимальный желаемый возраст
  - age_max — максимальный желаемый возраст
  - is_active — анкета активна и видна другим
  - created_at — дата создания анкеты
  - updated_at — дата последнего обновления анкеты

* **profile_photos** — фотографии анкеты
  - id — первичный ключ
  - profile_id — ссылка на профиль
  - photo_url — ссылка на файл в MinIO
  - order — порядковый номер фото в анкете
  - created_at — дата загрузки фото

* **ratings** — отдельная таблица для хранения рейтингов
  - id — первичный ключ
  - profile_id — ссылка на профиль
  - primary_score — первичный рейтинг
  - behavioral_score — поведенческий рейтинг
  - final_score — итоговый комбинированный рейтинг
  - last_calculated_at — дата и время последнего пересчёта

* **likes** — действия лайк / пропуск
  - id — первичный ключ
  - from_profile_id — кто поставил лайк/пропуск
  - to_profile_id — кому поставили
  - is_like — True = лайк, False = пропуск
  - created_at — дата и время действия

* **matches** — взаимные лайки (мэтчи)
  - id — первичный ключ
  - profile1_id — первый участник мэтча
  - profile2_id — второй участник мэтча
  - created_at — дата создания мэтча

* **referrals** — реферальная система
  - id — первичный ключ
  - referrer_id — кто пригласил друга
  - referred_id — кого пригласили
  - created_at — дата приглашения
  - bonus_given — был ли выдан бонус пригласившему

## ER-диаграмма (Mermaid)

```mermaid
erDiagram
    USERS ||--o{ PROFILES : "has"
    PROFILES ||--o{ PROFILE_PHOTOS : "has many"
    PROFILES ||--o{ RATINGS : "has one"
    PROFILES ||--o{ LIKES : "sent"
    PROFILES ||--o{ LIKES : "received"
    LIKES ||--o{ MATCHES : "creates"
    USERS ||--o{ REFERRALS : "invited"
