from commands import CommandStateStore
from handlers import bot

command = CommandStateStore()


# Запускаем бота
bot.infinity_polling(timeout=10, long_polling_timeout=5)
# price_list.load_price('price.xlsx')
# print(price_list.search('all'))
