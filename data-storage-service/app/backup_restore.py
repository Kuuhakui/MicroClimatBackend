import json
import logging
import os
from sqlalchemy.orm import Session
from datetime import datetime, date
from uuid import UUID

logger = logging.getLogger(__name__)

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def export_db_to_json(db: Session, file_path: str):
    from .models import Base
    data = {}
    for table in Base.metadata.sorted_tables:
        try:
            records = db.execute(table.select()).mappings().all()
            data[table.name] = [dict(record) for record in records]
        except Exception as e:
            logger.warning(f"Could not export table {table.name}: {e}")
            continue
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=json_serial, indent=2, ensure_ascii=False)
        logger.info(f"Database exported to {file_path}")
    except Exception as e:
        logger.error(f"Failed to write backup JSON: {e}")

def import_json_to_db(db: Session, file_path: str):
    from .models import Base
    if not os.path.exists(file_path):
        logger.info(f"Backup file {file_path} not found. Skipping import.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read backup JSON: {e}")
        return

    for table in Base.metadata.sorted_tables:
        table_data = data.get(table.name, [])
        if not table_data:
            continue
            
        # Check if table already has data
        existing = db.execute(table.select().limit(1)).first()
        if existing is not None:
            logger.info(f"Table {table.name} is not empty. Skipping import for this table.")
            continue
            
        logger.info(f"Restoring {len(table_data)} rows into {table.name}")
        # Insert data
        try:
            db.execute(table.insert().values(table_data))
        except Exception as e:
            logger.error(f"Failed to insert data into {table.name}: {e}")
    
    try:
        db.commit()
        logger.info("Database successfully imported from JSON.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit imported data: {e}")
