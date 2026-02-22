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
            [KeyboardButton(text="👨‍🏫 Админ-панель")],  # ✅ Кнопка админки
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
    def get_days_keyboard(from_menu: str = "main") -> InlineKeyboardMarkup:
        """
        from_menu: "main" (главное меню) или "admin" (админка)
        """
        keyboard = []
        for day_id, day_name in DAYS.items():
            keyboard.append([InlineKeyboardButton(
                text=day_name, 
                callback_data=f"day_{day_id}_from_{from_menu}"
            )])
        
        # Кнопка назад с информацией о предыдущем меню
        keyboard.append([InlineKeyboardButton(
            text="🔙 Назад", 
            callback_data=f"back_to_{from_menu}"
        )])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_admin_schedule_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="➕ Добавить пару", callback_data="admin_add_select_day")],
            [InlineKeyboardButton(text="➖ Удалить пару", callback_data="admin_del_select_day")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


    @staticmethod
    def get_admin_days_keyboard(action: str) -> InlineKeyboardMarkup:
        """
        action: 'add' или 'del'
        """
        keyboard = []
        for day_id, day_name in DAYS.items():
            if action == 'add':
                # Для добавления: admin_add_day_monday
                cb_data = f"admin_add_day_{day_id}"
            else:
                # Для удаления: admin_del_day_monday
                cb_data = f"admin_del_day_{day_id}"
            
            keyboard.append([InlineKeyboardButton(text=day_name, callback_data=cb_data)])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


    @staticmethod
    def example_keyboard():
        return ReplyKeyboardMarkup(keyboard=[
            [
                KeyboardButton(text='Текст 1'),
                KeyboardButton(text='Текст 2'),

            ]
        ], resize_keyboard=True, one_time_keyboard=False, )
    
    @staticmethod
    def inline_pay():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Купить подписку', callback_data='pay_inl')]
        ])
    
    @staticmethod
    def inline_pay_continue():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Продлить', callback_data='pay_inl')]
        ])
    
    @staticmethod
    def inline_payments():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Оплатить', callback_data='pay_inl')]
        ])
    
    @staticmethod
    def admin_menu():
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='Добавление диспетчеров')],
            [KeyboardButton(text='Удаление диспетчеров')],
            [KeyboardButton(text='Выйти')]
        ], resize_keyboard=True)