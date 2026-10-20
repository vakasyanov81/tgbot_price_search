import functools
from collections.abc import Callable, Coroutine
from typing import Any, cast

from telegram import Update, User
from telegram.ext import ContextTypes

from autosnab_bot import config
from autosnab_bot.services.response import send_response

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]


def _parse_allow_list(raw: str) -> frozenset[int]:
    return frozenset(int(item) for item in raw.split(",") if item.strip())


ALLOWED_USER_IDS = _parse_allow_list(config.ALLOW_USER_LIST)


def check_rights(user_id: int) -> bool:
    return user_id in ALLOWED_USER_IDS


def validate_user(handler: Handler) -> Handler:
    @functools.wraps(handler)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = cast(User, update.effective_user).id
        if not check_rights(user_id):
            await send_response(
                update,
                context,
                response=f"У вас нет доступа, обратитесь к системному администратору! Ваш ID - {user_id}",
                with_menu=False,
            )
            return
        await handler(update, context)

    return wrapped
