
# Схема Базы Данных (PostgreSQL) - 3NF

## 1. Пользователи и Доступ

### Таблица: `roles`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | ID роли |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Имя роли (admin, operator) |

### Таблица: `users`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK, DEFAULT gen_random_uuid() | ID пользователя |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL | Логин |
| `password_hash` | VARCHAR(255) | NOT NULL | Хеш пароля |
| `role_id` | INTEGER | FK (roles.id), NOT NULL | Ссылка на роль |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Дата создания |

### Таблица: `user_preferences`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | UUID | PK, FK (users.id) | ID пользователя |
| `theme` | VARCHAR(20) | DEFAULT 'light' | Тема оформления |
| `language` | VARCHAR(5) | DEFAULT 'ru' | Язык интерфейса |
| `notifications_enabled` | BOOLEAN | DEFAULT TRUE | Включены ли уведомления |

## 2. Пространственная Структура

### Таблица: `buildings`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID здания |
| `name` | VARCHAR(255) | NOT NULL | Название здания |
| `address` | TEXT | | Адрес |

### Таблица: `rooms`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID помещения |
| `building_id` | UUID | FK (buildings.id), NOT NULL | Ссылка на здание |
| `name` | VARCHAR(100) | NOT NULL | Название/номер комнаты |
| `floor` | INTEGER | NOT NULL | Этаж |
| `plan_image_url` | VARCHAR(512) | | Ссылка на план в MinIO |

### Таблица: `room_physical_params`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | ID записи |
| `room_id` | UUID | FK (rooms.id), UNIQUE | Ссылка на помещение |
| `volume_m3` | FLOAT | | Объем в м3 |
| `thermal_conductivity` | FLOAT | | Теплопроводность стен |

## 3. Оборудование и Датчики

### Таблица: `sensor_types`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | ID типа |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Тип (temperature, humidity, CO2) |
| `unit` | VARCHAR(10) | | Единица измерения (C, %, ppm) |

### Таблица: `sensors`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID датчика |
| `room_id` | UUID | FK (rooms.id), NOT NULL | Где установлен |
| `type_id` | INTEGER | FK (sensor_types.id), NOT NULL | Ссылка на тип |
| `model_name` | VARCHAR(100) | | Модель устройства |
| `pos_x` | FLOAT | | Координата X на плане (%) |
| `pos_y` | FLOAT | | Координата Y на плане (%) |
| `status` | VARCHAR(20) | DEFAULT 'active' | Статус (active, offline, maintenance) |

### Таблица: `sensor_calibrations`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID поверки |
| `sensor_id` | UUID | FK (sensors.id), NOT NULL | Ссылка на датчик |
| `calibration_date` | DATE | NOT NULL | Дата текущей поверки |
| `next_calibration_date` | DATE | NOT NULL | Дата следующей поверки |
| `technician_name` | VARCHAR(255) | | Кто проводил |

## 4. Данные и Прогнозы

### Таблица: `sensor_measurements`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGSERIAL | PK | ID замера |
| `sensor_id` | UUID | FK (sensors.id), NOT NULL | Источник |
| `value` | FLOAT | NOT NULL | Значение |
| `measured_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Время замера |

### Таблица: `ml_models`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID модели |
| `name` | VARCHAR(100) | NOT NULL | Имя модели (версия) |
| `file_path` | VARCHAR(512) | NOT NULL | Путь к .pkl/.onnx в MinIO |
| `trained_at` | TIMESTAMP | DEFAULT NOW() | Дата обучения |

### Таблица: `temperature_predictions`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGSERIAL | PK | ID прогноза |
| `room_id` | UUID | FK (rooms.id), NOT NULL | Помещение |
| `model_id` | UUID | FK (ml_models.id), NOT NULL | Какая модель считала |
| `predicted_value` | FLOAT | NOT NULL | Прогноз |
| `prediction_for_time` | TIMESTAMP | NOT NULL | На какое время прогноз |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Когда сделан прогноз |

## 5. События и Логирование

### Таблица: `event_types`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | ID типа |
| `code` | VARCHAR(50) | UNIQUE, NOT NULL | Код (exceed_temp, low_battery, calib_due) |
| `severity` | VARCHAR(20) | | info, warning, critical |

### Таблица: `system_events`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID события |
| `type_id` | INTEGER | FK (event_types.id), NOT NULL | Тип события |
| `room_id` | UUID | FK (rooms.id), NULLABLE | Ссылка на помещение |
| `sensor_id` | UUID | FK (sensors.id), NULLABLE | Ссылка на датчик |
| `message` | TEXT | | Сообщение |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Время возникновения |

### Таблица: `incident_tickets`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID инцидента |
| `event_id` | UUID | FK (system_events.id), UNIQUE | Ссылка на событие |
| `status` | VARCHAR(20) | DEFAULT 'new' | new, in_progress, resolved |
| `operator_id` | UUID | FK (users.id), NULLABLE | Кто взял в работу |
| `resolved_at` | TIMESTAMP | | Время закрытия |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Время последнего обновления |

## 6. Системные настройки и Конфигурация (Core Service)

### Таблица: `system_settings`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | ID настройки |
| `key` | VARCHAR(100) | UNIQUE, NOT NULL | Ключ настройки |
| `value` | JSONB | NOT NULL | Значение (JSON) |
| `description` | TEXT | | Описание |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Дата обновления |

### Таблица: `ml_model_configs`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | ID конфигурации |
| `model_id` | UUID | FK (ml_models.id), NOT NULL | Ссылка на модель |
| `room_id` | UUID | FK (rooms.id), NOT NULL | Для какого помещения |
| `config` | JSONB | NOT NULL | Конфигурация модели |
| `is_active` | BOOLEAN | DEFAULT FALSE | Активна ли модель |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Дата создания |

### Таблица: `threshold_configs`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | ID порога |
| `sensor_type_id` | INTEGER | FK (sensor_types.id), NOT NULL | Тип датчика |
| `room_id` | UUID | FK (rooms.id), NULLABLE | Для помещения или NULL (глобально) |
| `min_value` | FLOAT | | Мин. значение |
| `max_value` | FLOAT | | Макс. значение |
| `alert_enabled` | BOOLEAN | DEFAULT TRUE | Оповещение включено |

### Таблица: `feature_flags`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | ID флага |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Имя функции |
| `is_enabled` | BOOLEAN | DEFAULT FALSE | Статус |
| `description` | TEXT | | Описание |

### Таблица: `system_logs`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGSERIAL | PK | ID лога |
| `user_id` | UUID | FK (users.id), NULLABLE | Кто внес изменения |
| `action` | VARCHAR(255) | NOT NULL | Действие |
| `details` | JSONB | | Детали (старое/новое значение) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Время |
