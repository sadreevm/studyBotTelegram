from sqlalchemy.orm import Session as DBSession
from bot.db.models import SessionFile, Session
from bot.utils.file_storage import save_file, allowed_file
from typing import List, Optional

class SessionFileService:
    def __init__(self, db: DBSession):
        self.db = db

    def upload_file(
        self, 
        session_id: str, 
        file_bytes: bytes, 
        original_filename: str,
        category: str = "other"  # ✅ Теперь категория обязательна (по умолчанию 'other')
    ) -> Optional[SessionFile]:
        """
        Загружает файл в контекст учебной сессии.
        Файлы сохраняются в: storage/files/session_files/{category}/{uuid}.ext
        """
        # 1. Валидация
        if not allowed_file(original_filename):
            raise ValueError(f"Файл {original_filename} имеет запрещенное расширение")

        # 2. Формируем путь для сохранения
        # ✅ FIX: Склеиваем базовую папку и подкатегорию
        # save_file создаст папку storage/files/session_files/tickets/ автоматически
        storage_path = f"session_files/{category}"
        
        relative_path = save_file(file_bytes, original_filename, storage_path)

        # 3. Запись в БД
        db_file = SessionFile(
            session_id=session_id,
            original_filename=original_filename,
            stored_path=relative_path,
            file_size=len(file_bytes),
            category=category  # ✅ Сохраняем категорию в БД для фильтрации
        )
        
        self.db.add(db_file)
        self.db.commit()
        self.db.refresh(db_file)
        
        return db_file

    def get_session_files(self, session_id: str, category: str = None) -> List[SessionFile]:
        """
        Список материалов сессии.
        ✅ Можно фильтровать по категории (если передана).
        """
        query = self.db.query(SessionFile).filter(SessionFile.session_id == session_id)
        
        if category:
            query = query.filter(SessionFile.category == category)
            
        return query.all()

    def delete_file(self, file_id: str) -> bool:
        """Удалить конкретный файл сессии."""
        db_file = self.db.query(SessionFile).filter(SessionFile.id == file_id).first()
        if not db_file:
            return False
            
        self.db.delete(db_file)
        self.db.commit()
        return True

    def delete_all_session_files(self, session_id: str):
        """Очистить все файлы сессии (работает cascade при удалении Session)."""
        files = self.get_session_files(session_id)
        for f in files:
            self.delete_file(f.id)