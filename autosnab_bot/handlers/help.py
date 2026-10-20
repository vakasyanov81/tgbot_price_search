from typing import cast

from telegram import Update, User
from telegram.ext import ContextTypes

from autosnab_bot.services.response import send_response
from autosnab_bot.services.validate_user import check_admin, validate_user

INTRO = (
    'Напишите название позиции, бот найдёт её в прайсе (по умолчанию в прайсе для Дрома).\n'
    'Меню внизу — фильтр по типу товара: «Все» или конкретный тип.'
)
COMMANDS = [
    '/start - приветствие и описание бота',
    '/source - выбрать прайс для поиска',
    '/pf - сформировать прайсы, обновить и загрузить прайсы поставщиков',
]
ADMIN_COMMANDS = ['/script_manager - обновить код бота и перезапустить сервис']


@validate_user
async def help_(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = cast(User, update.effective_user).id
    commands = [*COMMANDS, *ADMIN_COMMANDS] if check_admin(user_id) else COMMANDS
    await send_response(update, context, response='\n'.join([INTRO, *commands]))
