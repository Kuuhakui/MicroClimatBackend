# 🌡️ MicroClimat: Система предиктивного поддержания микроклимата

**MicroClimat** — это дипломный проект по разработке системы прецизионного поддержания микроклиматических параметров для объектов критической инфраструктуры. Система построена на микросервисной архитектуре и использует методы машинного обучения для прогнозирования состояния среды.

## 🚀 Обзор системы
Проект представляет собой комплексное решение для мониторинга, управления и предиктивного анализа температуры и влажности. Система обучается на реальных данных и позволяет визуализировать состояние объектов на планах помещений в реальном времени.

## 🛠 Технологический стек
* **Backend:** Python (FastAPI).
* **Frontend:** React.
* **Базы данных:** PostgreSQL (основная), Redis (брокер сообщений и кэш).
* **Хранилище:** MinIO (S3-совместимое хранилище для ML-моделей и файлов).

---

## 🏗 Архитектура микросервисов

Проект состоит из 12 независимых сервисов, каждый из которых отвечает за свой участок бизнес-логики:

| Сервис | Функционал |
| :--- | :--- |
| **`api-gateway`** | Единая точка входа, маршрутизация и авторизация. |
| **`auth-service`** | Управление пользователями, ролями (Администратор/Оператор) и сессиями. |
| **`core-service`** | Центральная логика, настройки ML-моделей и уставок. |
| **`sensor-ingestion`** | Прием и первичная валидация данных с датчиков. |
| **`data-storage`** | Интерфейс взаимодействия с PostgreSQL. |
| **`ml-prediction`** | Прогнозирование параметров и управление жизненным циклом моделей. |
| **`room-management`** | Конфигурация помещений и привязка датчиков к картам. |
| **`notification`** | Анализ аномалий и отправка уведомлений (Email/Push). |
| **`event-log`** | Логирование системных событий и действий пользователей. |
| **`minio-service`** | Работа с объектным хранилищем MinIO. |

---

## 📊 Диаграмма взаимодействия (Mermaid)

mermaid
graph TD
    subgraph Frontend
        UI[MicroClimat Frontend <br> React]
    end

    subgraph Gateway
        APIGW[API Gateway <br> FastAPI]
    end

    subgraph Business_Logic
        CORE[Core Service]
        AUTH[Auth Service]
        ROOM[Room Management]
        ML[ML Prediction]
        NOTIF[Notification Service]
        EVENT[Event Log Service]
    end

    subgraph Data_Handling
        SENSOR[Sensor Ingestion]
        DATA[Data Storage]
        MINIO_SVC[MinIO File Service]
    end

    subgraph Infrastructure
        PG[(PostgreSQL)]
        REDIS[(Redis Broker)]
        MINIO_S3[(MinIO S3)]
    end

    UI -- HTTP/S --> APIGW
    
    APIGW --> AUTH
    APIGW --> CORE
    APIGW --> ROOM
    APIGW --> NOTIF
    APIGW --> EVENT
    APIGW --> DATA

    SENSOR -- Pub --> REDIS
    ML -- Sub --> REDIS
    ML -- Pub --> REDIS
    NOTIF -- Sub --> REDIS

    CORE -- Configs --> ML
    CORE -- Thresholds --> NOTIF
    
    DATA -- Training Data --> ML
    DATA -- SQL --> PG
    EVENT -- SQL --> PG
    ROOM -- SQL --> PG
    AUTH -- SQL --> PG
    
    ML -- Save/Load --> MINIO_SVC
    ROOM -- Images --> MINIO_SVC
    MINIO_SVC -- S3 --> MINIO_S3

  ##  Ключевые возможности
Предиктивный анализ: Предсказание температуры и дообучение моделей на лету.

Учет оборудования: Отслеживание сроков поверки датчиков.

Безопасность: Ролевая модель доступа и централизованный аудит событий.

Гибкость: Хранение планов помещений и конфигураций в облачном хранилище