import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from autosnab_bot import config, handlers

COMMAND_HANDLERS = {
    "start": handlers.start,
    "help": handlers.help,
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


if not config.TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN variable wasn't implemented in .env.")


def main():
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    for command_name, command_handler in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command_name, command_handler))

    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.search)
    )

    application.add_handler(MessageHandler(filters.Document.ALL, handlers.download))

    application.run_polling()


if __name__ == "__main__":
    try:
        # price_list.load_price('price.xlsx')
        # print(price_list.search('all'))
        main()
    except Exception:
        import traceback

        logger.warning(traceback.format_exc())
