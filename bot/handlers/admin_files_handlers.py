from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.models import FileDocument, User
from bot.utils.file_storage import save_file, allowed_file, get_file_extension, delete_file, get_file_full_path
from bot.utils.keyboards import Keyboards
from bot.utils.state import FileUpload

import os


router_files_admin = Router()


@router_files_admin.callback_query(F.data == "admin_add_common_files")
async def start_file_upload(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    stmt = select(User).where(User.user_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or user.status not in ("admin", "elder"):
        await callback.answer("❌ У вас нет прав для загрузки файлов", show_alert=True)
        return
    
    await state.set_state(FileUpload.waiting_for_category)
    await callback.message.edit_text(
        "📂 <b>Выберите категорию для файла:</b>\n\n"
        "• <code>math</code> — Математика\n"
        "• <code>programming</code> — Программирование\n"
        "• <code>physics</code> — Физика\n"
        "• <code>other</code> — Другое\n\n"
        "Или напишите свою категорию латиницей:",
        reply_markup=Keyboards.get_file_categories(),
        parse_mode="HTML"
    )
    await callback.answer()


# === Обработчик выбора категории ===
@router_files_admin.callback_query(FileUpload.waiting_for_category, F.data.startswith("category_"))
async def category_selected(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.replace("category_", "")
    await state.update_data(category=category)
    await state.set_state(FileUpload.waiting_for_file)
    
    await callback.message.edit_text(
        f"📎 <b>Категория:</b> <code>{category}</code>\n\n"
        "Теперь отправьте файл (документ, изображение, архив):\n"
        "📏 Макс. размер: 20 МБ",
        parse_mode="HTML"
    )
    await callback.answer()



@router_files_admin.message(FileUpload.waiting_for_file, F.photo | F.document)
async def file_received(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.photo:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_io = await message.bot.download_file(file.file_path)
        file_bytes = file_io.read()  # ✅ Читаем байты!
        original_name = f"photo_{photo.file_id[:8]}.jpg"
        file_size = photo.file_size
        file_extension = "jpg"
    

    elif message.document:
        document = message.document
        
        if document.file_size > 20 * 1024 * 1024:
            await message.answer("❌ Файл слишком большой (макс. 20 МБ)")
            return
        
        if not allowed_file(document.file_name):
            await message.answer("❌ Этот тип файлов не поддерживается")
            return
        
        file = await message.bot.get_file(document.file_id)
        file_io = await message.bot.download_file(file.file_path)
        file_bytes = file_io.read()  # ✅ Читаем байты!
        original_name = document.file_name
        file_size = document.file_size
        file_extension = get_file_extension(document.file_name)
    
    else:
        await message.answer("❌ Неверный формат файла")
        return
    
    if file_size > 20 * 1024 * 1024:
        await message.answer("❌ Файл слишком большой (макс. 20 МБ)")
        return
    

    data = await state.get_data()
    category = data.get("category")
    
    try:
        relative_path = save_file(file_bytes, original_name, category)
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")
        return
    
   
    await state.update_data(
        file_bytes=file_bytes,
        original_name=original_name,
        file_size=file_size,
        file_extension=file_extension,
        relative_path=relative_path,
        category=category
    )
    

    await state.set_state(FileUpload.waiting_for_filename)
    await message.answer(
        f"📎 <b>Файл получен!</b>\n\n"
        f"📄 Оригинальное имя: <code>{original_name}</code>\n"
        f"💾 Размер: {file_size / 1024:.1f} КБ\n\n"
        "📝 <b>Введите новое имя для файла:</b>\n"
        "(или напишите <code>пропустить</code>, чтобы оставить оригинальное)",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_filename")]
        ])
    )


@router_files_admin.message(FileUpload.waiting_for_filename, F.text)
async def filename_received(message: types.Message, state: FSMContext, session: AsyncSession):
    import logging
    import re
    
    custom_name = message.text.strip()
    
    data = await state.get_data()
    
    
    original_name = data.get("original_name", "")
    file_extension = data.get("file_extension", "jpg")
    relative_path = data.get("relative_path", "")
    category = data.get("category", "other")
    file_size = data.get("file_size", 0)
    
    
    logging.info(f"🔍 FSM state: original_name='{original_name}', type={type(original_name)}")
    
    
    if (not original_name or 
        " " in original_name or 
        "📄" in original_name or 
        "📎" in original_name or
        len(original_name) > 100):
        
        logging.warning(f"⚠️ corrupted original_name detected: '{original_name}'")
        
        
        if relative_path and "/" in relative_path:
            original_name = relative_path.split("/")[-1]
            logging.info(f"✅ restored original_name from path: '{original_name}'")
        else:
            original_name = f"file_{file_extension}"
    

    if not re.match(r'^[\w\.\-]+$', original_name):
        original_name = re.sub(r'[^\w\.\-]', '', original_name)
        if not original_name:
            original_name = f"file_{file_extension}"
    

    if custom_name.lower() != "пропустить":
        safe_name = "".join(c for c in custom_name if c.isalnum() or c in "._- ")
        safe_name = safe_name.strip()
        
        if not safe_name:
            await message.answer("❌ Неверное имя файла. Попробуйте снова:")
            return
        
        new_name = f"{safe_name}.{file_extension}"
        
        old_path = get_file_full_path(relative_path)
        new_relative_path = relative_path.replace(original_name, new_name)
        new_path = get_file_full_path(new_relative_path)
        
        new_path.parent.mkdir(parents=True, exist_ok=True)
        os.rename(old_path, new_path)
        relative_path = new_relative_path
        file_name = new_name
    else:
        file_name = original_name  
    
   
    stmt = select(User).where(User.user_id == message.from_user.id)
    result = await session.execute(stmt)
    uploader = result.scalar_one_or_none()
    
    new_file = FileDocument(
        file_name=file_name,
        file_path=relative_path,
        file_extension=file_extension,
        category=category,
        uploaded_by=uploader.id if uploader else 1,
        file_size=file_size
    )
    
    session.add(new_file)
    await session.commit()
    

    await state.update_data(
        file_bytes=None,
        original_name=None,
        file_size=None,
        file_extension=None,
        relative_path=None
    )
    
    await message.answer(
        f"✅ <b>Файл загружен!</b>\n\n"
        f"📄 Имя: <code>{file_name}</code>\n"
        f"📂 Категория: {category}\n"
        f"💾 Размер: {file_size / 1024:.1f} КБ",
        parse_mode="HTML",
        reply_markup=Keyboards.get_admin_main_keyboard()
    )
    
    await state.clear()


@router_files_admin.callback_query(FileUpload.waiting_for_filename, F.data == "skip_filename")
async def skip_filename(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    original_name = data.get("original_name")
    file_extension = data.get("file_extension")
    relative_path = data.get("relative_path")
    category = data.get("category")
    file_size = data.get("file_size")
    
    file_name = original_name
    

    stmt = select(User).where(User.user_id == callback.from_user.id)
    result = await session.execute(stmt)
    uploader = result.scalar_one_or_none()
    
    new_file = FileDocument(
        file_name=file_name,
        file_path=relative_path,
        file_extension=file_extension,
        category=category,
        uploaded_by=uploader.id if uploader else 1,
        file_size=file_size
    )
    
    session.add(new_file)
    await session.commit()


    await state.update_data(
        file_bytes=None,
        original_name=None,
        file_size=None,
        file_extension=None,
        relative_path=None
    )
    

    await callback.message.edit_text(
        f"✅ <b>Файл загружен!</b>\n\n"
        f"📄 Имя: <code>{file_name}</code>\n"
        f"📂 Категория: {category}\n"
        f"💾 Размер: {file_size / 1024:.1f} КБ",
        parse_mode="HTML",
        reply_markup=Keyboards.get_admin_main_keyboard()
    )
    
    await state.clear()




@router_files_admin.message(
    StateFilter(FileUpload.waiting_for_category, FileUpload.waiting_for_file, FileUpload.waiting_for_filename),
    F.text.lower() == "отмена"
)
@router_files_admin.callback_query(
    StateFilter(FileUpload.waiting_for_category, FileUpload.waiting_for_file, FileUpload.waiting_for_filename),
    F.data == "cancel_upload"
)
async def cancel_upload(event: types.Message | types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if data.get("relative_path"):
        delete_file(data.get("relative_path"))
    
    await state.clear()
    
    msg = event.message if isinstance(event, types.CallbackQuery) else event
    await msg.edit_text(
        "❌ Загрузка отменена",
        reply_markup=Keyboards.get_admin_main_keyboard(),  
        parse_mode="HTML"
    )
    if isinstance(event, types.CallbackQuery):
        await event.answer()



@router_files_admin.callback_query(F.data == "admin_del_common_files")
async def show_files_for_delete(callback: types.CallbackQuery, session: AsyncSession):
    stmt = select(User).where(User.user_id == callback.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or user.status != "admin":
        await callback.answer("❌ У вас нет прав для удаления файлов", show_alert=True)
        return
    
    stmt = select(FileDocument).order_by(FileDocument.uploaded_at.desc())
    result = await session.execute(stmt)
    files = result.scalars().all()
    
    if not files:
        await callback.answer("📭 Нет файлов для удаления", show_alert=True)
        return
    
    keyboard = []
    for f in files[:20]:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🗑️ {f.file_name} ({f.category})",
                callback_data=f"delete_file_{f.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="goto_back")])
    
    await callback.message.edit_text(
        f"📂 <b>Файлов в базе:</b> {len(files)}\n\n"
        "Нажмите на файл, чтобы удалить его:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router_files_admin.callback_query(F.data.startswith("delete_file_"))
async def confirm_delete_file(callback: types.CallbackQuery, session: AsyncSession):
    file_id = int(callback.data.replace("delete_file_", ""))
    
    doc = await session.get(FileDocument, file_id)
    
    if not doc:
        await callback.answer("❌ Файл не найден", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{file_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="goto_back")
        ]
    ])
    
    await callback.message.edit_text(
        f"⚠️ <b>Подтвердите удаление:</b>\n\n"
        f"📄 {doc.file_name}\n"
        f"📂 Категория: {doc.category}\n"
        f"💾 Размер: {doc.file_size / 1024:.1f} КБ\n\n"
        "Файл будет удалён из базы и с диска!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()



@router_files_admin.callback_query(F.data.startswith("confirm_delete_"))
async def execute_delete_file(callback: types.CallbackQuery, session: AsyncSession):
    file_id = int(callback.data.replace("confirm_delete_", ""))
    
    doc = await session.get(FileDocument, file_id)
    
    if not doc:
        await callback.answer("❌ Файл не найден", show_alert=True)
        return
    
    file_deleted = delete_file(doc.file_path)
    
    await session.delete(doc)
    await session.commit()
    
    await callback.message.edit_text(
        f"✅ <b>Файл удалён!</b>\n\n"
        f"📄 {doc.file_name}\n"
        f"{'🗑️ С диска: Да' if file_deleted else '⚠️ С диска: Нет (файл не найден)'}",
        reply_markup=Keyboards.get_admin_main_keyboard(), 
        parse_mode="HTML"
    )