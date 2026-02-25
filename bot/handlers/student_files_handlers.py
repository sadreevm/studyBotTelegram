from aiogram import Router, F, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc


from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import FileDocument
from bot.utils.keyboards import Keyboards

router_files_student = Router()


@router_files_student.message(F.text == "📚 Обычные файлы")
async def open_files_from_menu(message: types.Message, session: AsyncSession):
    stmt = select(FileDocument.category).distinct()
    result = await session.execute(stmt)
    categories = result.scalars().all()
    cat_list = list(categories)
    
    if not cat_list:
        await message.answer("📭 Пока нет файлов", reply_markup=Keyboards.get_student_menu())
        return
    
    await message.answer(
        "📚 <b>Доступные категории:</b>\n\n" +
        "\n".join(f"• <code>{cat}</code>" for cat in cat_list),
        reply_markup=Keyboards.get_categories_keyboard(cat_list),
        parse_mode="HTML"
    )


@router_files_student.callback_query(F.data == "view_files")
async def show_categories(callback: types.CallbackQuery, session: AsyncSession):
    stmt = select(FileDocument.category).distinct()
    result = await session.execute(stmt)
    categories = result.scalars().all()
    cat_list = list(categories)
    
    if not cat_list:
        await callback.answer("📭 Пока нет файлов", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📚 <b>Доступные категории:</b>\n\n" +
        "\n".join(f"• <code>{cat}</code>" for cat in cat_list),
        reply_markup=Keyboards.get_categories_keyboard(cat_list),
        parse_mode="HTML"
    )
    await callback.answer()


@router_files_student.callback_query(F.data.startswith("files_in_"))
async def show_files_in_category(callback: types.CallbackQuery, session: AsyncSession):
    category = callback.data.replace("files_in_", "")
    
    stmt = select(FileDocument).where(
        FileDocument.category == category
    ).order_by(desc(FileDocument.uploaded_at))
    
    result = await session.execute(stmt)
    files = result.scalars().all()
    
    if not files:
        await callback.answer("📭 В этой категории пока пусто", show_alert=True)
        return
    

    file_list = "\n".join([
        f"📄 <b>{f.file_name}</b>\n"
        f"   <i>💾 {f.file_size / 1024:.1f} КБ • {f.uploaded_at.strftime('%d.%m.%Y')}</i>"
        for f in files[:10]
    ])
    

    keyboard = []
    for f in files[:10]:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📥 Скачать: {f.file_name[:30]}{'...' if len(f.file_name) > 30 else ''}",
                callback_data=f"download_file_{f.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 К категориям", callback_data="view_files")])
    
    await callback.message.edit_text(
        f"📂 <b>Категория:</b> <code>{category}</code>\n\n{file_list}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router_files_student.callback_query(F.data.startswith("download_file_"))
async def download_file(callback: types.CallbackQuery, session: AsyncSession):
    file_id = int(callback.data.replace("download_file_", ""))
    
    doc = await session.get(FileDocument, file_id)
    
    if not doc:
        await callback.answer("❌ Файл не найден", show_alert=True)
        return
    
    from bot.utils.file_storage import get_file_full_path
    file_path = get_file_full_path(doc.file_path)
    
    if not file_path.exists():
        await callback.answer("⚠️ Файл был удалён с сервера", show_alert=True)
        return
    

    if doc.file_extension in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        await callback.message.answer_photo(
            photo=FSInputFile(str(file_path)),
            caption=f"📎 {doc.file_name}\n📂 {doc.category}\n💾 {doc.file_size / 1024:.1f} КБ"
        )
    else:
        await callback.message.answer_document(
            document=FSInputFile(str(file_path)),
            caption=f"📎 {doc.file_name}\n📂 {doc.category}\n💾 {doc.file_size / 1024:.1f} КБ"
        )


    await callback.answer("✅ Файл отправлен!")
    
    
    await callback.message.edit_text(
        f"📂 <b>Категория:</b> <code>{doc.category}</code>\n\n"
        "✅ Файл отправлен!\n\n"
        "Выберите другой файл или вернитесь назад:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К категориям", callback_data="view_files")]
        ]),
        parse_mode="HTML"
    )


@router_files_student.message(F.text.regexp(r"^/file_(\d+)$"))
async def send_file_by_id(message: types.Message, session: AsyncSession):
    file_id = int(message.text.split("_")[1])
    
    doc = await session.get(FileDocument, file_id)
    
    if not doc:
        await message.answer("❌ Файл не найден")
        return
    
    from bot.utils.file_storage import get_file_full_path
    file_path = get_file_full_path(doc.file_path)
    
    if not file_path.exists():
        await message.answer("⚠️ Файл был удалён с сервера")
        return
    
    if doc.file_extension in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        await message.answer_photo(
            photo=FSInputFile(str(file_path)),
            caption=f"📎 {doc.file_name}\n📂 {doc.category}"
        )
    else:
        await message.answer_document(
            document=FSInputFile(str(file_path)),
            caption=f"📎 {doc.file_name}\n📂 {doc.category}\n💾 {doc.file_size / 1024:.1f} КБ"
        )