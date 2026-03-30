# Database Models
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import datetime
import os

# Database setup - Use absolute path to ensure consistent location
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BACKEND_DIR, "users.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model_used = Column(String, nullable=True)  # Track which model was used for this response
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", backref="user_chat_history")

class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", backref="user_uploaded_documents")

class UploadedCSV(Base):
    __tablename__ = "uploaded_csvs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    columns_info = Column(Text, nullable=True)
    table_name = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", backref="user_uploaded_csvs")

class DatabaseConnection(Base):
    __tablename__ = "database_connections"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # User-friendly name
    db_type = Column(String, nullable=False)  # mysql, postgresql, sqlite, sqlserver, etc.
    host = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    database = Column(String, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)  # Encrypted in production
    connection_string = Column(Text, nullable=True)  # Optional custom connection string
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    user = relationship("User", backref="database_connections")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def recreate_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def ensure_database_schema():
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if all required tables exist
            result = conn.execute(text("SELECT table_name FROM uploaded_csvs LIMIT 1"))
            result = conn.execute(text("SELECT id FROM database_connections LIMIT 1"))
    except Exception as e:
        print(f"Database schema outdated, recreating tables: {e}")
        recreate_database()

# Initialize database
Base.metadata.create_all(bind=engine)
ensure_database_schema()