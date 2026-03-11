from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, BIGINT, UUID as UUIDType
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())

class UserPreference(Base):
    __tablename__ = 'user_preferences'

    user_id = Column(UUID, ForeignKey('users.id'), primary_key=True)
    theme = Column(String(20), default='light')
    language = Column(String(5), default='ru')
    notifications_enabled = Column(Boolean, default=True)

class Building(Base):
    __tablename__ = 'buildings'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    address = Column(Text)

class Room(Base):
    __tablename__ = 'rooms'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    building_id = Column(UUID, ForeignKey('buildings.id'), nullable=False)
    name = Column(String(100), nullable=False)
    floor = Column(Integer, nullable=False)
    plan_image_url = Column(String(512))

class RoomPhysicalParams(Base):
    __tablename__ = 'room_physical_params'

    id = Column(Integer, primary_key=True)
    room_id = Column(UUID, ForeignKey('rooms.id'), unique=True, nullable=False)
    volume_m3 = Column(Float)
    thermal_conductivity = Column(Float)

class SensorType(Base):
    __tablename__ = 'sensor_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    unit = Column(String(10))

class Sensor(Base):
    __tablename__ = 'sensors'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    room_id = Column(UUID, ForeignKey('rooms.id'), nullable=False)
    type_id = Column(Integer, ForeignKey('sensor_types.id'), nullable=False)
    model_name = Column(String(100))
    pos_x = Column(Float)
    pos_y = Column(Float)
    status = Column(String(20), default='active')

class SensorCalibration(Base):
    __tablename__ = 'sensor_calibrations'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    sensor_id = Column(UUID, ForeignKey('sensors.id'), nullable=False)
    calibration_date = Column(DateTime, nullable=False)
    next_calibration_date = Column(DateTime, nullable=False)
    technician_name = Column(String(255))

class SensorMeasurement(Base):
    __tablename__ = 'sensor_measurements'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    sensor_id = Column(UUID, ForeignKey('sensors.id'), nullable=False)
    value = Column(Float, nullable=False)
    measured_at = Column(DateTime, nullable=False, default=func.now())

class MLModel(Base):
    __tablename__ = 'ml_models'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    name = Column(String(100), nullable=False)
    file_path = Column(String(512), nullable=False)
    trained_at = Column(DateTime, default=func.now())

class TemperaturePrediction(Base):
    __tablename__ = 'temperature_predictions'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    room_id = Column(UUID, ForeignKey('rooms.id'), nullable=False)
    model_id = Column(UUID, ForeignKey('ml_models.id'), nullable=False)
    predicted_value = Column(Float, nullable=False)
    prediction_for_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())

class EventType(Base):
    __tablename__ = 'event_types'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    severity = Column(String(20))

class SystemEvent(Base):
    __tablename__ = 'system_events'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    type_id = Column(Integer, ForeignKey('event_types.id'), nullable=False)
    room_id = Column(UUID, ForeignKey('rooms.id'))
    sensor_id = Column(UUID, ForeignKey('sensors.id'))
    message = Column(Text)
    created_at = Column(DateTime, default=func.now())

class IncidentTicket(Base):
    __tablename__ = 'incident_tickets'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    event_id = Column(UUID, ForeignKey('system_events.id'), unique=True, nullable=False)
    status = Column(String(20), default='new')
    operator_id = Column(UUID, ForeignKey('users.id'))
    resolved_at = Column(DateTime)
    updated_at = Column(DateTime, default=func.now())

class SystemSetting(Base):
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=func.now())

class MLModelConfig(Base):
    __tablename__ = 'ml_model_configs'

    id = Column(UUID, primary_key=True, default=func.gen_random_uuid())
    model_id = Column(UUID, ForeignKey('ml_models.id'), nullable=False)
    room_id = Column(UUID, ForeignKey('rooms.id'), nullable=False)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class ThresholdConfig(Base):
    __tablename__ = 'threshold_configs'

    id = Column(Integer, primary_key=True)
    sensor_type_id = Column(Integer, ForeignKey('sensor_types.id'), nullable=False)
    room_id = Column(UUID, ForeignKey('rooms.id'))
    min_value = Column(Float)
    max_value = Column(Float)
    alert_enabled = Column(Boolean, default=True)

class FeatureFlag(Base):
    __tablename__ = 'feature_flags'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=False)
    description = Column(Text)

class SystemLog(Base):
    __tablename__ = 'system_logs'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(UUID, ForeignKey('users.id'))
    action = Column(String(255), nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime, default=func.now())