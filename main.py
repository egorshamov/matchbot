# =========================================
# MATCH TELEGRAM BOT
# FULL STABLE VERSION
# =========================================

import telebot
from telebot import types
from flask import Flask
import threading
import os
import json
import time
import random

TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

# =========================================
# FLASK
# =========================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Match is running"

# =========================================
# DATA
# =========================================

DATA_FILE = "users.json"

waiting_users = []
chat_pairs = {}

user_states = {}
spam_control = {}

likes = {}
matches = {}

# =========================================
# LOAD USERS
# =========================================

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

# =========================================
# SAVE MATCH
# =========================================

def save_match(user1, user2):

    user1 = str(user1)
    user2 = str(user2)

    if user1 not in matches:
        matches[user1] = []

    if user2 not in matches[user1]:
        matches[user1].append(user2)

# =========================================
# MENU
# =========================================

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
        "🔥 Мои MATCH",
        "✏️ Изменить"
    )

    markup.add(
        "🚫 Жалоба",
        "🗑 Удалить профиль"
    )

    markup.add("❌ Выйти")

    return markup

# =========================================
# SKIP MARKUP
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
            "reports": 0,
            "banned": False,
            "created": int(time.time())

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

        if users[user_id]["banned"]:

            bot.send_message(
                message.chat.id,
                "🚫 Твой аккаунт заблокирован"
            )

            return

        bot.send_message(
            message.chat.id,
            "🔥 С возвращением в Match",
            reply_markup=menu()
        )

# =========================================
# REGISTER
# =========================================

@bot.message_handler(
    func=lambda m:
    str(m.chat.id) in user_states
    and (
        m.content_type != "text"
        or m.text not in [
            "🔍 Найти",
            "❤️ Лайк",
            "⏭ Следующий",
            "👤 Профиль",
            "📊 Онлайн",
            "🔥 Мои MATCH",
            "✏️ Изменить",
            "🚫 Жалоба",
            "🗑 Удалить профиль",
            "❌ Выйти",
            "↩️ Назад"
        ]
    )
)
def register(message):

    user_id = str(message.chat.id)

    state = user_states[user_id]

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
            "📝 Напиши описание\n\n"
            "Или нажми ⏭ Пропустить",
            reply_markup=skip_markup()
        )

    elif state == "bio":

        if message.text == "↩️ Назад":

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "↩️ Возврат в меню",
                reply_markup=menu()
            )

            return

        if message.text == "⏭ Пропустить":

            users[user_id]["bio"] = "Нет описания"

        else:

            users[user_id]["bio"] = message.text[:300]

        save_users(users)

        user_states[user_id] = "photo"

        bot.send_message(
            message.chat.id,
            "📸 Отправь фото профиля"
        )

    elif state == "edit_bio":

        if message.text == "↩️ Назад":

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "↩️ Возврат в меню",
                reply_markup=menu()
            )

            return

        if message.text == "⏭ Пропустить":

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "❌ Изменение отменено",
                reply_markup=menu()
            )

            return

        users[user_id]["bio"] = message.text[:300]

        save_users(users)

        del user_states[user_id]

        bot.send_message(
            message.chat.id,
            "✅ Описание обновлено",
            reply_markup=menu()
        )

# =========================================
# BACK BUTTON
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "↩️ Назад"
)
def back_button(message):

    user_id = str(message.chat.id)

    if user_id in user_states:

        del user_states[user_id]

    bot.send_message(
        message.chat.id,
        "↩️ Возврат в меню",
        reply_markup=menu()
    )

# =========================================
# PHOTO
# =========================================

@bot.message_handler(content_types=["photo"])
def photo_handler(message):

    user_id = str(message.chat.id)

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

    if message.chat.id in chat_pairs:

        partner = chat_pairs[message.chat.id]

        bot.send_photo(
            partner,
            message.photo[-1].file_id,
            caption=message.caption
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

    text = (
        f"👤 Твой профиль\n\n"
        f"Пол: {user['gender']}\n"
        f"Возраст: {user['age']}\n"
        f"Описание: {user['bio']}\n\n"
        f"❤️ Лайки: {user['likes']}\n"
        f"💘 MATCH: {len(matches.get(user_id, []))}\n"
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

# =========================================
# EDIT PROFILE
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "✏️ Изменить"
)
def edit_profile(message):

    user_id = str(message.chat.id)

    user_states[user_id] = "edit_bio"

    bot.send_message(
        message.chat.id,
        "📝 Напиши новое описание\n\n"
        "Или нажми ⏭ Пропустить",
        reply_markup=skip_markup()
    )

# =========================================
# DELETE PROFILE
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "🗑 Удалить профиль"
)
def delete_profile(message):

    user_id = str(message.chat.id)

    if user_id in users:

        del users[user_id]

        save_users(users)

    bot.send_message(
        message.chat.id,
        "🗑 Профиль удалён"
    )

# =========================================
# MATCHES
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

    for partner in matches[user_id]:

        if partner not in users:
            continue

        p = users[partner]

        text = (
            f"💘 MATCH\n\n"
            f"Возраст: {p['age']}\n"
            f"{p['bio']}"
        )

        markup = types.InlineKeyboardMarkup()

        try:

            info = bot.get_chat(int(partner))

            if info.username:

                btn = types.InlineKeyboardButton(
                    "💬 Открыть Telegram",
                    url=f"https://t.me/{info.username}"
                )

                markup.add(btn)

            else:

                btn = types.InlineKeyboardButton(
                    "❌ Нет username",
                    callback_data="none"
                )

                btn2 = types.InlineKeyboardButton(
                    f"🆔 ID: {partner}",
                    callback_data="none"
                )

                markup.add(btn)
                markup.add(btn2)

        except:
            pass

        if p["photo"]:

            bot.send_photo(
                message.chat.id,
                p["photo"],
                caption=text,
                reply_markup=markup
            )

        else:

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup
            )

# =========================================
# ONLINE
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "📊 Онлайн"
)
def online(message):

    online_count = len(waiting_users)

    now = int(time.time())

    month_users = 0

    for uid in users:

        created = users[uid].get("created", now)

        if now - created <= 30 * 24 * 60 * 60:

            month_users += 1

    bot.send_message(
        message.chat.id,
        f"🔥 Статистика Match\n\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"📅 За месяц: {month_users}\n"
        f"🟢 Онлайн: {online_count}\n"
        f"💬 Активных чатов: {len(chat_pairs)//2}"
    )

# =========================================
# COMPATIBLE
# =========================================

def compatible(user1, user2):

    u1 = users[str(user1)]
    u2 = users[str(user2)]

    if u1["search"] == "Л":
        return True

    return u1["search"] == u2["gender"]

# =========================================
# SEARCH
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "🔍 Найти"
)
def search(message):

    user_id = message.chat.id

    if str(user_id) in user_states:
        del user_states[str(user_id)]

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

    random.shuffle(waiting_users)

    while waiting_users:

        partner = waiting_users.pop(0)

        if partner == user_id:
            continue

        if not compatible(user_id, partner):
            continue

        chat_pairs[user_id] = partner
        chat_pairs[partner] = user_id

        user_data = users[str(user_id)]
        partner_data = users[str(partner)]

        text_for_user = (
            f"💬 Собеседник найден\n\n"
            f"Возраст: {partner_data['age']}\n"
            f"{partner_data['bio']}"
        )

        text_for_partner = (
            f"💬 Собеседник найден\n\n"
            f"Возраст: {user_data['age']}\n"
            f"{user_data['bio']}"
        )

        if partner_data["photo"]:

            bot.send_photo(
                user_id,
                partner_data["photo"],
                caption=text_for_user
            )

        else:

            bot.send_message(
                user_id,
                text_for_user
            )

        if user_data["photo"]:

            bot.send_photo(
                partner,
                user_data["photo"],
                caption=text_for_partner
            )

        else:

            bot.send_message(
                partner,
                text_for_partner
            )

        return

    waiting_users.append(user_id)

    bot.send_message(
        user_id,
        "🔎 Ищем собеседника..."
    )

# =========================================
# LIKE
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "❤️ Лайк"
)
def like(message):

    user_id = str(message.chat.id)

    if message.chat.id not in chat_pairs:

        bot.send_message(
            message.chat.id,
            "❌ Лайк только в чате"
        )

        return

    partner = str(chat_pairs[message.chat.id])

    if partner not in likes:
        likes[partner] = []

    if user_id in likes[partner]:

        bot.send_message(
            message.chat.id,
            "⚠️ Уже лайкал"
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

# =========================================
# REPORT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "🚫 Жалоба"
)
def report(message):

    user_id = message.chat.id

    if user_id not in chat_pairs:

        bot.send_message(
            user_id,
            "❌ Жалоба только в чате"
        )

        return

    partner = str(chat_pairs[user_id])

    users[partner]["reports"] += 1

    if users[partner]["reports"] >= 5:

        users[partner]["banned"] = True

    save_users(users)

    bot.send_message(
        user_id,
        "🚫 Жалоба отправлена"
    )

# =========================================
# NEXT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "⏭ Следующий"
)
def next_chat(message):

    user_id = message.chat.id

    if str(user_id) in user_states:
        del user_states[str(user_id)]

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

# =========================================
# EXIT
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "❌ Выйти"
)
def stop_chat(message):

    user_id = message.chat.id

    if str(user_id) in user_states:
        del user_states[str(user_id)]

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

# =========================================
# ANTISPAM
# =========================================

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

# =========================================
# RELAY
# =========================================

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

    if message.content_type == "text":

        commands = [
            "🔍 Найти",
            "❤️ Лайк",
            "⏭ Следующий",
            "👤 Профиль",
            "📊 Онлайн",
            "🔥 Мои MATCH",
            "✏️ Изменить",
            "🚫 Жалоба",
            "🗑 Удалить профиль",
            "❌ Выйти",
            "⏭ Пропустить",
            "↩️ Назад"
        ]

        if message.text not in commands:

            bot.send_message(
                partner,
                message.text[:1000]
            )

    elif message.content_type == "voice":

        bot.send_voice(
            partner,
            message.voice.file_id
        )

    elif message.content_type == "sticker":

        bot.send_sticker(
            partner,
            message.sticker.file_id
        )

# =========================================
# RUN BOT
# =========================================

def run_bot():

    print("MATCH STARTED")

    while True:

        try:

            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30
            )

        except Exception as e:

            print("ERROR:", e)

            time.sleep(5)

# =========================================
# START
# =========================================

if __name__ == "__main__":

    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )