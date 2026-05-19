import telebot
from telebot import types
from flask import Flask
import threading
import os
import json
import time

# ---------- TOKEN ----------

TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

# ---------- FLASK ----------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

# ---------- DATA ----------

waiting_users = []
chat_pairs = {}

user_states = {}
spam_control = {}

DATA_FILE = "users.json"

# ---------- LOAD USERS ----------

def load_users():

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    except:
        return {}

def save_users(data):

    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

users = load_users()

# ---------- MENU ----------

def menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add("🔍 Найти")

    markup.add(
        "❤️ Лайк",
        "⏭ Следующий"
    )

    markup.add(
        "👤 Профиль",
        "📊 Статистика"
    )

    markup.add(
        "🚫 Жалоба",
        "❌ Выйти"
    )

    return markup

# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(message):

    user_id = str(message.chat.id)

    if user_id not in users:

        users[user_id] = {
            "gender": "",
            "age": "",
            "likes": 0,
            "reports": 0
        }

        save_users(users)

        user_states[user_id] = "gender"

        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать\n\nВыбери пол:\nМ или Ж"
        )

    else:

        bot.send_message(
            message.chat.id,
            "🔥 Ты уже зарегистрирован",
            reply_markup=menu()
        )

# ---------- REGISTER ----------

@bot.message_handler(
    func=lambda m: str(m.chat.id) in user_states
)
def register(message):

    user_id = str(message.chat.id)

    state = user_states[user_id]

    # ----- GENDER -----

    if state == "gender":

        text = message.text.lower()

        if text not in ["м", "ж"]:

            bot.send_message(
                message.chat.id,
                "❌ Напиши М или Ж"
            )

            return

        users[user_id]["gender"] = text.upper()

        save_users(users)

        user_states[user_id] = "age"

        bot.send_message(
            message.chat.id,
            "🎂 Напиши возраст"
        )

    # ----- AGE -----

    elif state == "age":

        if not message.text.isdigit():

            bot.send_message(
                message.chat.id,
                "❌ Возраст цифрами"
            )

            return

        age = int(message.text)

        if age < 10 or age > 99:

            bot.send_message(
                message.chat.id,
                "❌ Возраст 10-99"
            )

            return

        users[user_id]["age"] = age

        save_users(users)

        del user_states[user_id]

        bot.send_message(
            message.chat.id,
            "✅ Регистрация завершена",
            reply_markup=menu()
        )

# ---------- PROFILE ----------

@bot.message_handler(
    func=lambda m: m.text == "👤 Профиль"
)
def profile(message):

    user_id = str(message.chat.id)

    if user_id not in users:
        return

    user = users[user_id]

    text = (
        f"👤 Профиль\n\n"
        f"Пол: {user['gender']}\n"
        f"Возраст: {user['age']}\n"
        f"Лайки: ❤️ {user['likes']}\n"
        f"Жалобы: 🚫 {user['reports']}"
    )

    bot.send_message(
        message.chat.id,
        text
    )

# ---------- STATS ----------

@bot.message_handler(
    func=lambda m: m.text == "📊 Статистика"
)
def stats(message):

    active = len(chat_pairs) // 2

    text = (
        f"👥 Пользователей: {len(users)}\n"
        f"💬 Активных чатов: {active}"
    )

    bot.send_message(
        message.chat.id,
        text
    )

# ---------- SEARCH ----------

@bot.message_handler(
    func=lambda m: m.text == "🔍 Найти"
)
def search(message):

    user_id = message.chat.id

    if user_id in chat_pairs:

        bot.send_message(
            user_id,
            "⚠️ Ты уже в чате"
        )

        return

    if user_id in waiting_users:

        bot.send_message(
            user_id,
            "⏳ Уже ищем собеседника"
        )

        return

    while waiting_users:

        partner = waiting_users.pop(0)

        if partner == user_id:
            continue

        chat_pairs[user_id] = partner
        chat_pairs[partner] = user_id

        bot.send_message(
            user_id,
            "✅ Собеседник найден"
        )

        bot.send_message(
            partner,
            "✅ Собеседник найден"
        )

        return

    waiting_users.append(user_id)

    bot.send_message(
        user_id,
        "🔎 Ищем собеседника..."
    )

# ---------- LIKE ----------

@bot.message_handler(
    func=lambda m: m.text == "❤️ Лайк"
)
def like(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
        return

    partner = str(chat_pairs[user_id])

    if partner not in users:
        return

    users[partner]["likes"] += 1

    save_users(users)

    bot.send_message(
        chat_pairs[user_id],
        "❤️ Ты понравился собеседнику"
    )

    bot.send_message(
        user_id,
        "❤️ Лайк отправлен"
    )

# ---------- REPORT ----------

@bot.message_handler(
    func=lambda m: m.text == "🚫 Жалоба"
)
def report(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
        return

    partner = str(chat_pairs[user_id])

    if partner not in users:
        return

    users[partner]["reports"] += 1

    save_users(users)

    bot.send_message(
        user_id,
        "🚫 Жалоба отправлена"
    )

# ---------- NEXT ----------

@bot.message_handler(
    func=lambda m: m.text == "⏭ Следующий"
)
def next_chat(message):

    user_id = message.chat.id

    if user_id in waiting_users:
        waiting_users.remove(user_id)

    if user_id in chat_pairs:

        partner = chat_pairs[user_id]

        chat_pairs.pop(user_id, None)
        chat_pairs.pop(partner, None)

        bot.send_message(
            partner,
            "❌ Собеседник отключился"
        )

    search(message)

# ---------- EXIT ----------

@bot.message_handler(
    func=lambda m: m.text == "❌ Выйти"
)
def stop_chat(message):

    user_id = message.chat.id

    if user_id in waiting_users:
        waiting_users.remove(user_id)

    if user_id in chat_pairs:

        partner = chat_pairs[user_id]

        chat_pairs.pop(user_id, None)
        chat_pairs.pop(partner, None)

        bot.send_message(
            partner,
            "❌ Собеседник вышел"
        )

    bot.send_message(
        user_id,
        "🚪 Ты вышел из чата",
        reply_markup=menu()
    )

# ---------- ANTISPAM ----------

def anti_spam(user_id):

    now = time.time()

    if user_id not in spam_control:
        spam_control[user_id] = []

    spam_control[user_id].append(now)

    spam_control[user_id] = [
        t for t in spam_control[user_id]
        if now - t < 5
    ]

    return len(spam_control[user_id]) > 7

# ---------- RELAY ----------

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "voice",
        "sticker"
    ]
)
def relay(message):

    user_id = message.chat.id

    if anti_spam(user_id):

        bot.send_message(
            user_id,
            "🚫 Слишком много сообщений"
        )

        return

    if user_id not in chat_pairs:
        return

    partner = chat_pairs[user_id]

    # ----- TEXT -----

    if message.content_type == "text":

        if len(message.text) > 1000:
            return

        commands = [
            "🔍 Найти",
            "❤️ Лайк",
            "⏭ Следующий",
            "👤 Профиль",
            "📊 Статистика",
            "🚫 Жалоба",
            "❌ Выйти"
        ]

        if message.text not in commands:

            bot.send_message(
                partner,
                message.text
            )

    # ----- PHOTO -----

    elif message.content_type == "photo":

        bot.send_photo(
            partner,
            message.photo[-1].file_id,
            caption=message.caption
        )

    # ----- VOICE -----

    elif message.content_type == "voice":

        bot.send_voice(
            partner,
            message.voice.file_id
        )

    # ----- STICKER -----

    elif message.content_type == "sticker":

        bot.send_sticker(
            partner,
            message.sticker.file_id
        )

# ---------- RUN BOT ----------

def run_bot():

    print("BOT STARTED")

    bot.infinity_polling(
        skip_pending=True
    )

# ---------- START THREAD ----------

threading.Thread(
    target=run_bot
).start()

# ---------- RUN FLASK ----------

port = int(os.environ.get("PORT", 10000))

app.run(
    host="0.0.0.0",
    port=port
)