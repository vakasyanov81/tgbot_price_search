from typing import cast

from telegram import Chat, InlineKeyboardMarkup, LinkPreviewOptions, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def send_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    response: str,
    keyboard: InlineKeyboardMarkup | None = None,
) -> None:
    args = {}
    if keyboard:
        args["reply_markup"] = keyboard
    await context.bot.send_message(
        chat_id=_get_chat_id(update),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
        text=response,
        parse_mode=ParseMode.HTML,
        **args,
    )


def _get_chat_id(update: Update) -> int:
    return cast(Chat, update.effective_chat).id
