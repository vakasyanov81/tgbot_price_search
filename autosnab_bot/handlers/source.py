import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from autosnab_bot.services.price_sources import PriceSource, get_sources
from autosnab_bot.services.response import send_response
from autosnab_bot.services.type_menu import USER_SOURCE, USER_TYPE_FILTER, user_source, user_type_filter
from autosnab_bot.services.validate_user import validate_user

CALLBACK_PREFIX = 'src:'


@validate_user
async def choose_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = user_source(context)
    keyboard = InlineKeyboardMarkup([[_source_button(source, current)] for source in get_sources()])
    await send_response(
        update,
        context,
        response=f'Сейчас поиск идёт по: <b>{html.escape(current.title)}</b>\nВыберите прайс для поиска:',
        keyboard=keyboard,
    )


@validate_user
async def set_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    key = query.data.removeprefix(CALLBACK_PREFIX)
    source = next((entry for entry in get_sources() if entry.key == key), None)
    if source is None or context.user_data is None:
        return
    context.user_data[USER_SOURCE] = source.key
    if await user_type_filter(context, source) is None:
        context.user_data.pop(USER_TYPE_FILTER, None)
    note = '' if source.latest_file() else f'\nЭтот прайс ещё не сформирован. {source.how_to_make}.'
    chosen = f'Поиск будет идти по: <b>{html.escape(source.title)}</b>'
    await send_response(update, context, response=f'{chosen}{note}')


def _source_button(source: PriceSource, current: PriceSource) -> InlineKeyboardButton:
    """Кнопка прайса: текущий отмечен, рядом — файл, по которому идёт поиск."""
    path = source.latest_file()
    mark = '✅ ' if source == current else ''
    state = f': {path.name}' if path else ' (не сформирован)'
    return InlineKeyboardButton(f'{mark}{source.title}{state}', callback_data=f'{CALLBACK_PREFIX}{source.key}')
