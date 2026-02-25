import os
import uuid
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FILES_DIR = BASE_DIR / "storage" / "files"

# Разрешённые расширения
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',  # Office
    'txt', 'rtf', 'odt', 'ods', 'odp',                   # OpenOffice
    'png', 'jpg', 'jpeg', 'gif', 'webp',                 # Images
    'zip', 'rar', '7z', 'tar', 'gz',                     # Archives
    'py', 'js', 'java', 'cpp', 'c', 'h', 'sql', 'md',   # Code
}

def allowed_file(filename: str) -> bool:
    """Проверка расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename: str) -> str:
    """Получить расширение файла в нижнем регистре"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def save_file(file_bytes: bytes, original_filename: str, category: str) -> str:
    """
    Сохраняет файл и возвращает относительный путь к нему.
    Файлы хранятся по схеме: storage/files/{category}/{unique_id}.{ext}
    """
    ext = get_file_extension(original_filename)
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    
    category_dir = FILES_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = category_dir / unique_name
    file_path.write_bytes(file_bytes)
    
    # Возвращаем относительный путь для БД
    return str(file_path.relative_to(BASE_DIR))

def get_file_full_path(relative_path: str) -> Path:
    """Получить абсолютный путь к файлу для отправки"""
    return BASE_DIR / relative_path

def delete_file(relative_path: str) -> bool:
    """Удалить файл с диска"""
    try:
        file_path = get_file_full_path(relative_path)
        if file_path.exists():
            file_path.unlink()
            # Опционально: удалить пустую папку категории
            category_dir = file_path.parent
            if not any(category_dir.iterdir()):
                category_dir.rmdir()
            return True
    except Exception:
        pass
    return False


def sanitize_filename(filename: str) -> str:
    """Очищает имя файла от опасных символов"""
    # Разрешаем: буквы, цифры, точка, подчёркивание, дефис, пробел
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    return safe_name.strip()