"""Загрузка файлов поставщика в priceformation: выбор поставщика, сбор файлов, загрузка."""

import html
import tempfile
from pathlib import Path
from typing import Any

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.pf_upload_ui import CANCEL_BUTTON, download_files, show_collected, suppliers_keyboard
from autosnab_bot.services import priceformation, priceformation_reference
from autosnab_bot.services.priceformation_output import log_block
from autosnab_bot.services.response import send_response
from autosnab_bot.services.supplier_upload import PendingUpload, rejection, upload_report
from autosnab_bot.services.validate_user import validate_user

# Загрузка прайса поставщика, для которой собираем файлы (user_data).
PENDING_UPLOAD = 'pf_pending_upload'
_SUPPLIERS_CACHE = 'pf_suppliers'


async def choose_supplier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        suppliers = await priceformation_reference.get_suppliers()
    except RuntimeError as exc:
        failure = f'Не удалось получить список поставщиков:\n{log_block(str(exc))}'
        await send_response(update, context, response=failure)
        return
    context.bot_data[_SUPPLIERS_CACHE] = suppliers
    prompt = 'Выберите поставщика, для которого загрузить прайс:'
    await send_response(update, context, response=prompt, keyboard=suppliers_keyboard(suppliers))


async def wait_supplier_files(update: Update, context: ContextTypes.DEFAULT_TYPE, supplier_id: str) -> None:
    title = context.bot_data.get(_SUPPLIERS_CACHE, {}).get(supplier_id)
    if title is None:
        await send_response(update, context, response='Список поставщиков устарел, откройте его заново через /pf')
        return
    _user_data(context)[PENDING_UPLOAD] = PendingUpload(supplier_id, title)
    await send_response(
        update,
        context,
        response=f'Пришлите файлы поставщика «{html.escape(title)}»: xls, xlsx, json или zip-архив, '
        'можно несколько. Затем нажмите «Загрузить».',
        keyboard=InlineKeyboardMarkup([[CANCEL_BUTTON]]),
    )


async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _user_data(context).pop(PENDING_UPLOAD, None)
    await send_response(update, context, response='Загрузка прайса отменена')


@validate_user
async def supplier_price_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Файлы после выбора поставщика копятся для загрузки в priceformation."""
    document = update.message.document if update.message else None
    if document is None:
        return
    pending: PendingUpload | None = _user_data(context).get(PENDING_UPLOAD)
    reason = rejection(document) if pending else 'Чтобы загрузить прайс поставщика, выберите его: /pf'
    if reason or pending is None:
        await send_response(update, context, response=reason)
        return
    pending.add(document)
    await show_collected(update, context, pending)


async def upload_supplier_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending: PendingUpload | None = _user_data(context).pop(PENDING_UPLOAD, None)
    if pending is None or not pending.files:
        await send_response(update, context, response='Нет файлов для загрузки, выберите поставщика заново через /pf')
        return
    with tempfile.TemporaryDirectory() as tmp_dir:
        sources = await download_files(context, pending, Path(tmp_dir))
        outcome = await priceformation.load_supplier_prices(pending.supplier_id, sources)
    await send_response(update, context, response=upload_report(pending.title, outcome))


def _user_data(context: ContextTypes.DEFAULT_TYPE) -> dict[Any, Any]:
    if context.user_data is None:
        raise RuntimeError('user_data недоступна для этого обновления')
    return context.user_data
