from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, func

from bot.db.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    status = Column(String, nullable=True)

    def __init__(self, user_id: int, username: str, status: str):
        self.user_id = user_id
        self.username = username
        self.status = status

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id})>"


class Schedule(Base):
    __tablename__ = 'schedule'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(String, nullable=False)  # monday, tuesday, etc.
    lesson_number = Column(Integer, nullable=False)  # 1, 2, 3...
    subject = Column(String, nullable=False)
    time_start = Column(String, nullable=False)  # "09:00"
    time_end = Column(String, nullable=False)    # "10:30"
    classroom = Column(String, nullable=True)    # "305"
    teacher = Column(String, nullable=True)      # "Иванов И.И."

    def __repr__(self):
        return f"<Schedule(day={self.day_of_week}, lesson={self.lesson_number}, subject={self.subject})>"
    

class Dispatchers(Base):
    __tablename__ = "dispatchers"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)

    def __init__(self, username: str):
        self.username = username