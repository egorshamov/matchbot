import telebot
from telebot import types

import json
import threading
import os

from flask import Flask

# =========================================
# CONFIG
# =========================================

TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

# =========================================
# FLASK
# =========================================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )

# =========================================
# FILES
# =========================================

USERS_FILE = "users.json"

def load_users():

    try:

        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return {}

def save_users():

    data = {
        "users": users,
        "likes": likes,
        "matches": matches
    }

    with open(
        USERS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )

data = load_users()

users = data.get("users", {})
likes = data.get("likes", {})
matches = data.get("matches", {})

# =========================================
# DATA
# =========================================

user_states = {}

waiting_users = []

chat_pairs = {}

# =========================================
# MENU
# =========================================

def menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add("🔍 Найти")

    markup.add(
        "👤 Профиль",
        "📊 Онлайн"
    )

    markup.add(
        "🔥 Мои MATCH",
        "🗑 Удалить профиль"
    )

    return markup

# =========================================
# CHAT MENU
# =========================================

def chat_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        "❤️ Лайк",
        "⏭ Следующий"
    )

    markup.add(
        "🚫 Жалоба",
        "❌ Выйти"
    )

    return markup

# =========================================
# PROFILE MENU
# =========================================

def profile_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add("✏️ Изменить описание")

    markup.add("📸 Изменить фото")

    markup.add(
        "🎂 Изменить возраст",
        "⚧ Изменить пол"
    )

    markup.add("🔎 Изменить поиск")

    markup.add("↩️ Назад")

    return markup

# =========================================
# SKIP
# =========================================

def skip_markup():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add("⏭ Пропустить")

    markup.add("↩️ Назад")

    return markup

# =========================================
# START
# =========================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = str(message.chat.id)

    if user_id not in users:

        users[user_id] = {
            "gender": "",
            "search": "",
            "age": "",
            "bio": "",
            "photo": ""
        }

        save_users()

        user_states[user_id] = "gender"

        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать\n\nНапиши М или Ж",
            reply_markup=skip_markup()
        )

    else:

        bot.send_message(
            message.chat.id,
            "🏠 Главное меню",
            reply_markup=menu()
        )

# =========================================
# BACK
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "↩️ Назад"
)
def back(message):

    user_id = str(message.chat.id)

    if user_id in user_states:

        state = user_states[user_id]

        if state == "search":

            user_states[user_id] = "gender"

            bot.send_message(
                message.chat.id,
                "↩️ Вернулись назад\n\nНапиши М или Ж"
            )

            return

        elif state == "age":

            user_states[user_id] = "search"

            bot.send_message(
                message.chat.id,
                "↩️ Вернулись назад\n\nМ / Ж / Л"
            )

            return

        elif state == "bio":

            user_states[user_id] = "age"

            bot.send_message(
                message.chat.id,
                "↩️ Вернулись назад\n\nНапиши возраст"
            )

            return

        elif state == "photo":

            user_states[user_id] = "bio"

            bot.send_message(
                message.chat.id,
                "↩️ Вернулись назад\n\nНапиши описание",
                reply_markup=skip_markup()
            )

            return

        del user_states[user_id]

    bot.send_message(
        message.chat.id,
        "🏠 Главное меню",
        reply_markup=menu()
    )

# =========================================
# STATES
# =========================================

@bot.message_handler(
    func=lambda m:
    str(m.chat.id) in user_states
)
def states(message):

    user_id = str(message.chat.id)

    state = user_states[user_id]

    # GENDER

    if state == "gender":

        text = message.text.lower()

        if text not in ["м", "ж"]:

            bot.send_message(
                message.chat.id,
                "❌ Напиши М или Ж"
            )

            return

        users[user_id]["gender"] = text.upper()

        save_users()

        user_states[user_id] = "search"

        bot.send_message(
            message.chat.id,
            "🔎 Кого ищешь?\n\nМ / Ж / Л"
        )

    # SEARCH

    elif state == "search":

        text = message.text.lower()

        if text not in ["м", "ж", "л"]:

            bot.send_message(
                message.chat.id,
                "❌ Напиши М / Ж / Л"
            )

            return

        users[user_id]["search"] = text.upper()

        save_users()

        user_states[user_id] = "age"

        bot.send_message(
            message.chat.id,
            "🎂 Напиши возраст"
        )

    # AGE

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

        save_users()

        user_states[user_id] = "bio"

        bot.send_message(
            message.chat.id,
            "📝 Напиши описание\n\nИли ⏭ Пропустить",
            reply_markup=skip_markup()
        )

    # BIO

    elif state == "bio":

        if message.text != "⏭ Пропустить":

            users[user_id]["bio"] = message.text[:300]

            save_users()

        user_states[user_id] = "photo"

        bot.send_message(
            message.chat.id,
            "📸 Отправь фото\n\nИли ⏭ Пропустить",
            reply_markup=skip_markup()
        )

    # PHOTO

    elif state == "photo":

        if message.text == "⏭ Пропустить":

            users[user_id]["photo"] = ""

            save_users()

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "✅ Профиль создан",
                reply_markup=menu()
            )

            return

        if message.photo:

            users[user_id]["photo"] = (
                message.photo[-1].file_id
            )

            save_users()

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "✅ Профиль создан",
                reply_markup=menu()
            )

    # EDIT BIO

    elif state == "edit_bio":

        if message.text != "⏭ Пропустить":

            users[user_id]["bio"] = message.text[:300]

            save_users()

        del user_states[user_id]

        bot.send_message(
            message.chat.id,
            "✅ Описание изменено",
            reply_markup=profile_menu()
        )

    # EDIT PHOTO

    elif state == "edit_photo":

        if message.text == "⏭ Пропустить":

            users[user_id]["photo"] = ""

            save_users()

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "✅ Фото удалено",
                reply_markup=profile_menu()
            )

            return

        if message.photo:

            users[user_id]["photo"] = (
                message.photo[-1].file_id
            )

            save_users()

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "✅ Фото изменено",
                reply_markup=profile_menu()
            )

# =========================================
# PROFILE
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "👤 Профиль"
)
def profile(message):

    user_id = str(message.chat.id)

    if user_id not in users:

        bot.send_message(
            message.chat.id,
            "❌ Профиль не найден"
        )

        return

    user = users[user_id]

    username = message.from_user.username

    if username:
        username = f"@{username}"
    else:
        username = f"ID: {user_id}"

    text = (
        f"{username}\n\n"
        f"👤 Пол: {user['gender']}\n"
        f"🔎 Поиск: {user['search']}\n"
        f"🎂 Возраст: {user['age']}\n\n"
        f"📝 {user['bio']}"
    )

    if user["photo"]:

        bot.send_photo(
            message.chat.id,
            user["photo"],
            caption=text,
            reply_markup=profile_menu()
        )

    else:

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=profile_menu()
        )

# =========================================
# ONLINE
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "📊 Онлайн"
)
def online(message):

    bot.send_message(
        message.chat.id,
        f"👥 Пользователей: {len(users)}"
    )

# =========================================
# EDIT PROFILE
# =========================================

@bot.message_handler(
    func=lambda m:
    m.text == "✏️ Изменить описание"
)
def edit_bio(message):

    user_states[str(message.chat.id)] = "edit_bio"

    bot.send_message(
        message.chat.id,
        "📝 Отправь новое описание",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m:
    m.text == "📸 Изменить фото"
)
def edit_photo(message):

    user_states[str(message.chat.id)] = "edit_photo"

    bot.send_message(
        message.chat.id,
        "📸 Отправь новое фото",
        reply_markup=skip_markup()
    )

# =========================================
# SEARCH
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "🔍 Найти"
)
def find_chat(message):

    user_id = message.chat.id

    if user_id in chat_pairs:

        bot.send_message(
            message.chat.id,
            "❌ Ты уже в чате"
        )

        return

    if user_id in waiting_users:

        bot.send_message(
            message.chat.id,
            "⏳ Уже ищем собеседника"
        )

        return

    if waiting_users:

        partner = waiting_users.pop(0)

        if partner == user_id:

            waiting_users.append(user_id)

            return

        chat_pairs[user_id] = partner
        chat_pairs[partner] = user_id

        bot.send_message(
            user_id,
            "✅ Собеседник найден",
            reply_markup=chat_menu()
        )

        bot.send_message(
            partner,
            "✅ Собеседник найден",
            reply_markup=chat_menu()
        )

    else:

        waiting_users.append(user_id)

        bot.send_message(
            message.chat.id,
            "🔍 Ищем собеседника..."
        )

# =========================================
# LIKE + MATCH
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "❤️ Лайк"
)
def like_user(message):

    user_id = str(message.chat.id)

    if int(user_id) not in chat_pairs:
        return

    partner = str(chat_pairs[int(user_id)])

    likes.setdefault(partner, [])

    if user_id not in likes[partner]:

        likes[partner].append(user_id)

    likes.setdefault(user_id, [])

    # MATCH

    if partner in likes[user_id]:

        matches.setdefault(user_id, [])
        matches.setdefault(partner, [])

        if partner not in matches[user_id]:
            matches[user_id].append(partner)

        if user_id not in matches[partner]:
            matches[partner].append(user_id)

        save_users()

        bot.send_message(
            int(user_id),
            "🔥 У вас взаимная симпатия!"
        )

        bot.send_message(
            int(partner),
            "🔥 У вас взаимная симпатия!"
        )

    save_users()

    bot.send_message(
        int(user_id),
        "❤️ Лайк отправлен"
    )

# =========================================
# MY MATCHES
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "🔥 Мои MATCH"
)
def my_matches(message):

    user_id = str(message.chat.id)

    if user_id not in matches:

        bot.send_message(
            message.chat.id,
            "❌ У тебя пока нет MATCH"
        )

        return

    if not matches[user_id]:

        bot.send_message(
            message.chat.id,
            "❌ У тебя пока нет MATCH"
        )

        return

    text = "🔥 Твои MATCH:\n\n"

    for partner_id in matches[user_id]:

        if partner_id not in users:
            continue

        user = users[partner_id]

        text += (
            f"👤 {user['gender']} | "
            f"{user['age']} лет\n"
        )

        if user["bio"]:
            text += f"📝 {user['bio']}\n"

        text += f"🆔 {partner_id}\n\n"

    bot.send_message(
        message.chat.id,
        text
    )

# =========================================
# NEXT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "⏭ Следующий"
)
def next_chat(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:

        bot.send_message(
            message.chat.id,
            "❌ Ты не в чате"
        )

        return

    partner = chat_pairs[user_id]

    del chat_pairs[user_id]

    if partner in chat_pairs:
        del chat_pairs[partner]

    try:

        bot.send_message(
            partner,
            "❌ Собеседник вышел",
            reply_markup=menu()
        )

    except:
        pass

    bot.send_message(
        user_id,
        "🔍 Ищем нового собеседника...",
        reply_markup=menu()
    )

    find_chat(message)

# =========================================
# REPORT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "🚫 Жалоба"
)
def report_user(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
        return

    partner = chat_pairs[user_id]

    try:

        bot.send_message(
            partner,
            "⚠️ На тебя отправили жалобу"
        )

    except:
        pass

    bot.send_message(
        user_id,
        "🚫 Жалоба отправлена"
    )

# =========================================
# EXIT CHAT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "❌ Выйти"
)
def exit_chat(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:

        bot.send_message(
            message.chat.id,
            "❌ Ты не в чате"
        )

        return

    partner = chat_pairs[user_id]

    del chat_pairs[user_id]

    if partner in chat_pairs:
        del chat_pairs[partner]

    try:

        bot.send_message(
            partner,
            "❌ Собеседник вышел",
            reply_markup=menu()
        )

    except:
        pass

    bot.send_message(
        user_id,
        "🏠 Ты вышел из чата",
        reply_markup=menu()
    )

# =========================================
# DELETE PROFILE
# =========================================

@bot.message_handler(
    func=lambda m:
    m.text == "🗑 Удалить профиль"
)
def delete_profile(message):

    user_id = str(message.chat.id)

    if user_id in users:
        del users[user_id]

    if user_id in user_states:
        del user_states[user_id]

    if int(user_id) in waiting_users:
        waiting_users.remove(int(user_id))

    if user_id in likes:
        del likes[user_id]

    if user_id in matches:
        del matches[user_id]

    partner_to_remove = None

    for u1, u2 in chat_pairs.items():

        if str(u1) == user_id:

            partner_to_remove = u2
            break

    if partner_to_remove:

        del chat_pairs[int(user_id)]

        if partner_to_remove in chat_pairs:
            del chat_pairs[partner_to_remove]

        try:

            bot.send_message(
                partner_to_remove,
                "❌ Собеседник удалил профиль",
                reply_markup=menu()
            )

        except:
            pass

    save_users()

    bot.send_message(
        message.chat.id,
        "🗑 Профиль удалён",
        reply_markup=menu()
    )

# =========================================
# TEXT RELAY
# =========================================

@bot.message_handler(
    content_types=["text"]
)
def relay_text(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
        return

    if message.text in [
        "❤️ Лайк",
        "⏭ Следующий",
        "🚫 Жалоба",
        "❌ Выйти"
    ]:
        return

    partner = chat_pairs[user_id]

    try:

        bot.send_message(
            partner,
            message.text
        )

    except:
        pass

# =========================================
# PHOTO RELAY
# =========================================

@bot.message_handler(
    content_types=["photo"]
)
def relay_photo(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
        return

    partner = chat_pairs[user_id]

    try:

        bot.send_photo(
            partner,
            message.photo[-1].file_id,
            caption=message.caption
        )

    except:
        pass

# =========================================
# VIDEO RELAY
# =========================================

@bot.message_handler(
    content_types=["video"]
)
def relay_video(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
        return

    partner = chat_pairs[user_id]

    try:

        bot.send_video(
            partner,
            message.video.file_id,
            caption=message.caption
        )

    except:
        pass

# =========================================
# STICKER RELAY
# =========================================

@bot.message_handler(
    content_types=["sticker"]
)
def relay_sticker(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
        return

    partner = chat_pairs[user_id]

    try:

        bot.send_sticker(
            partner,
            message.sticker.file_id
        )

    except:
        pass

# =========================================
# VOICE RELAY
# =========================================

@bot.message_handler(
    content_types=["voice"]
)
def relay_voice(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
        return

    partner = chat_pairs[user_id]

    try:

        bot.send_voice(
            partner,
            message.voice.file_id
        )

    except:
        pass

# =========================================
# RUN
# =========================================

threading.Thread(
    target=run_web
).start()

print("BOT STARTED")

bot.infinity_polling()
