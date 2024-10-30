import json

import telebot

from commands import Commands, CommandStateStore
from config import Config
from file_upload import upload_file, clear_uploads
from price_list import prepare_search_result, get_instance_price_list

# Создаем экземпляр бота
bot = telebot.TeleBot(Config.TG_TOKEN)

price_list = get_instance_price_list(
    "PriceList", "PriceListSearch", f"{Config.UPLOAD_DIR}/price.xlsx"
)
price_list.load_price()

command_store = CommandStateStore()


# Обработчик команды /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    if not check_rights(message.from_user.id):
        replay_not_right_msg(message)
        return
    bot.reply_to(message, "Привет! Это бот для поиска позиций по прайс листу")


# Обработчик команды /help
@bot.message_handler(commands=["help"])
def send_welcome(message):
    if not check_rights(message.from_user.id):
        replay_not_right_msg(message)
        return
    bot.reply_to(
        message,
        "Для поиска по прайсу необходимо загрузить файл price.xlsx выполнив команду /download",
    )


# Обработчик команды /download
@bot.message_handler(commands=["download"])
def set_download_state(message):
    if not check_rights(message.from_user.id):
        replay_not_right_msg(message)
        return
    command_store.set_command(message.from_user.id, Commands.DOWNLOAD_PRICE)
    bot.reply_to(message, "Загрузите файл с остатками price.xlsx")


# Обработчик загрузки файла
@bot.message_handler(content_types=["document"])
def download_price(message):
    if not check_rights(message.from_user.id):
        replay_not_right_msg(message)
        return

    print(message)

    if command_store.current_state(message.from_user.id) != Commands.DOWNLOAD_PRICE:
        bot.reply_to(
            message,
            "Если необходимо загрузить прайс, воспользуйтесь командой /download",
        )
        return

    if ".xlsx" not in message.document.file_name:
        bot.reply_to(
            message,
            "Не верный формат файла. Необходим файл в формате xlsx",
        )
        return

    upload_file(bot.get_file(message.document.file_id), "price.xlsx", bot.download_file)
    price_list.load_price()
    command_store.clear(message.from_user.id)
    bot.reply_to(message, "Прайс загружен!")


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    if not check_rights(message.from_user.id):
        replay_not_right_msg(message)
        return
    # Load your API key from an environment variable or secret management service
    print(f"request: {message.text} / user_id={message.from_user.id}")
    result = price_list.search(message.text)
    response_txt = prepare_search_result(result)
    print(f"response: {response_txt}")
    bot.send_message(message.chat.id, f"Найдено {len(list(result.keys()))} позиций")
    bot.send_message(message.chat.id, response_txt, parse_mode="Markdown")


@bot.message_handler(content_types=["voice"])
def handle_docs_audio(message):
    if not check_rights(message.from_user.id):
        replay_not_right_msg(message)
        return
    # print(message)
    try:
        bot.send_message(message.chat.id, "Моя твоя не понимать. Давай текстом.")
    except Exception as exc:
        print(exc)
        bot.send_message(
            message.chat.id, "[!] error - {ошибка при загрузке голосового сообщения}"
        )
        raise


@bot.message_handler(content_types=["text"])
def handle_text(message):
    if not check_rights(message.from_user.id):
        replay_not_right_msg(message)
        return
    # print(message)
    try:
        clear_uploads(message.from_user.id)
        result = price_list.search(message.text.strip())
        response_txt = prepare_search_result(result)
        bot.send_message(message.chat.id, f"Найдено {len(list(result.keys()))} позиций")
        bot.send_message(message.chat.id, response_txt, parse_mode="Markdown")

    except Exception as exc:
        print(exc)
        bot.send_message(
            message.chat.id, "[!] error - {ошибка при загрузке голосового сообщения}"
        )
        raise


def check_rights(user_id):
    allow_users = json.loads(Config.ALLOW_USER_LIST)
    if int(user_id) not in allow_users:
        print(f"User blocked: {user_id}")
        return False
    return True


def replay_not_right_msg(message):
    bot.reply_to(
        message,
        f"У вас нет доступа, обратитесь к системному администратору! Ваш ID - {message.from_user.id}",
    )
