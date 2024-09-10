import telebot
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text'])
def send_who_coming_poll(message : telebot.types.Message):
    if 'кто' in message.text.lower() and 'придет' in message.text.lower():
        chat_id = message.chat.id
        question = 'Кто придет?'
        options = ['Я', 'Не я']
        bot.send_poll(chat_id, question, options, is_anonymous=False)

bot.polling()