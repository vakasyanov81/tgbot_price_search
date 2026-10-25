import logging
from typing import Any

from telegram.ext import (
    Application,
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
    'script_manager': handlers.script_manager,
}


async def _warm_up(_application: object) -> None:
    # Типы товара для меню внизу: CLI отвечает несколько секунд, первый поиск не должен его ждать.
    await get_product_types()


def check_config() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN variable wasn't implemented in .env.")
    if not ALLOWED_USER_IDS:
        raise ValueError('ALLOW_USER_LIST variable must contain at least one user ID in .env.')


def _setup_logging() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    # httpx на INFO пишет в лог полный URL запроса, а в нём токен бота.
    logging.getLogger('httpx').setLevel(logging.WARNING)


def _add_vendor_handlers(application: Application[Any, Any, Any, Any, Any, Any]) -> None:
    application.add_handler(
        CallbackQueryHandler(handlers.show_vendors, pattern=f'^{handlers.SCRIPT_VENDORS_CALLBACK}$', block=False)
    )
    application.add_handler(
        CallbackQueryHandler(handlers.switch_vendor, pattern=f'^{handlers.SCRIPT_VENDOR_PREFIX}', block=False)
    )


def _add_handlers(application: Application[Any, Any, Any, Any, Any, Any]) -> None:
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

    application.add_handler(
        CallbackQueryHandler(handlers.update_system, pattern=f'^{handlers.SCRIPT_UPDATE_CALLBACK}$', block=False)
    )

    application.add_handler(
        CallbackQueryHandler(handlers.export_logs, pattern=f'^{handlers.SCRIPT_LOGS_CALLBACK}$', block=False)
    )

    _add_vendor_handlers(application)

    application.add_error_handler(handlers.on_error)


def main() -> None:
    _setup_logging()
    check_config()
    persistence = PicklePersistence(filepath=config.STATE_FILE)
    application = (
        ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).persistence(persistence).post_init(_warm_up).build()
    )
    _add_handlers(application)
    application.run_polling()


if __name__ == '__main__':
    main()
