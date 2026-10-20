"""Меню /pf: команды CLI priceformation кнопками."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers import pf_upload
from autosnab_bot.handlers.pf_callbacks import (
    CANCEL_UPLOAD,
    CHOOSE_SUPPLIER,
    CONFIRM_UPLOAD,
    MAKE_PRICE,
    SHOW_HELP,
    SUPPLIER_PREFIX,
    UPDATE_ALL,
)
from autosnab_bot.services import priceformation
from autosnab_bot.services.priceformation_cli import README_FILE, is_available
from autosnab_bot.services.priceformation_output import log_block, update_report
from autosnab_bot.services.response import send_document, send_response
from autosnab_bot.services.validate_user import validate_user

type _Action = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]

# Пункты интерактивного меню CLI priceformation (без «выхода»).
MENU = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Сформировать общий прайс по прайсам поставщиков', callback_data=MAKE_PRICE)],
        [InlineKeyboardButton('Обновить прайсы всех поставщиков (API и почта)', callback_data=UPDATE_ALL)],
        [InlineKeyboardButton('Загрузить прайс поставщика', callback_data=CHOOSE_SUPPLIER)],
        [InlineKeyboardButton('Справка (README)', callback_data=SHOW_HELP)],
    ]
)


@validate_user
async def priceformation_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_available():
        not_found = 'Сабмодуль priceformation не найден. Выполните <code>git submodule update --init</code>'
        await send_response(update, context, response=not_found)
        return
    await send_response(update, context, response='Формирование прайсов:', keyboard=MENU)


@validate_user
async def priceformation_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    if query.data.startswith(SUPPLIER_PREFIX):
        await pf_upload.wait_supplier_files(update, context, query.data.removeprefix(SUPPLIER_PREFIX))
        return
    if query.data in _FILE_ACTIONS and priceformation.is_busy():
        await send_response(update, context, response='Уже выполняется другая команда, дождитесь её завершения')
        return
    action = _ACTIONS.get(query.data) or _FILE_ACTIONS.get(query.data)
    if action is not None:
        await action(update, context)


async def _show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_document(update, context, README_FILE)


async def _make_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_response(update, context, response='Формирую общий прайс, это может занять несколько минут…')
    outcome, files = await priceformation.make_price()
    status = 'Общий прайс сформирован' if outcome.ok else 'Ошибка при формировании прайса'
    await send_response(update, context, response=f'<b>{status}</b>\n{log_block(outcome.output)}')
    await asyncio.gather(*(send_document(update, context, path) for path in files))


async def _update_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_response(update, context, response='Обновляю прайсы поставщиков, это может занять несколько минут…')
    outcomes = await priceformation.update_all_prices()
    await send_response(update, context, response=update_report(outcomes))


# Кнопки, которые только читают или показывают.
_ACTIONS: dict[str, _Action] = {
    SHOW_HELP: _show_help,
    CHOOSE_SUPPLIER: pf_upload.choose_supplier,
    CANCEL_UPLOAD: pf_upload.cancel_upload,
}
# Кнопки, которые запускают команду, меняющую файлы priceformation: по одной за раз.
_FILE_ACTIONS: dict[str, _Action] = {
    MAKE_PRICE: _make_price,
    UPDATE_ALL: _update_all,
    CONFIRM_UPLOAD: pf_upload.upload_supplier_files,
}
