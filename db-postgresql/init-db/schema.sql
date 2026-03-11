CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Пользователи и роли
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(5) DEFAULT 'ru',
    notifications_enabled BOOLEAN DEFAULT TRUE
);

-- 2. Пространственная структура
CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT
);

CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID REFERENCES buildings(id) NOT NULL,
    name VARCHAR(100) NOT NULL,
    floor INTEGER NOT NULL,
    plan_image_url VARCHAR(512)
);

CREATE TABLE room_physical_params (
    id SERIAL PRIMARY KEY,
    room_id UUID UNIQUE REFERENCES rooms(id),
    volume_m3 FLOAT,
    thermal_conductivity FLOAT
);

-- 3. Оборудование и датчики
CREATE TABLE sensor_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    unit VARCHAR(10)
);

CREATE TABLE sensors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES rooms(id) NOT NULL,
    type_id INTEGER REFERENCES sensor_types(id) NOT NULL,
    model_name VARCHAR(100),
    pos_x FLOAT,
    pos_y FLOAT,
    status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE sensor_calibrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sensor_id UUID REFERENCES sensors(id) NOT NULL,
    calibration_date DATE NOT NULL,
    next_calibration_date DATE NOT NULL,
    technician_name VARCHAR(255)
);

-- 4. Данные и прогнозы
CREATE TABLE sensor_measurements (
    id BIGSERIAL PRIMARY KEY,
    sensor_id UUID REFERENCES sensors(id) NOT NULL,
    value FLOAT NOT NULL,
    measured_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    trained_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE temperature_predictions (
    id BIGSERIAL PRIMARY KEY,
    room_id UUID REFERENCES rooms(id) NOT NULL,
    model_id UUID REFERENCES ml_models(id) NOT NULL,
    predicted_value FLOAT NOT NULL,
    prediction_for_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. События и логирование
CREATE TABLE event_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    severity VARCHAR(20)
);

CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_id INTEGER REFERENCES event_types(id) NOT NULL,
    room_id UUID REFERENCES rooms(id),
    sensor_id UUID REFERENCES sensors(id),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE incident_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID UNIQUE REFERENCES system_events(id),
    status VARCHAR(20) DEFAULT 'new',
    operator_id UUID REFERENCES users(id),
    resolved_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Системные настройки
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ml_model_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id) NOT NULL,
    room_id UUID REFERENCES rooms(id) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE threshold_configs (
    id SERIAL PRIMARY KEY,
    sensor_type_id INTEGER REFERENCES sensor_types(id) NOT NULL,
    room_id UUID REFERENCES rooms(id),
    min_value FLOAT,
    max_value FLOAT,
    alert_enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    description TEXT
);

CREATE TABLE system_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(255) NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);