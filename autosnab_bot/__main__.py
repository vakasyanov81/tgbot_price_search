import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

from autosnab_bot import config, handlers
from autosnab_bot.services.product_types import get_product_types
from autosnab_bot.services.validate_user import ALLOWED_USER_IDS

COMMAND_HANDLERS = {
    'start': handlers.start,
    'help': handlers.help_,
    'pf': handlers.priceformation_menu,
    'source': handlers.choose_source,
}


async def _warm_up(_application: object) -> None:
    # Типы товара для меню внизу: CLI отвечает несколько секунд, первый поиск не должен его ждать.
    await get_product_types()


def check_config() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN variable wasn't implemented in .env.")
    if not ALLOWED_USER_IDS:
        raise ValueError('ALLOW_USER_LIST variable must contain at least one user ID in .env.')


def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    check_config()
    persistence = PicklePersistence(filepath=config.STATE_FILE)
    application = (
        ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).persistence(persistence).post_init(_warm_up).build()
    )

    for command_name, command_handler in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command_name, command_handler))

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.search))

    application.add_handler(MessageHandler(filters.Document.ALL, handlers.supplier_price_upload))

    application.add_handler(CallbackQueryHandler(handlers.set_source, pattern=f'^{handlers.SOURCE_CALLBACK_PREFIX}'))

    # block=False: пока priceformation формирует прайс, бот продолжает отвечать на поиск.
    application.add_handler(
        CallbackQueryHandler(
            handlers.priceformation_action,
            pattern=f'^{handlers.PF_CALLBACK_PREFIX}',
            block=False,
        )
    )

    application.add_error_handler(handlers.on_error)

    application.run_polling()


if __name__ == '__main__':
    main()
