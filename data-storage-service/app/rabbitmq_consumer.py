import json
import logging
import os
import pika
from pika.adapters.blocking_connection import BlockingChannel
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from . import crud, schemas

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

class RabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='sensor_data')
            logger.info("Connected to RabbitMQ for consuming")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

    def on_message(self, ch: BlockingChannel, method, properties, body):
        try:
            data = json.loads(body)
            sensor_id = data.get("sensor_id")
            temp = data.get("temperature")
            hum = data.get("humidity")
            
            db = SessionLocal()
            try:
                # В реальном приложении мы бы доставали type_id из базы.
                # Пока что мы сохраняем просто как float значения. БД позволяет сохранить только одно значение в value.
                # Если датчик прислал и temp и hum, сохраняем как два независимых замера от одного sensor_id
                # Но в схеме DB `value` это float, а `type_id` находится в таблице `sensors`.
                # Поэтому в идеале sensor_id должен быть привязан к конкретному типу.
                # На текущем этапе (в рамках плана) мы просто запишем обе метрики как отдельные замеры для этого sensor_id
                
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                
                if temp is not None:
                    measurement = schemas.SensorMeasurementCreate(
                        sensor_id=sensor_id,
                        value=float(temp),
                        measured_at=now
                    )
                    crud.create_sensor_measurement(db=db, measurement=measurement)
                    
                if hum is not None:
                    measurement = schemas.SensorMeasurementCreate(
                        sensor_id=sensor_id,
                        value=float(hum),
                        measured_at=now
                    )
                    crud.create_sensor_measurement(db=db, measurement=measurement)
                    
                logger.info(f"Saved data for sensor {sensor_id}")
            except Exception as e:
                logger.error(f"Error saving to DB: {e}")
            finally:
                db.close()
                
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError:
            logger.error("Failed to decode message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        if not self.channel:
            self.connect()
        if self.channel:
            self.channel.basic_consume(queue='sensor_data', on_message_callback=self.on_message)
            try:
                self.channel.start_consuming()
            except KeyboardInterrupt:
                self.channel.stop_consuming()
            self.connection.close()
