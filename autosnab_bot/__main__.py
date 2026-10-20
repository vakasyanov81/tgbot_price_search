import logging

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from autosnab_bot import config, handlers
from autosnab_bot.handlers.priceformation import CALLBACK_PREFIX
from autosnab_bot.services.validate_user import ALLOWED_USER_IDS

COMMAND_HANDLERS = {
    "start": handlers.start,
    "help": handlers.help_,
    "pf": handlers.priceformation_menu,
}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


if not config.TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN variable wasn't implemented in .env.")

if not ALLOWED_USER_IDS:
    raise ValueError("ALLOW_USER_LIST variable must contain at least one user ID in .env.")


def main() -> None:
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    for command_name, command_handler in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command_name, command_handler))

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.search))

    # Группа -1 раньше download: после выбора поставщика в /pf файл уходит в priceformation.
    application.add_handler(MessageHandler(filters.Document.ALL, handlers.supplier_price_upload), group=-1)
    application.add_handler(MessageHandler(filters.Document.ALL, handlers.download))

    # block=False: пока priceformation формирует прайс, бот продолжает отвечать на поиск.
    application.add_handler(
        CallbackQueryHandler(
            handlers.priceformation_action,
            pattern=f"^{CALLBACK_PREFIX}",
            block=False,
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()
