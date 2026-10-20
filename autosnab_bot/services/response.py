from pathlib import Path
from typing import cast

from telegram import Chat, InlineKeyboardMarkup, LinkPreviewOptions, Message, ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def send_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    response: str,
    keyboard: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
) -> Message:
    args = {}
    if keyboard:
        args["reply_markup"] = keyboard
    return await context.bot.send_message(
        chat_id=_get_chat_id(update),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
        text=response,
        parse_mode=ParseMode.HTML,
        **args,
    )


async def edit_response(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int, response: str) -> None:
    await context.bot.edit_message_text(
        chat_id=_get_chat_id(update),
        message_id=message_id,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
        text=response,
        parse_mode=ParseMode.HTML,
    )


async def send_document(update: Update, context: ContextTypes.DEFAULT_TYPE, path: Path) -> None:
    with path.open("rb") as document:
        await context.bot.send_document(chat_id=_get_chat_id(update), document=document, filename=path.name)


def _get_chat_id(update: Update) -> int:
    return cast(Chat, update.effective_chat).id
