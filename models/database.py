# database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from config import settings
from datetime import datetime

engine = create_engine(settings.database_url, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ScanTarget(Base):
    __tablename__ = 'scan_targets'
    
    id = Column(Integer, primary_key=True, index=True)
    target = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    result = Column(Text, nullable=True)

class EmailLog(Base):
    __tablename__ = 'email_config'
    
    id = Column(Integer, primary_key=True, index=True)
    smtp_server = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    use_tls = Column(Integer, default=1)  # 1 for True, 0 for False
    use_ssl = Column(Integer, default=0)  # 1 for True, 0 for False
    sender_email = Column(String(255), nullable=False)
    recipients = Column(JSON, nullable=False)  # Store as JSON array
    sent_at = Column(DateTime, default=datetime.utcnow)

class ScanHistory(Base):
    __tablename__ = 'scan_history'

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String(255), index=True, nullable=False)
    status = Column(String(50), nullable=False)
    ports = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=True)
    scan_time = Column(DateTime(timezone=True), server_default=func.now())
    scan_duration = Column(Integer, nullable=True)  # Duration in seconds

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()