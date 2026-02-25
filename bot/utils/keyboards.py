from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


DAYS = {
        "monday": "Понедельник",
        "tuesday": "Вторник",
        "wednesday": "Среда",
        "thursday": "Четверг",
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье",
    }


class Keyboards:

    @staticmethod
    def get_admin_menu() -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton(text="👨‍🏫 Админ-панель")],
            [KeyboardButton(text="📅 Расписание")],
            [KeyboardButton(text="🆘 Помощь")],
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    

    @staticmethod
    def get_student_menu() -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton(text="📅 Расписание")],
            [KeyboardButton(text="🆘 Помощь")],
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    

    @staticmethod
    def get_admin_main_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="⏰ Редактировать расписание", callback_data="admin_edit_schedule")],
            [InlineKeyboardButton(text="📚 Редактировать общие материалы", callback_data="admin_edit_common_files")],
            [InlineKeyboardButton(text="📝 Редактировать материалы для сессии", callback_data="admin_edit_session_files")],
            [InlineKeyboardButton(text="⏳ Редактировать напоминания", callback_data="admin_edit_reminders")],
            [InlineKeyboardButton(text="✨ Редактировать события", callback_data="admin_edit_events")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    

    @staticmethod
    def get_admin_schedule_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="➕ Добавить пару", callback_data="admin_add_select_day")],
            [InlineKeyboardButton(text="➖ Удалить пару", callback_data="admin_del_select_day")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="goto_back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


    @staticmethod
    def get_admin_common_edit_files_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="➕ Добавить файлы", callback_data="admin_add_common_files")],
            [InlineKeyboardButton(text="➖ Удалить файлы", callback_data="admin_del_common_files")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="goto_back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


    @staticmethod
    def get_admin_session_edit_files_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="➕ Добавить файлы", callback_data="admin_add_session_files")],
            [InlineKeyboardButton(text="➖ Удалить файлы", callback_data="admin_del_session_files")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="goto_back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    

    @staticmethod
    def get_admin_reminders_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="➕ Добавить напоминание", callback_data="admin_add_session_files")],
            [InlineKeyboardButton(text="➖ Удалить напоминание", callback_data="admin_del_session_files")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="goto_back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


    @staticmethod
    def get_admin_days_keyboard(action: str = "view", from_menu: str = "main") -> InlineKeyboardMarkup:
        keyboard = []
        for day_id, day_name in DAYS.items():
            if action == "view":
                cb_data = f"day_{day_id}|{from_menu}"
            elif action == "add":
                cb_data = f"add_{day_id}|{from_menu}"
            elif action == "del":
                cb_data = f"del_{day_id}|{from_menu}"
            
            keyboard.append([InlineKeyboardButton(text=day_name, callback_data=cb_data)])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="goto_back")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    

    @staticmethod
    def get_student_days_keyboard(action: str = "view", from_menu: str = "main") -> InlineKeyboardMarkup:
        keyboard = []
        for day_id, day_name in DAYS.items():
            if action == "view":
                cb_data = f"day_{day_id}|{from_menu}"
            elif action == "add":
                cb_data = f"add_{day_id}|{from_menu}"
            elif action == "del":
                cb_data = f"del_{day_id}|{from_menu}"
            
            keyboard.append([InlineKeyboardButton(text=day_name, callback_data=cb_data)])
            
        return InlineKeyboardMarkup(inline_keyboard=keyboard)







    # @staticmethod
    # def example_keyboard():
    #     return ReplyKeyboardMarkup(keyboard=[
    #         [
    #             KeyboardButton(text='Текст 1'),
    #             KeyboardButton(text='Текст 2'),

    #         ]
    #     ], resize_keyboard=True, one_time_keyboard=False, )
    