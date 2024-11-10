from commands import CommandStateStore
from handlers import bot

command = CommandStateStore()


# Запускаем бота
bot.polling()
# price_list.load_price('price.xlsx')
# print(price_list.search('all'))
