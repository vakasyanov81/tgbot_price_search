from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.type_filter import send_type_menu
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def help_(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_type_menu(
        update,
        context,
        "Напишите название позиции, бот найдёт её в прайсе (по умолчанию в прайсе для Дрома).\n"
        "Меню внизу — фильтр по типу товара: «Все» или конкретный тип.\n"
        "/source - выбрать прайс для поиска\n"
        "/pf - сформировать прайсы, обновить и загрузить прайсы поставщиков",
    )
