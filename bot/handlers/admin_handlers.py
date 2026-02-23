from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from bot.utils.filters import IsAdmin  
from aiogram.fsm.context import FSMContext

from bot.utils.keyboards import Keyboards, DAYS

from bot.utils.state import ScheduleAdd

from bot.db.database import async_session_maker
from bot.db.models import Schedule

from sqlalchemy import select, delete

from aiogram.exceptions import TelegramBadRequest



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
        reply_markup=Keyboards.get_admin_days_keyboard(action='add', from_menu="admin"),  # Префикс admin_add_day_
        parse_mode="HTML"
    )
    await callback.answer()

# === 1. НАЧАЛО УДАЛЕНИЯ ===
@router_admin.callback_query(F.data == "admin_del_select_day")
async def start_delete_lesson(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➖ <b>Удаление пары</b>\n\nВыберите день:",
        reply_markup=Keyboards.get_admin_days_keyboard(action='del', from_menu="admin"),  # Префикс admin_del_day_
        parse_mode="HTML"
    )
    await callback.answer()

# === ОБРАБОТКА ВЫБОРА ДНЯ (УНИВЕРСАЛЬНАЯ) ===
@router_admin.callback_query(F.data.startswith("add_"))
async def add_lesson_select_day(callback: CallbackQuery, state: FSMContext):
    day_id = callback.data.split("_")[1].split("|")[0]
    await state.update_data(day=day_id, from_menu="admin")
    
    try:
        await callback.message.edit_text(
            f"📅 День: <b>{DAYS[day_id]}</b>\n\nВведите номер пары (1, 2, 3...):",
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.answer()
        return

    await state.set_state(ScheduleAdd.lesson_number)
    await callback.answer()

@router_admin.callback_query(F.data.startswith("del_"))
async def delete_lesson_select_day(callback: CallbackQuery, state: FSMContext):
    # Парсим: del_monday|admin -> day_id = monday
    day_id = callback.data.split("_")[1].split("|")[0]
    
    await state.update_data(day=day_id)
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Schedule).where(Schedule.day_of_week == day_id).order_by(Schedule.lesson_number)
        )
        lessons = result.scalars().all()
    
    # Исправлено: callback_data теперь ведет на существующий хендлер admin_del_select_day
    keyboard_empty = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к дням", callback_data="admin_del_select_day")]
    ])

    if not lessons:
        try:
            await callback.message.edit_text(
                "📭 На этот день пар нет.", 
                reply_markup=keyboard_empty
            )
        except TelegramBadRequest:
            # Исправлено: reply_markup нельзя передать в answer(), он не сменит кнопки сообщения
            await callback.answer("📭 На этот день пар нет.", show_alert=True)
        return
    
    text = f"📅 {DAYS[day_id]}\n\nВыберите пару для удаления:\n"
    keyboard = []
    for lesson in lessons:
        keyboard.append([InlineKeyboardButton(
            text=f"{lesson.lesson_number}. {lesson.subject}",
            callback_data=f"admin_del_confirm_{lesson.id}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_del_select_day")])
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.answer()
        return
    
    await callback.answer()


@router_admin.callback_query(F.data.startswith("admin_del_confirm_"))
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    try:
        lesson_id_str = callback.data.split("_")[-1]
        
        if not lesson_id_str.isdigit():
            await callback.answer("❌ Неверный ID", show_alert=True)
            return
        
        lesson_id = int(lesson_id_str)

        async with async_session_maker() as session:
            result = await session.execute(select(Schedule).where(Schedule.id == lesson_id))
            lesson = result.scalar_one_or_none()
            
            if not lesson:
                await callback.answer("⚠️ Пара не найдена", show_alert=True)
                return

            lesson_subject = lesson.subject
            
            await session.delete(lesson)
            await session.commit()

        # === Создаем ПРАВИЛЬНУЮ inline-клавиатуру ===
        # Вариант 1: Если у вас есть метод для inline-меню
        # from_menu_keyboard = Keyboards.get_admin_inline_menu()
        
        # Вариант 2: Создаем вручную, если метода нет
        from_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить пару", callback_data="admin_add_select_day")],
            [InlineKeyboardButton(text="➖ Удалить пару", callback_data="admin_del_select_day")]
        ])

        # === Обновляем сообщение ===
        try:
            await callback.message.edit_text(
                f"✅ <b>{lesson_subject}</b> удалена!",
                reply_markup=from_menu_keyboard,  # <-- Только InlineKeyboardMarkup!
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            # Если edit_text не сработал — удаляем и отправляем новое
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(
                f"✅ <b>{lesson_subject}</b> удалена!",
                reply_markup=from_menu_keyboard,
                parse_mode="HTML"
            )
        
        await callback.answer()  # Пустой answer, чтобы убрать "часики"
        await state.clear()
        
    except Exception as e:
        # Логируем полную ошибку в консоль
        print(f"❌ Ошибка при удалении: {type(e).__name__}: {e}")
        
        # В callback.answer отправляем ТОЛЬКО короткое сообщение (<200 символов!)
        error_msg = f"❌ Ошибка: {type(e).__name__}"
        await callback.answer(error_msg[:200], show_alert=True)


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