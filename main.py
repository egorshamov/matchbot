import telebot
import os

TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

waiting_users = []
chat_pairs = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Анонимный чат\n\n/search — поиск\n/next — следующий"
    )

@bot.message_handler(commands=['search'])
def search(message):
    user_id = message.chat.id

    if user_id in chat_pairs:
        bot.send_message(user_id, "Ты уже в чате")
        return

    if waiting_users:
        partner = waiting_users.pop(0)

        chat_pairs[user_id] = partner
        chat_pairs[partner] = user_id

        bot.send_message(user_id, "Собеседник найден")
        bot.send_message(partner, "Собеседник найден")
    else:
        waiting_users.append(user_id)
        bot.send_message(user_id, "Ищем собеседника...")

@bot.message_handler(commands=['next'])
def next_chat(message):
    user_id = message.chat.id

    if user_id in chat_pairs:
        partner = chat_pairs[user_id]

        del chat_pairs[user_id]
        del chat_pairs[partner]

        bot.send_message(partner, "Собеседник вышел")

    search(message)

@bot.message_handler(func=lambda m: True)
def relay(message):
    user_id = message.chat.id

    if user_id in chat_pairs:
        partner = chat_pairs[user_id]

        bot.send_message(
            partner,
            message.text
        )

bot.infinity_polling()