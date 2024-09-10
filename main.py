import telebot
from config import TOKEN
import datetime


bot = telebot.TeleBot(TOKEN)
last_poll_time = bot.last_poll_time = None


@bot.message_handler(commands=['poll'])
def send_poll(message: telebot.types.Message):
    chat_id = message.chat.id
    question = 'Кто придет?'
    options = ['Я', 'Не я']
    bot.send_poll(chat_id, question, options, is_anonymous=False)

@bot.message_handler(commands=['reset'])
def reset_poll(message: telebot.types.Message):
    chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status in ['creator', 'administrator']:
        bot.last_poll_time = None
        bot.send_message(message.chat.id, "Опрос сброшен успешно!")
    else:
        bot.send_message(message.chat.id, "Только администраторы и владельцы чата могут сбросить опрос.")

@bot.message_handler(content_types=['text'])
def send_who_coming_poll(message: telebot.types.Message):
    if 'кто' in message.text.lower() and ('придет' in message.text.lower() or 'придёт' in message.text.lower()):
        current_time = datetime.datetime.now()
        if bot.last_poll_time is None or current_time.date() != bot.last_poll_time.date():
            chat_id = message.chat.id
            question = 'Кто придет?'
            options = ['Я', 'Не я']
            bot.send_poll(chat_id, question, options, is_anonymous=False)
            bot.last_poll_time = current_time

bot.polling()