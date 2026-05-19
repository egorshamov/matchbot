import telebot
from telebot import types
from flask import Flask
import threading
import os
import json
import time

TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

# ---------------- FLASK ----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Match is running"

# ---------------- DATA ----------------

DATA_FILE = "users.json"

waiting_users = []
chat_pairs = {}

user_states = {}
spam_control = {}

likes = {}

# ---------------- LOAD ----------------

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

# ---------------- MENU ----------------

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
        "📊 Онлайн"
    )

    markup.add(
        "🚫 Жалоба",
        "❌ Выйти"
    )

    return markup

# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(message):

    user_id = str(message.chat.id)

    if user_id not in users:

        users[user_id] = {
            "gender": "",
            "search": "",
            "age": "",
            "bio": "",
            "photo": "",
            "likes": 0,
            "reports": 0
        }

        save_users(users)

        user_states[user_id] = "gender"

        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать в Match\n\n"
            "Выбери свой пол:\n"
            "М или Ж"
        )

    else:

        bot.send_message(
            message.chat.id,
            "🔥 С возвращением в Match",
            reply_markup=menu()
        )

# ---------------- REGISTER ----------------

@bot.message_handler(
    func=lambda m: str(m.chat.id) in user_states
)
def register(message):

    user_id = str(message.chat.id)

    state = user_states[user_id]

    # -------- GENDER --------

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

        user_states[user_id] = "search"

        bot.send_message(
            message.chat.id,
            "🔎 Кого ищешь?\n\n"
            "М / Ж / Л"
        )

    # -------- SEARCH --------

    elif state == "search":

        text = message.text.lower()

        if text not in ["м", "ж", "л"]:

            bot.send_message(
                message.chat.id,
                "❌ Напиши М / Ж / Л"
            )

            return

        users[user_id]["search"] = text.upper()

        save_users(users)

        user_states[user_id] = "age"

        bot.send_message(
            message.chat.id,
            "🎂 Напиши возраст"
        )

    # -------- AGE --------

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

        user_states[user_id] = "bio"

        bot.send_message(
            message.chat.id,
            "📝 Напиши описание о себе"
        )

    # -------- BIO --------

    elif state == "bio":

        users[user_id]["bio"] = message.text[:300]

        save_users(users)

        user_states[user_id] = "photo"

        bot.send_message(
            message.chat.id,
            "📸 Отправь фото профиля"
        )

# ---------------- PHOTO REGISTER ----------------

@bot.message_handler(
    content_types=["photo"]
)
def photo_handler(message):

    user_id = str(message.chat.id)

    # ----- регистрация -----

    if user_id in user_states:

        if user_states[user_id] == "photo":

            users[user_id]["photo"] = message.photo[-1].file_id

            save_users(users)

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "✅ Профиль создан",
                reply_markup=menu()
            )

            return

    # ----- чат -----

    if message.chat.id in chat_pairs:

        partner = chat_pairs[message.chat.id]

        bot.send_photo(
            partner,
            message.photo[-1].file_id,
            caption=message.caption
        )

# ---------------- PROFILE ----------------

@bot.message_handler(
    func=lambda m: m.text == "👤 Профиль"
)
def profile(message):

    user_id = str(message.chat.id)

    if user_id not in users:
        return

    user = users[user_id]

    text = (
        f"👤 Твой профиль\n\n"
        f"Пол: {user['gender']}\n"
        f"Возраст: {user['age']}\n"
        f"Описание: {user['bio']}\n\n"
        f"❤️ Лайки: {user['likes']}\n"
        f"🚫 Жалобы: {user['reports']}"
    )

    if user["photo"]:

        bot.send_photo(
            message.chat.id,
            user["photo"],
            caption=text
        )

    else:

        bot.send_message(
            message.chat.id,
            text
        )

# ---------------- ONLINE ----------------

@bot.message_handler(
    func=lambda m: m.text == "📊 Онлайн"
)
def online(message):

    bot.send_message(
        message.chat.id,
        f"👥 Пользователей: {len(users)}\n"
        f"💬 Активных чатов: {len(chat_pairs)//2}"
    )

# ---------------- COMPATIBLE ----------------

def compatible(user1, user2):

    u1 = users[str(user1)]
    u2 = users[str(user2)]

    if u1["search"] == "Л":
        return True

    return u1["search"] == u2["gender"]

# ---------------- SEARCH ----------------

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
            "⏳ Уже ищем"
        )

        return

    while waiting_users:

        partner = waiting_users.pop(0)

        if partner == user_id:
            continue

        if not compatible(user_id, partner):
            continue

        chat_pairs[user_id] = partner
        chat_pairs[partner] = user_id

        p = users[str(partner)]

        text = (
            f"💬 Собеседник найден\n\n"
            f"Пол: {p['gender']}\n"
            f"Возраст: {p['age']}\n"
            f"{p['bio']}"
        )

        if p["photo"]:

            bot.send_photo(
                user_id,
                p["photo"],
                caption=text
            )

        else:

            bot.send_message(
                user_id,
                text
            )

        bot.send_message(
            partner,
            "💬 Собеседник найден"
        )

        return

    waiting_users.append(user_id)

    bot.send_message(
        user_id,
        "🔎 Ищем собеседника..."
    )

# ---------------- LIKE ----------------

@bot.message_handler(
    func=lambda m: m.text == "❤️ Лайк"
)
def like(message):

    user_id = str(message.chat.id)

    if message.chat.id not in chat_pairs:

        bot.send_message(
            message.chat.id,
            "❌ Лайк доступен только во время общения"
        )

        return

    partner = str(chat_pairs[message.chat.id])

    if partner not in likes:
        likes[partner] = []

    if user_id in likes[partner]:

        bot.send_message(
            message.chat.id,
            "⚠️ Ты уже отправил лайк"
        )

        return

    likes[partner].append(user_id)

    users[partner]["likes"] += 1

    save_users(users)

    bot.send_message(
        int(partner),
        "❤️ Ты понравился собеседнику"
    )

    bot.send_message(
        message.chat.id,
        "❤️ Лайк отправлен"
    )

    # ----- взаимный лайк -----

    if (
        user_id in likes
        and partner in likes[user_id]
    ):

        bot.send_message(
            int(user_id),
            "💘 Взаимная симпатия!"
        )

        bot.send_message(
            int(partner),
            "💘 Взаимная симпатия!"
        )

# ---------------- REPORT ----------------

@bot.message_handler(
    func=lambda m: m.text == "🚫 Жалоба"
)
def report(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:

        bot.send_message(
            user_id,
            "❌ Жалоба доступна только в чате"
        )

        return

    partner = str(chat_pairs[user_id])

    users[partner]["reports"] += 1

    save_users(users)

    bot.send_message(
        user_id,
        "🚫 Жалоба отправлена"
    )

    real_partner = chat_pairs[user_id]

    chat_pairs.pop(user_id, None)
    chat_pairs.pop(real_partner, None)

    bot.send_message(
        real_partner,
        "❌ Собеседник завершил диалог"
    )

    bot.send_message(
        user_id,
        "🚪 Диалог завершён"
    )

# ---------------- NEXT ----------------

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

# ---------------- EXIT ----------------

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
        "🚪 Ты вышел",
        reply_markup=menu()
    )

# ---------------- ANTISPAM ----------------

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

# ---------------- RELAY ----------------

@bot.message_handler(
    content_types=[
        "text",
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

    # -------- TEXT --------

    if message.content_type == "text":

        commands = [
            "🔍 Найти",
            "❤️ Лайк",
            "⏭ Следующий",
            "👤 Профиль",
            "📊 Онлайн",
            "🚫 Жалоба",
            "❌ Выйти"
        ]

        if message.text not in commands:

            bot.send_message(
                partner,
                message.text[:1000]
            )

    # -------- VOICE --------

    elif message.content_type == "voice":

        bot.send_voice(
            partner,
            message.voice.file_id
        )

    # -------- STICKER --------

    elif message.content_type == "sticker":

        bot.send_sticker(
            partner,
            message.sticker.file_id
        )

# ---------------- RUN BOT ----------------

def run_bot():

    print("MATCH STARTED")

    bot.infinity_polling(
        skip_pending=True
    )

# ---------------- THREAD ----------------

threading.Thread(
    target=run_bot
).start()

# ---------------- FLASK ----------------

port = int(os.environ.get("PORT", 10000))

app.run(
    host="0.0.0.0",
    port=port
)