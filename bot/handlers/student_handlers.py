from aiogram import Router, F
from aiogram.filters import Command 
from aiogram.types import Message, CallbackQuery\

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
        reply_markup=Keyboards.get_days_keyboard(from_menu="main"),
        parse_mode="HTML"
    )


@router_student.callback_query(F.data.startswith("day_"))
async def show_day_schedule(callback: CallbackQuery):
    parts = callback.data.split("_from_")
    day_id = parts[0].replace("day_", "")
    from_menu = parts[1] if len(parts) > 1 else "main"
    
    day_name = DAYS.get(day_id, day_id)
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Schedule)
            .where(Schedule.day_of_week == day_id)
            .order_by(Schedule.lesson_number)
        )
        lessons = result.scalars().all()
    
    if not lessons:
        text = f"📭 <b>{day_name}</b>\n\nНа этот день пар нет."
    else:
        text = f"📅 <b>{day_name}</b>\n\n"
        for lesson in lessons:
            text += f"<b>{lesson.lesson_number}.</b> {lesson.time_start}-{lesson.time_end}\n"
            text += f"   📚 {lesson.subject}\n"
            if lesson.classroom:
                text += f"   🚪 Ауд. {lesson.classroom}\n"
            text += "\n"
    
    # Передаём from_menu дальше
    await callback.message.edit_text(
        text, 
        reply_markup=Keyboards.get_days_keyboard(from_menu=from_menu), 
        parse_mode="HTML"
    )
    await callback.answer()

# ✅ Кнопка "Назад"
@router_student.callback_query(F.data.startswith("back_to_"))
async def back_handler(callback: CallbackQuery):
    from_menu = callback.data.replace("back_to_", "")
    
    if from_menu == "main":
        # Возврат в главное меню
        await callback.message.edit_text(
            "📋 Главное меню:",
            reply_markup=Keyboards.get_student_menu()
        )
    elif from_menu == "admin":
        # Возврат в админку
        await callback.message.edit_text(
            "👨‍🏫 <b>Панель старосты:</b>",
            reply_markup=Keyboards.admin_menu(),
            parse_mode="HTML"
        )
    
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