from aiogram import types, Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.utils.keyboards import Keyboards
from bot.utils.messages import Messages
from bot.utils.state import SignUp

from bot.config import Config

from bot.db.database import async_session_maker, init_db
from bot.db.models import User

from sqlalchemy import select


router_start = Router()

# Фильтр прямо в роутере: пропускаем только если статус == 'student'
# Если пользователь админ, этот роутер его проигнорирует
router_start.message.filter(lambda msg: msg.from_user.id) # Базовый фильтр на наличие юзера

@router_start.message(Command('start'))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    initial_status = "admin" if user_id in Config.ADMIN_IDS else "student"
    
    async with async_session_maker() as session:
        # Ищем пользователя по user_id
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            # Создаем нового пользователя с правильной ролью
            user = User(user_id=user_id, username=username, status=initial_status)
            session.add(user)
            await session.commit()
            
            role_text = "старостой 🎓" if initial_status == "admin" else "студентом 📚"
            await message.answer(f"👋 Привет! Я записал тебя {role_text}.")
        else:
            # Обновляем username, если изменился
            if user.username != username:
                user.username = username
                await session.commit()
            await message.answer(f"👋 С возвращением, {message.from_user.first_name}!")

        if user.status == "admin":
            await message.answer("📋 Главное меню:", reply_markup=Keyboards.get_admin_menu())
        else:
            await message.answer("📋 Главное меню:", reply_markup=Keyboards.get_student_menu())


@router_start.message(F.text == "🆘 Помощь")
@router_start.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(
        "🆘 <b>Доступные команды:</b>\n\n"
        "/start - Меню\n"
        "/schedule - Расписание\n"
        "/admin - Панель старосты",
        parse_mode="HTML"
    )

    # await message.answer(Messages.hello_message(Config.LINK_CHANNEL), reply_markup=Keyboards.inline_pay())
#     await message.answer(text='Мне нужно вас зарегестрировать😉')
#     await message.answer(text='Ваше имя⬇️')
#     await state.set_state(SignUp.get_name)

# @router_start.message(F.text, SignUp.get_name)
# async def get_name(message: types.Message, state: FSMContext):
#     await state.update_data(name = message.text)
#     await message.answer(text='Ваша фамилия⬇️')
#     await state.set_state(SignUp.get_surname)


# @router_start.message(F.text, SignUp.get_surname)
# async def get_surname(message: types.Message, state: FSMContext):
#     await state.update_data(surname = message.text)
#     await message.answer(text=f'Чтобы не потеряться в случае блокировки Телеграм, оставьте свои запасные контактные данные.\n\nВаш e-mail⬇️')
#     await state.set_state(SignUp.get_email)


# @router_start.message(F.text, SignUp.get_email)
# async def get_email(message: types.Message, state: FSMContext):
#     email = message.text
#     if ValidationHelper.is_valid_email(email):
#         await state.update_data(email=email)
#         await message.answer(text='Ваш номер телефона⬇️')
#         await state.set_state(SignUp.get_number)
#     else:
#         await message.answer(text=f'Неверный формат почты.\nПроверьте на ошибки и отправьте еще раз.')
#         await state.set_state(SignUp.get_email)

# @router_start.message(F.text, SignUp.get_number)
# async def get_number(message: types.Message, state: FSMContext):
#     await state.update_data(number=message.text)
#     data = await state.get_data()
#     data["user_id"] = message.from_user.id
#     data["username"] = message.from_user.username

#     user = UserBase(
#         user_id=data.get('user_id'),
#         username=data.get('username'),
#         name=data.get('name'),
#         surname=data.get('surname'),
#         email=data.get('email'),
#         number=data.get('number')
#     )

#     try:
        

#         async with UserRepository() as db:
#             result = await db.add_user(user)

#         add_row(
#             user.username,
#             result.get('create'),
#             result.get('last_pay'),
#             'заблокирован',
#             'обычный пользователь',
#             user.user_id
#         )

#         await message.answer(text='✅Регистрация прошла успешно', reply_markup=Keyboards.inline_pay())
#         await state.clear()

#     except Exception as err:
#         await message.answer(text='Произошла какая то ошибка')
#         print(f'Error - {err}')
#         await state.clear()


