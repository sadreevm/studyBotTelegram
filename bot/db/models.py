import uuid
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, BigInteger, event
from sqlalchemy.orm import relationship, declarative_base
from bot.db.database import Base
# Импортируем твои утилиты для работы с диском
from bot.utils.file_storage import delete_file 

# ==========================================
# 1. МОДЕЛЬ СЕССИИ (Учебная сессия)
# ==========================================
class Session(Base):
    __tablename__ = "sessions"
    
    # Используем UUID, чтобы ID сессии было сложно подобрать
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Привязка к студенту
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Метаданные сессии
    title = Column(String(100), nullable=True)       # Например: "Сессия 2024 Лето"
    start_date = Column(DateTime, nullable=True)     # Начало сессии
    end_date = Column(DateTime, nullable=True)       # Конец сессии
    is_completed = Column(Integer, default=0)        # 0 = идет, 1 = завершена/сдана
    
    created_at = Column(DateTime, default=func.now())

    # Связь с файлами: если удаляем сессию -> удаляем файлы (cascade)
    files = relationship("SessionFile", back_populates="session", cascade="all, delete-orphan")
    # Связь с пользователем
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, completed={self.is_completed})>"


# ==========================================
# 2. ПОЛЬЗОВАТЕЛЬ (Студент)
# ==========================================
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False) # Telegram ID
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    status = Column(String, nullable=True)
    
    # Файлы в базе знаний (загруженные пользователем)
    uploaded_files = relationship("FileDocument", back_populates="uploader", lazy="select")
    # Учебные сессии пользователя
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, user_id: int, username: str, status: str):
        self.user_id = user_id
        self.username = username
        self.status = status

    def __repr__(self):
        # FIX: Было self.telegram_id (ошибка), стало self.user_id
        return f"<User(telegram_id={self.user_id})>"


# ==========================================
# 3. ФАЙЛ СЕССИИ (Материалы к сессии)
# ==========================================
class SessionFile(Base):
    __tablename__ = "session_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # ✅ FIX: Делаем session_id необязательным
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, default=0)
    mime_type = Column(String(100), nullable=True)
    category = Column(String(50), nullable=True, index=True)  # ✅ Подкатегория: tickets, answers...
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Обратная связь (может быть None)
    session = relationship("Session", back_populates="files")

    def __repr__(self):
        return f"<SessionFile(id={self.id}, filename={self.original_filename})>"

# ==========================================
# 4. БАЗА ЗНАНИЙ (Общие файлы)
# ==========================================
class FileDocument(Base):
    __tablename__ = 'file_documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_extension = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    uploaded_at = Column(DateTime, default=func.now())
    file_size = Column(Integer, nullable=False)
    
    uploader = relationship("User", back_populates="uploaded_files")
    
    def __repr__(self):
        return f"<FileDocument(name={self.file_name}, category={self.category})>"


# ==========================================
# 5. ОСТАЛЬНЫЕ МОДЕЛИ
# ==========================================
class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(String, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    time_start = Column(String, nullable=False)
    time_end = Column(String, nullable=False)
    classroom = Column(String, nullable=True)
    teacher = Column(String, nullable=True)

class Dispatchers(Base):
    __tablename__ = "dispatchers"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    def __init__(self, username: str):
        self.username = username


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)      # Название события
    event_date = Column(DateTime, nullable=False)    # Дата и время события
    description = Column(String(1000), nullable=True)  # Описание (опционально)
    created_at = Column(DateTime, default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Кто создал

    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title}, date={self.event_date})>"


# ==========================================
# 6. АВТО-УДАЛЕНИЕ ФАЙЛОВ (Хук)
# ==========================================
@event.listens_for(SessionFile, "before_delete")
def receive_before_delete(mapper, connection, target):
    """
    Удаляет физический файл с диска перед удалением записи из БД.
    Срабатывает и при ручном удалении, и при каскадном удалении сессии.
    """
    try:
        delete_file(target.stored_path)
    except Exception as e:
        print(f"Error deleting file {target.stored_path}: {e}")