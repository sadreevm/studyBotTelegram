import importlib
import os

from aiogram import Router
from .start_handlers import router_start
from .admin_handlers import router_admin
from .student_handlers import router_student

routes = [
    router_start,
    router_admin,
    router_student
]

def setup_handlers(dp: Router):
    handlers_dir = os.path.dirname(__file__)
    for file in os.listdir(handlers_dir):
        if file.endswith("_handler.py") or file.endswith("_handlers.py"):
            module_name = file[:-3]  # Убираем ".py"
            try:
                module = importlib.import_module(f"bot.handlers.{module_name}")
                if hasattr(module, "register_handlers"):
                    module.register_handlers(dp)
            except Exception as e:
                print(f"[ERROR] Не удалось загрузить {module_name}: {e}")
                