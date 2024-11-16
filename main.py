import telebot
from config import TOKEN
import datetime
import time
import json
import sqlite3
import os
import re


bot = telebot.TeleBot(TOKEN)
last_poll_time = bot.last_poll_time = None
chat_history = {}
words = []

with open('mat.txt', 'r') as f:
    words = f.read().splitlines()

if not os.path.exists('messages.json'):
    open('messages.json', 'w').close()

def create_tables():
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats
        (chat_id TEXT, user_id TEXT, username TEXT, messages INTEGER, PRIMARY KEY (chat_id, user_id))
    ''')
    conn.commit()
    conn.close()

create_tables()

def save_stats(chat_id, user_id, username, stats):
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO stats VALUES (?, ?, ?, ?)', (str(chat_id), str(user_id), username, stats['messages']))
    conn.commit()
    conn.close()

def load_stats(chat_id, user_id):
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, messages FROM stats WHERE chat_id=? AND user_id=?', (str(chat_id), str(user_id)))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {'username': result[0], 'messages': result[1]}
    else:
        return {'username': None, 'messages': 0}


@bot.message_handler(commands=['poll'])
def send_poll(message: telebot.types.Message):
    if message.chat.type == 'supergroup':
        chat_id = message.chat.id
        sender_status = bot.get_chat_member(chat_id, message.from_user.id).status
        if sender_status not in ['administrator', 'creator']:
            bot.reply_to(message, "Только администраторы и владельцы чата могут использовать эту команду.")
            bot.delete_message(chat_id, message.message_id)
            return
        question = 'Кто придет?'
        options = ['Я', 'Не я']
        poll_message = bot.send_poll(chat_id, question, options, is_anonymous=False)
        bot.pin_chat_message(chat_id, poll_message.message_id)
        bot.delete_message(chat_id, message.message_id)
    else:
        bot.reply_to(message, "Эту команду можно использовать только в группах.")
        bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(commands=['kick'])
def kick_user(message):
    if message.chat.type == 'supergroup':
        if message.reply_to_message:
            chat_id = message.chat.id
            user_id = message.reply_to_message.from_user.id
            sender_status = bot.get_chat_member(chat_id, message.from_user.id).status
            if sender_status not in ['administrator', 'creator']:
                bot.send_message(chat_id, "Только администраторы и владельцы чата могут использовать эту команду за это вы получите мут в течение 20 минут.")
                bot.restrict_chat_member(chat_id, message.from_user.id, until_date=time.time()+20*60)
                bot.delete_message(chat_id, message.id)
                return
            user_status = bot.get_chat_member(chat_id, user_id).status
            if user_status == 'administrator' or user_status == 'creator':
                bot.send_message(chat_id, "Нельзя кикнуть администратора.")
                bot.delete_message(chat_id, message.id)
            else:
                bot.kick_chat_member(chat_id, user_id)
                bot.send_message(chat_id, f"Пользователь {message.reply_to_message.from_user.username} был кикнут.")
                bot.delete_message(chat_id, message.id)
        else:
            bot.send_message(chat_id, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите кикнуть.")
            bot.delete_message(message.chat.id, message.id)
    else:
        bot.send_message(chat_id, "Эту команду можно использовать только в группах.")
        bot.delete_message(message.chat.id, message.id)


@bot.message_handler(commands=['mute'])
def mute_user(message):
    if message.chat.type == 'supergroup':
        if message.reply_to_message:
            chat_id = message.chat.id
            user_id = message.reply_to_message.from_user.id
            sender_status = bot.get_chat_member(chat_id, message.from_user.id).status
            if sender_status not in ['administrator', 'creator']:
                bot.send_message(chat_id, "Только администраторы и владельцы чата могут использовать эту команду за это вы получите мут в течение 20 минут.")
                bot.restrict_chat_member(chat_id, message.from_user.id, until_date=time.time()+20*60)
                bot.delete_message(chat_id, message.id)
                return
            else:
                args = message.text.split()[1:]
                if len(args) < 2:
                    bot.send_message(chat_id, "Неправильный формат команды. Используйте: /mute <время> <причина>")
                    bot.delete_message(chat_id, message.id)
                    return
                try:
                    muttime = int(args[0])
                except ValueError:
                    bot.send_message(chat_id, "Неправильный формат времени.")
                    bot.delete_message(chat_id, message.id)
                    return
                if muttime < 1:
                    bot.send_message(chat_id, "Время должно быть положительным числом.")
                    bot.delete_message(chat_id, message.id)
                    return
                if muttime > 1440:
                    bot.send_message(chat_id, "Максимальное время - 1 день.")
                    bot.delete_message(chat_id, message.id)
                    return
                reason = ' '.join(args[1:])
                bot.restrict_chat_member(chat_id, user_id, until_date=time.time()+muttime*60)
                bot.send_message(chat_id, f"Пользователь {message.reply_to_message.from_user.username} замучен на {muttime} минут.\nПричина: {reason}", reply_to_message_id=message.reply_to_message.message_id)
                bot.delete_message(chat_id, message.id)
        else:
            bot.send_message(message.chat.id, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите замутить.")
            bot.delete_message(message.chat.id, message.id)
    else:
        bot.send_message(chat_id, "Эту команду можно использовать только в группах.")
        bot.delete_message(message.chat.id, message.id)

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if message.chat.type == 'supergroup':
        if message.reply_to_message:
            chat_id = message.chat.id
            user_id = message.reply_to_message.from_user.id
            sender_status = bot.get_chat_member(chat_id, message.from_user.id).status
            if sender_status not in ['administrator', 'creator']:
                bot.send_message(message.chat.id, "Только администраторы и владельцы чата могут использовать эту команду за это вы получите мут в течение 20 минут.")
                bot.restrict_chat_member(chat_id, message.from_user.id, until_date=time.time()+20*60)
                bot.delete_message(message.chat.id, message.id)
                return
            bot.restrict_chat_member(chat_id, user_id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True, until_date=0)
            bot.send_message(message.chat.id, f"Пользователь {message.reply_to_message.from_user.username} размучен.")
            bot.delete_message(message.chat.id, message.id)
        else:
            bot.send_message(message.chat.id, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите размутить.")
            bot.delete_message(message.chat.id, message.id)
    else:
        bot.send_message(message.chat.id, "Эту команду можно использовать только в группах.")
        bot.delete_message(message.chat.id, message.id)

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.chat.type == 'supergroup':
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_stats = load_stats(chat_id, user_id)
        total_messages = 0
        with sqlite3.connect('stats.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(messages) FROM stats WHERE chat_id=?', (str(chat_id),))
            result = cursor.fetchone()
            if result:
                total_messages = result[0]
        try:
            bot.send_message(user_id, f"Всего сообщений в группе: {total_messages}\nСообщений от @{message.from_user.username}: {user_stats['messages']}")
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 403:
                bot.send_message(message.chat.id, "Надо создать чат с ботом https://t.me/poll_IT_clube_bot")
        bot.delete_message(message.chat.id, message.id)
    else:
        bot.send_message(chat_id, "Эту команду можно использовать только в группах.")
        bot.delete_message(message.chat.id, message.id)

translit_dict = {
    'a': 'а', 'b': 'б', 'e': 'е',
    'k': 'к', 'm': 'м',
    'o': 'о', 'p': 'р', 'q': 'к', 'r': 'р', 'c': 'с', 't': 'т',
    'x': 'х', 'y': 'у', 'z': 'з'
}

def check_message(message):
    message_text = message.text.lower()
    for char in message_text:
        if char.isalpha():
            message_text = message_text.replace(char, translit_dict.get(char, char))
    for word in words:
        if re.search(r'\b' + re.escape(word) + r'\b', message_text):
            return True
    return False


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username
    user_stats = load_stats(chat_id, user_id)
    user_stats['messages'] += 1
    save_stats(chat_id, user_id, username, user_stats)
    if chat_id not in chat_history:
        chat_history[chat_id] = {}
    if user_id not in chat_history[chat_id]:
        chat_history[chat_id][user_id] = {'messages': 0}
    chat_history[chat_id][user_id]['messages'] += 1
    
    user_name = message.from_user.username
    message_text = message.text
    with open('messages.json', 'r+') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        data.append({"user": user_name, "text": message_text})
        if len(data) > 10:
            data.pop(0) 
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    
    if 'кто' in message.text.lower() and ('придет' in message.text.lower() or 'придёт' in message.text.lower()):
        current_time = datetime.datetime.now()
        if bot.last_poll_time is None or current_time.date() != bot.last_poll_time.date():
            chat_id = message.chat.id
            chat = bot.get_chat(chat_id)
            if chat.pinned_message:
                bot.unpin_chat_message(chat_id) 
            question = 'Кто придет?'
            options = ['Я', 'Не я']
            poll_message = bot.send_poll(chat_id, question, options, is_anonymous=False)
            bot.pin_chat_message(chat_id, poll_message.message_id)
            bot.last_poll_time = current_time
    

    
    if check_message(message):
        if message.chat.type == 'supergroup':
            chat_id = message.chat.id
            user_id = message.from_user.id
            sender_status = bot.get_chat_member(chat_id, message.from_user.id).status
            if sender_status not in ['administrator', 'creator']:
                bot.restrict_chat_member(chat_id, user_id, until_date=time.time()+15*60)
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"Пользователь {message.from_user.username} был замучен на 15 минут за использование запрещенных слов")
            else:
                bot.send_message(chat_id, f"Так нельзя {message.from_user.username}.")
                bot.delete_message(chat_id, message.message_id)

bot.infinity_polling()