"""Интерфейс загрузки поставщика в Telegram: выбор поставщика, список собранных файлов, скачивание."""

import asyncio
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from autosnab_bot.handlers.pf_callbacks import CANCEL_UPLOAD, CONFIRM_UPLOAD, SUPPLIER_PREFIX
from autosnab_bot.services.response import send_response
from autosnab_bot.services.supplier_upload import PendingUpload

CANCEL_BUTTON = InlineKeyboardButton('Отмена', callback_data=CANCEL_UPLOAD)
UPLOAD_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton('Загрузить', callback_data=CONFIRM_UPLOAD),
            CANCEL_BUTTON,
        ]
    ]
)


async def show_collected(update: Update, context: ContextTypes.DEFAULT_TYPE, pending: PendingUpload) -> None:
    """Одно сообщение со списком файлов: альбом из нескольких файлов не плодит ответов."""
    text = pending.collected_text()
    if pending.status_message_id is not None:
        edited = await _edit_status(update, context, pending.status_message_id, text)
        if edited:
            return
    status = await send_response(update, context, response=text, keyboard=UPLOAD_KEYBOARD)
    pending.status_message_id = status.message_id


async def download_files(context: ContextTypes.DEFAULT_TYPE, pending: PendingUpload, folder: Path) -> list[Path]:
    """Скачать собранные файлы во временную папку folder."""
    targets = pending.targets(folder)
    downloads = [_download(context, *download_target) for download_target in targets]
    return list(await asyncio.gather(*downloads))


def suppliers_keyboard(suppliers: dict[str, str]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(title, callback_data=f'{SUPPLIER_PREFIX}{supplier_id}')]
        for supplier_id, title in sorted(suppliers.items(), key=_by_title)
    ]
    return InlineKeyboardMarkup([*buttons, [CANCEL_BUTTON]])


async def _edit_status(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int, text: str) -> bool:
    """Обновить сообщение со списком файлов; False — его уже нельзя изменить (удалено или старое)."""
    chat_id = update.effective_chat.id if update.effective_chat else None
    try:
        await context.bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode=ParseMode.HTML,
            reply_markup=UPLOAD_KEYBOARD,
        )
    except BadRequest:
        return False
    return True


async def _download(context: ContextTypes.DEFAULT_TYPE, file_id: str, target: Path) -> Path:
    target.parent.mkdir(parents=True)
    telegram_file = await context.bot.get_file(file_id)
    await telegram_file.download_to_drive(target)
    return target


def _by_title(supplier: tuple[str, str]) -> str:
    return supplier[1].lower()
