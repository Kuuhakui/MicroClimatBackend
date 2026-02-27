MicroClimat: Система предиктивного поддержания микроклимата
MicroClimat — это высокомасштабируемая микросервисная платформа для мониторинга, управления и прогнозирования параметров микроклимата в помещениях критической инфраструктуры.

Обзор системы
Система не просто собирает данные, но и использует Machine Learning для предсказания динамики температуры. Это позволяет заранее реагировать на изменения, оптимизировать энергопотребление и предотвращать аварийные ситуации.

Ключевой стек технологий
Backend: Python (FastAPI / Пакетная обработка)

Frontend: React (Визуализация реального времени)

Data: PostgreSQL (Персистентность), Redis (Pub/Sub & Cache), MinIO (S3-хранилище моделей)

ML: Scikit-learn / TensorFlow (Предиктивная модель)

Список сервисов

Сервис,Описание
api-gateway,"Точка входа, авторизация и роутинг."
auth-service,"Управление пользователями, ролями (Админ/Оператор) и JWT."
core-service,Управление бизнес-правилами и конфигурациями ML.
sensor-ingestion,Прием данных с датчиков и первичная валидация.
data-storage,Слой абстракции над PostgreSQL для всех сервисов.
ml-prediction,"Прогнозирование на основе данных из Redis, хранение весов в MinIO."
room-management,Карты помещений и привязка датчиков к объектам.
notification,Обработка аномалий и отправка уведомлений (Email/Push).
event-log,Аудит действий операторов и история инцидентов.
minio-service,"Хранилище для артефактов (планы зданий, обученные модели)."

Схема взаимодействия (Mermaid)
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

    Особенности реализации
Real-time мониторинг: Визуализация данных с датчиков на планах помещений.

Контроль поверки: Автоматическое отслеживание сроков калибровки оборудования.

Предиктивный анализ: Система "знает", какая температура будет в помещении через час.

Логирование: Полный аудит событий для обеспечения безопасности инфраструктуры

Как запустить (в разработке)
Клонируйте репозиторий: git clone git@github.com:Kuuhakui/MicroClimatBackend.git

Настройте окружение: cp .env.example .env

Запустите инфраструктуру: docker-compose up -d

