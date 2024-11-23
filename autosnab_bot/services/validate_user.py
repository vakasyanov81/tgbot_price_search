from typing import cast

from telegram import Update, User
from telegram.ext import ContextTypes

from autosnab_bot import config
from autosnab_bot.handlers.response import send_response


async def check_rights(user_id):
    if not config.ALLOW_USER_LIST:
        return True

    allow_users: list[int] = [
        int(id_) for id_ in str(config.ALLOW_USER_LIST).split(",")
    ]
    if int(user_id) not in allow_users:
        return False
    return True


def validate_user(handler):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = cast(User, update.effective_user).id
        if not await check_rights(user_id):
            await send_response(
                update,
                context,
                response=f"У вас нет доступа, обратитесь к системному администратору! Ваш ID - {user_id}",
            )
            return
        await handler(update, context)

    return wrapped
