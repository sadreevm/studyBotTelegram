from aiogram import Router, F
from aiogram.filters import Command 
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from bot.utils.filters import IsStudent
from bot.utils.keyboards import Keyboards, DAYS
from bot.db.database import async_session_maker
from sqlalchemy import select
from bot.db.models import Schedule

router_student = Router()

@router_student.message(F.text == "📅 Расписание")
@router_student.message(Command('schedule'))
async def cmd_schedule(message: Message):
    await message.answer(
        "📅 <b>Выберите день недели:</b>",
        reply_markup=Keyboards.get_admin_days_keyboard(action="view", from_menu="main"),
        parse_mode="HTML"
    )

@router_student.callback_query(F.data.startswith("day_"))
async def show_day_schedule(callback: CallbackQuery):
    # 1. Парсинг данных
    try:
        day_part, from_menu = callback.data.split("|")
        day_id = day_part.replace("day_", "")
    except ValueError:
        day_id = callback.data.replace("day_", "")
        from_menu = "main"
    
    day_name = DAYS.get(day_id, day_id)
    
    # 2. Получение пар из БД
    async with async_session_maker() as session:
        result = await session.execute(
            select(Schedule)
            .where(Schedule.day_of_week == day_id)
            .order_by(Schedule.lesson_number)
        )
        lessons = result.scalars().all()
    
    # 3. Формирование текста
    if not lessons:
        text = f"📭 <b>{day_name}</b>\n\nНа этот день пар нет."
    else:
        text = f"📅 <b>{day_name}</b>\n\n"
        for lesson in lessons:
            text += f"<b>{lesson.lesson_number}.</b> {lesson.time_start}-{lesson.time_end}\n"
            text += f"   📚 {lesson.subject}\n"
            if lesson.classroom:
                text += f"   🚪 Ауд. {lesson.classroom}\n"
            if lesson.teacher:
                text += f"   👨‍🏫 {lesson.teacher}\n"
            text += "\n"
    
    # 4. Формирование клавиатуры
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к дням", callback_data=f"back_to_{from_menu}")]
        ])
    
    # 5. Отправка сообщения
    try:
        await callback.message.edit_text(
            text, 
            reply_markup=keyboard, 
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.answer()
        return
    
    await callback.answer()

# ✅ ИЗМЕНЁННЫЙ ХЕНДЛЕР "НАЗАД"
@router_student.callback_query(F.data.startswith("back_to_"))
async def back_handler(callback: CallbackQuery):
    from_menu = callback.data.replace("back_to_", "")
    
    try:
        # Вместо удаления — редактируем сообщение и показываем выбор дней
        await callback.message.edit_text(
            "📅 <b>Выберите день недели:</b>",
            reply_markup=Keyboards.get_admin_days_keyboard(action="view", from_menu=from_menu),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        # Если сообщение не изменилось (например, быстро нажали)
        await callback.answer()
        return
    
    await callback.answer()

@router_student.message(F.text == "🆘 Помощь")
@router_student.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(
        "🆘 <b>Доступные команды:</b>\n\n"
        "/start - Регистрация\n"
        "/schedule - Моё расписание\n"
        "/help - Эта справка",
        parse_mode="HTML"
    )