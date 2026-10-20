import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.search import USER_SOURCE, user_source
from autosnab_bot.services.price_sources import SOURCES, SOURCES_BY_KEY
from autosnab_bot.services.response import send_response
from autosnab_bot.services.validate_user import validate_user

CALLBACK_PREFIX = "src:"


@validate_user
async def choose_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = user_source(context)
    buttons = []
    for source in SOURCES:
        path = source.latest_file()
        mark = "✅ " if source == current else ""
        label = f"{mark}{source.title}: {path.name}" if path else f"{mark}{source.title} (не сформирован)"
        buttons.append([InlineKeyboardButton(label, callback_data=CALLBACK_PREFIX + source.key)])
    await send_response(
        update,
        context,
        response=f"Сейчас поиск идёт по: <b>{html.escape(current.title)}</b>\nВыберите прайс для поиска:",
        keyboard=InlineKeyboardMarkup(buttons),
    )


@validate_user
async def set_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    source = SOURCES_BY_KEY.get(query.data.removeprefix(CALLBACK_PREFIX))
    if source is None or context.user_data is None:
        return
    context.user_data[USER_SOURCE] = source.key
    note = "" if source.latest_file() else f"\nЭтот прайс ещё не сформирован. {source.how_to_make}."
    await send_response(update, context, response=f"Поиск будет идти по: <b>{html.escape(source.title)}</b>{note}")
