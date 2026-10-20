import functools
from collections.abc import Callable, Coroutine
from typing import Any, cast

from telegram import Update, User
from telegram.ext import ContextTypes

from autosnab_bot import config
from autosnab_bot.services.response import send_response

type _Done = Coroutine[Any, Any, None]
type BotCallback = Callable[[Update, ContextTypes.DEFAULT_TYPE], _Done]


def _parse_allow_list(raw: str) -> frozenset[int]:
    user_ids = (chunk.strip() for chunk in raw.split(','))
    return frozenset(int(user_id) for user_id in user_ids if user_id)


ALLOWED_USER_IDS = _parse_allow_list(config.ALLOW_USER_LIST)


def check_rights(user_id: int) -> bool:
    return user_id in ALLOWED_USER_IDS


def validate_user(callback: BotCallback) -> BotCallback:
    @functools.wraps(callback)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = cast(User, update.effective_user).id
        if not check_rights(user_id):
            await send_response(
                update,
                context,
                response=f'У вас нет доступа, обратитесь к системному администратору! Ваш ID - {user_id}',
                with_menu=False,
            )
            return
        await callback(update, context)

    return wrapped
