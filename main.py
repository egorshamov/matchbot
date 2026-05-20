# FULL STABLE ANON BOT
# MATCH + PROFILE + RENDER READY

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
# FLASK + RENDER
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

def load_data():

    try:

        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return {}

def save_data():

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

data = load_data()

users = data.get("users", {})
likes = data.get("likes", {})
matches = data.get("matches", {})

# =========================================
# MEMORY
# =========================================

user_states = {}

waiting_users = []

chat_pairs = {}

# =========================================
# MENUS
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

def profile_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add("✏️ Изменить описание")

    markup.add("📸 Изменить фото")

    markup.add("↩️ Назад")

    return markup

def skip_markup():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add("⏭ Пропустить")

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

        save_data()

        user_states[user_id] = "gender"

        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать\n\nНапиши М или Ж",
            reply_markup=types.ReplyKeyboardRemove()
        )

    else:

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
    str(m.chat.id) in user_states,
    content_types=["text", "photo"]
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

        save_data()

        user_states[user_id] = "search"

        bot.send_message(
            message.chat.id,
            "🔎 Кого ищешь?\n\nМ / Ж / Л",
            reply_markup=types.ReplyKeyboardRemove()
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

        save_data()

        user_states[user_id] = "age"

        bot.send_message(
            message.chat.id,
            "🎂 Напиши возраст",
            reply_markup=types.ReplyKeyboardRemove()
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

        save_data()

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

            save_data()

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

            save_data()

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

            save_data()

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "✅ Профиль создан",
                reply_markup=menu()
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
        return

    user = users[user_id]

    username = message.from_user.username

    if username:
        tg = f"@{username}"
    else:
        tg = f"tg://user?id={user_id}"

    text = (
        f"{tg}\n\n"
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
# EDIT BIO
# =========================================

@bot.message_handler(
    func=lambda m:
    m.text == "✏️ Изменить описание"
)
def edit_bio(message):

    user_states[str(message.chat.id)] = "bio"

    bot.send_message(
        message.chat.id,
        "📝 Новое описание",
        reply_markup=skip_markup()
    )

# =========================================
# EDIT PHOTO
# =========================================

@bot.message_handler(
    func=lambda m:
    m.text == "📸 Изменить фото"
)
def edit_photo(message):

    user_states[str(message.chat.id)] = "photo"

    bot.send_message(
        message.chat.id,
        "📸 Отправь фото",
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

        save_data()

        p_user = users.get(partner)

        if p_user:

            try:

                username = bot.get_chat(int(partner)).username

                if username:
                    tg = f"@{username}"
                else:
                    tg = f"tg://user?id={partner}"

            except:

                tg = f"tg://user?id={partner}"

            text = (
                f"🔥 MATCH!\n\n"
                f"👤 Пол: {p_user['gender']}\n"
                f"🎂 Возраст: {p_user['age']}\n\n"
                f"📝 {p_user['bio']}\n\n"
                f"📩 {tg}"
            )

            if p_user["photo"]:

                bot.send_photo(
                    int(user_id),
                    p_user["photo"],
                    caption=text
                )

            else:

                bot.send_message(
                    int(user_id),
                    text
                )

        my_user = users.get(user_id)

        if my_user:

            try:

                username = bot.get_chat(int(user_id)).username

                if username:
                    tg = f"@{username}"
                else:
                    tg = f"tg://user?id={user_id}"

            except:

                tg = f"tg://user?id={user_id}"

            text = (
                f"🔥 MATCH!\n\n"
                f"👤 Пол: {my_user['gender']}\n"
                f"🎂 Возраст: {my_user['age']}\n\n"
                f"📝 {my_user['bio']}\n\n"
                f"📩 {tg}"
            )

            if my_user["photo"]:

                bot.send_photo(
                    int(partner),
                    my_user["photo"],
                    caption=text
                )

            else:

                bot.send_message(
                    int(partner),
                    text
                )

    save_data()

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

    if user_id not in matches or not matches[user_id]:

        bot.send_message(
            message.chat.id,
            "❌ MATCH пока нет"
        )

        return

    for partner_id in matches[user_id]:

        if partner_id not in users:
            continue

        user = users[partner_id]

        try:

            username = bot.get_chat(int(partner_id)).username

            if username:
                tg = f"@{username}"
            else:
                tg = f"tg://user?id={partner_id}"

        except:

            tg = f"tg://user?id={partner_id}"

        text = (
            f"🔥 MATCH\n\n"
            f"👤 Пол: {user['gender']}\n"
            f"🎂 Возраст: {user['age']}\n\n"
            f"📝 {user['bio']}\n\n"
            f"📩 {tg}"
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

# =========================================
# NEXT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "⏭ Следующий"
)
def next_chat(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
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
# EXIT CHAT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "❌ Выйти"
)
def exit_chat(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:
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
# REPORT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "🚫 Жалоба"
)
def report_user(message):

    bot.send_message(
        message.chat.id,
        "🚫 Жалоба отправлена"
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

    # CHAT CLEANUP

    if int(user_id) in chat_pairs:

        partner = chat_pairs[int(user_id)]

        del chat_pairs[int(user_id)]

        if partner in chat_pairs:
            del chat_pairs[partner]

        try:

            bot.send_message(
                partner,
                "❌ Собеседник удалил профиль",
                reply_markup=menu()
            )

        except:
            pass

    # WAITING CLEANUP

    if int(user_id) in waiting_users:
        waiting_users.remove(int(user_id))

    # STATE CLEANUP

    if user_id in user_states:
        del user_states[user_id]

    # USER CLEANUP

    if user_id in users:
        del users[user_id]

    # LIKES CLEANUP

    if user_id in likes:
        del likes[user_id]

    # MATCH CLEANUP

    for uid in matches:

        if user_id in matches[uid]:

            try:
                matches[uid].remove(user_id)
            except:
                pass

    if user_id in matches:
        del matches[user_id]

    save_data()

    bot.send_message(
        message.chat.id,
        "🗑 Профиль удалён",
        reply_markup=types.ReplyKeyboardRemove()
    )

# =========================================
# TEXT RELAY
# =========================================

@bot.message_handler(content_types=["text"])
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

@bot.message_handler(content_types=["photo"])
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

@bot.message_handler(content_types=["video"])
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

@bot.message_handler(content_types=["sticker"])
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

@bot.message_handler(content_types=["voice"])
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
