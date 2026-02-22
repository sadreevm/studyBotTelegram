from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from bot.utils.filters import IsAdmin  
from aiogram.fsm.context import FSMContext

from bot.utils.keyboards import Keyboards, DAYS

from bot.utils.state import ScheduleAdd

from bot.db.database import async_session_maker
from bot.db.models import Schedule

from sqlalchemy import select, delete



router_admin = Router()


@router_admin.message(F.text == "👨‍🏫 Админ-панель")
@router_admin.message(Command('admin'))
async def cmd_admin_panel(message: Message):
    # Проверка прав внутри хендлера
    if not await IsAdmin()(message):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    await message.answer(
        "👨‍🏫 <b>Панель старосты:</b>",
        reply_markup=Keyboards.get_admin_schedule_keyboard(),
        parse_mode="HTML"
    )


@router_admin.callback_query(F.data == "admin_add_select_day")
async def start_add_lesson(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ <b>Добавление пары</b>\n\nВыберите день:",
        reply_markup=Keyboards.get_admin_days_keyboard('add', from_menu="admin"),  # Префикс admin_add_day_
        parse_mode="HTML"
    )
    await callback.answer()

# === 1. НАЧАЛО УДАЛЕНИЯ ===
@router_admin.callback_query(F.data == "admin_del_select_day")
async def start_delete_lesson(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➖ <b>Удаление пары</b>\n\nВыберите день:",
        reply_markup=Keyboards.get_admin_days_keyboard('del', from_menu="admin"),  # Префикс admin_del_day_
        parse_mode="HTML"
    )
    await callback.answer()

# === ОБРАБОТКА ВЫБОРА ДНЯ (УНИВЕРСАЛЬНАЯ) ===
@router_admin.callback_query(F.data.startswith("admin_add_day_"))
async def add_lesson_select_day(callback: CallbackQuery, state: FSMContext):
    day_id = callback.data.split("_")[-1]
    await state.update_data(day=day_id, from_menu="admin")
    await callback.message.edit_text(
        f"📅 День: <b>{DAYS[day_id]}</b>\n\nВведите номер пары (1, 2, 3...):",
        parse_mode="HTML"
    )
    await state.set_state(ScheduleAdd.lesson_number)
    await callback.answer()

@router_admin.callback_query(F.data.startswith("admin_del_day_"))
async def delete_lesson_select_day(callback: CallbackQuery, state: FSMContext):
    day_id = callback.data.split("_")[-1]
    await state.update_data(day=day_id)
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Schedule).where(Schedule.day_of_week == day_id).order_by(Schedule.lesson_number)
        )
        lessons = result.scalars().all()
    
    if not lessons:
        await callback.message.edit_text("📭 На этот день пар нет.")
        return
    
    text = f"📅 {DAYS[day_id]}\n\nВыберите пару для удаления:\n"
    keyboard = []
    for lesson in lessons:
        # Уникальный callback для удаления конкретной пары
        keyboard.append([InlineKeyboardButton(
            text=f"{lesson.lesson_number}. {lesson.subject}",
            callback_data=f"admin_del_confirm_{lesson.id}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_del_select_day")])
    
    from aiogram.types import InlineKeyboardMarkup
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router_admin.callback_query(F.data.startswith("admin_del_confirm_"))
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    lesson_id = int(callback.data.split("_")[-1])
    
    async with async_session_maker() as session:
        await session.execute(delete(Schedule).where(Schedule.id == lesson_id))
        await session.commit()
    
    await callback.message.edit_text(
        "✅ Пара удалена!",
        reply_markup=Keyboards.get_admin_menu()
    )
    await callback.answer()
    await state.clear()

# === КНОПКА "НАЗАД" (ИЗ АДМИНКИ В ГЛАВНОЕ МЕНЮ) ===
@router_admin.callback_query(F.data == "admin_menu")
async def back_to_admin_main(callback: CallbackQuery):
    await callback.message.answer(
        "👨‍🏫 <b>Панель старосты:</b>",
        reply_markup=Keyboards.get_admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# === КНОПКА "НАЗАД" (В ГЛАВНОЕ МЕНЮ БОТА) ===
@router_admin.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.answer(
        "📋 Главное меню:",
        reply_markup=Keyboards.get_admin_menu()
    )
    await callback.answer()


@router_admin.message(StateFilter(ScheduleAdd.lesson_number))
async def add_lesson_number(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число!")
        return
    await state.update_data(lesson_number=int(message.text))
    await message.answer("📚 Введите название предмета:")
    await state.set_state(ScheduleAdd.subject)

@router_admin.message(StateFilter(ScheduleAdd.subject))
async def add_lesson_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer("⏰ Введите время начала (09:00):")
    await state.set_state(ScheduleAdd.time_start)

@router_admin.message(StateFilter(ScheduleAdd.time_start))
async def add_lesson_time_start(message: Message, state: FSMContext):
    await state.update_data(time_start=message.text)
    await message.answer("⏰ Введите время окончания (10:30):")
    await state.set_state(ScheduleAdd.time_end)

@router_admin.message(StateFilter(ScheduleAdd.time_end))
async def add_lesson_time_end(message: Message, state: FSMContext):
    await state.update_data(time_end=message.text)
    await message.answer("🚪 Аудитория (или 'пропустить'):")
    await state.set_state(ScheduleAdd.classroom)

@router_admin.message(StateFilter(ScheduleAdd.classroom))
async def add_lesson_classroom(message: Message, state: FSMContext):
    await state.update_data(classroom=message.text if message.text != "пропустить" else None)
    await message.answer("👨‍🏫 Преподаватель (или 'пропустить'):")
    await state.set_state(ScheduleAdd.teacher)

@router_admin.message(StateFilter(ScheduleAdd.teacher))
async def add_lesson_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    teacher = message.text if message.text != "пропустить" else None
    
    async with async_session_maker() as session:
        new_lesson = Schedule(
            day_of_week=data["day"],
            lesson_number=data["lesson_number"],
            subject=data["subject"],
            time_start=data["time_start"],
            time_end=data["time_end"],
            classroom=data.get("classroom"),
            teacher=teacher
        )
        session.add(new_lesson)
        await session.commit()
    
    await message.answer(
        f"✅ <b>Пара добавлена!</b>",
        parse_mode="HTML",
        reply_markup=Keyboards.get_admin_schedule_keyboard()
    )
    await state.clear()