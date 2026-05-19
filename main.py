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
# FILES
# =========================================

DATA_FILE = "users.json"
MATCH_FILE = "matches.json"
LIKES_FILE = "likes.json"

# =========================================
# MEMORY
# =========================================

waiting_users = []
chat_pairs = {}

user_states = {}
spam_control = {}

# =========================================
# LOAD / SAVE
# =========================================

def load_json(file_name):

    try:

        with open(file_name, "r") as f:
            return json.load(f)

    except:

        return {}

def save_json(file_name, data):

    with open(file_name, "w") as f:
        json.dump(data, f)

users = load_json(DATA_FILE)
likes = load_json(LIKES_FILE)
matches = load_json(MATCH_FILE)

def save_users():
    save_json(DATA_FILE, users)

def save_likes():
    save_json(LIKES_FILE, likes)

def save_matches():
    save_json(MATCH_FILE, matches)
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
        "🚫 Жалоба"
    )

    markup.add(
        "🗑 Удалить профиль",
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

    markup.add(
        "📸 Изменить фото",
        "🎂 Изменить возраст"
    )

    markup.add(
        "🔎 Изменить поиск",
        "⚧ Изменить пол"
    )

    markup.add("↩️ Назад")

    return markup

# =========================================
# SKIP MENU
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

    if user_id in users:

        if users[user_id]["banned"]:

            bot.send_message(
                message.chat.id,
                "🚫 Твой профиль заблокирован"
            )

            return

        bot.send_message(
            message.chat.id,
            "🔥 С возвращением в Match",
            reply_markup=menu()
        )

        return

    users[user_id] = {

        "gender": "",
        "search": "",
        "age": "",
        "bio": "Нет описания",
        "photo": "",
        "likes": 0,
        "reports": 0,
        "banned": False,
        "created": int(time.time())

    }

    save_users()

    user_states[user_id] = "gender"

    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать в Match\n\n"
        "Выбери свой пол:\n"
        "М или Ж",
        reply_markup=skip_markup()
    )
    ￼# =========================================
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
                "↩️ Вернулись назад\n\n"
                "Напиши М или Ж"
            )

            return

        elif state == "age":

            user_states[user_id] = "search"

            bot.send_message(
                message.chat.id,
                "↩️ Вернулись назад\n\n"
                "М / Ж / Л"
            )

            return

        elif state == "bio":

            user_states[user_id] = "age"

            bot.send_message(
                message.chat.id,
                "↩️ Вернулись назад\n\n"
                "Напиши возраст"
            )

            return

        elif state == "photo":

            user_states[user_id] = "bio"

            bot.send_message(
                message.chat.id,
                "↩️ Вернулись назад\n\n"
                "Напиши описание",
                reply_markup=skip_markup()
            )

            return

        else:

            del user_states[user_id]

    bot.send_message(
        message.chat.id,
        "↩️ Возврат в меню",
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
            "🔎 Кого ищешь?\n\n"
            "М / Ж / Л"
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
            "📝 Напиши описание\n\n"
            "Или ⏭ Пропустить",
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
            "📸 Отправь фото"
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

    # EDIT AGE

    elif state == "edit_age":

        if not message.text.isdigit():

            bot.send_message(
                message.chat.id,
                "❌ Возраст цифрами"
            )

            return

        users[user_id]["age"] = int(message.text)

        save_users()

        del user_states[user_id]

        bot.send_message(
            message.chat.id,
            "✅ Возраст изменён",
            reply_markup=profile_menu()
        )

    # EDIT SEARCH

    elif state == "edit_search":

        text = message.text.lower()

        if text not in ["м", "ж", "л"]:

            bot.send_message(
                message.chat.id,
                "❌ М / Ж / Л"
            )

            return

        users[user_id]["search"] = text.upper()

        save_users()

        del user_states[user_id]

        bot.send_message(
            message.chat.id,
            "✅ Поиск изменён",
            reply_markup=profile_menu()
        )

    # EDIT GENDER

    elif state == "edit_gender":

        text = message.text.lower()

        if text not in ["м", "ж"]:

            bot.send_message(
                message.chat.id,
                "❌ М или Ж"
            )

            return

        users[user_id]["gender"] = text.upper()

        save_users()

        del user_states[user_id]

        bot.send_message(
            message.chat.id,
            "✅ Пол изменён",
            reply_markup=profile_menu()
        )
        # =========================================
# PHOTO
# =========================================

@bot.message_handler(content_types=["photo"])
def photo_handler(message):

    user_id = str(message.chat.id)

    # REGISTER PHOTO

    if user_id in user_states:

        state = user_states[user_id]

        if state == "photo":

            users[user_id]["photo"] = message.photo[-1].file_id

            save_users()

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "✅ Профиль создан",
                reply_markup=menu()
            )

            return

        elif state == "edit_photo":

            users[user_id]["photo"] = message.photo[-1].file_id

            save_users()

            del user_states[user_id]

            bot.send_message(
                message.chat.id,
                "✅ Фото изменено",
                reply_markup=profile_menu()
            )

            return

    # CHAT PHOTO

    if message.chat.id in chat_pairs:

        partner = chat_pairs[message.chat.id]

        try:

            bot.send_photo(
                partner,
                message.photo[-1].file_id,
                caption=message.caption
            )

        except:
            pass

# =========================================
# VIDEO
# =========================================

@bot.message_handler(content_types=["video"])
def video_handler(message):

    if message.chat.id not in chat_pairs:
        return

    partner = chat_pairs[message.chat.id]

    try:

        bot.send_video(
            partner,
            message.video.file_id,
            caption=message.caption
        )

    except:
        pass

# =========================================
# VIDEO NOTE
# =========================================

@bot.message_handler(content_types=["video_note"])
def video_note_handler(message):

    if message.chat.id not in chat_pairs:
        return

    partner = chat_pairs[message.chat.id]

    try:

        bot.send_video_note(
            partner,
            message.video_note.file_id
        )

    except:
        pass
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
# PROFILE BUTTONS
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "✏️ Изменить описание"
)
def edit_bio(message):

    user_states[str(message.chat.id)] = "edit_bio"

    bot.send_message(
        message.chat.id,
        "📝 Напиши новое описание",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m: m.text == "📸 Изменить фото"
)
def edit_photo(message):

    user_states[str(message.chat.id)] = "edit_photo"

    bot.send_message(
        message.chat.id,
        "📸 Отправь новое фото",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m: m.text == "🎂 Изменить возраст"
)
def edit_age(message):

    user_states[str(message.chat.id)] = "edit_age"

    bot.send_message(
        message.chat.id,
        "🎂 Напиши новый возраст",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m: m.text == "🔎 Изменить поиск"
)
def edit_search(message):

    user_states[str(message.chat.id)] = "edit_search"

    bot.send_message(
        message.chat.id,
        "🔎 М / Ж / Л",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m: m.text == "⚧ Изменить пол"
)
def edit_gender(message):

    user_states[str(message.chat.id)] = "edit_gender"

    bot.send_message(
        message.chat.id,
        "⚧ М или Ж",
        reply_markup=skip_markup()
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
# PROFILE BUTTONS
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "✏️ Изменить описание"
)
def edit_bio(message):

    user_states[str(message.chat.id)] = "edit_bio"

    bot.send_message(
        message.chat.id,
        "📝 Напиши новое описание",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m: m.text == "📸 Изменить фото"
)
def edit_photo(message):

    user_states[str(message.chat.id)] = "edit_photo"

    bot.send_message(
        message.chat.id,
        "📸 Отправь новое фото",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m: m.text == "🎂 Изменить возраст"
)
def edit_age(message):

    user_states[str(message.chat.id)] = "edit_age"

    bot.send_message(
        message.chat.id,
        "🎂 Напиши новый возраст",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m: m.text == "🔎 Изменить поиск"
)
def edit_search(message):

    user_states[str(message.chat.id)] = "edit_search"

    bot.send_message(
        message.chat.id,
        "🔎 М / Ж / Л",
        reply_markup=skip_markup()
    )

@bot.message_handler(
    func=lambda m: m.text == "⚧ Изменить пол"
)
def edit_gender(message):

    user_states[str(message.chat.id)] = "edit_gender"

    bot.send_message(
        message.chat.id,
        "⚧ М или Ж",
        reply_markup=skip_markup()
    )
    # =========================================
# LIKE / MATCH
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "❤️ Лайк"
)
def like_user(message):

    user_id = str(message.chat.id)

    if message.chat.id not in chat_pairs:
        return

    partner = str(chat_pairs[message.chat.id])

    if user_id not in likes:
        likes[user_id] = []

    if partner not in likes[user_id]:

        likes[user_id].append(partner)

        save_likes()

    users[partner]["likes"] += 1

    save_users()

    # MATCH

    if partner in likes and user_id in likes[partner]:

        if user_id not in matches:
            matches[user_id] = []

        if partner not in matches:
            matches[partner] = []

        if partner not in matches[user_id]:

            matches[user_id].append(partner)
            matches[partner].append(user_id)

            save_matches()

        user1 = users[user_id]
        user2 = users[partner]

        username1 = bot.get_chat(message.chat.id).username
        username2 = bot.get_chat(int(partner)).username

        text1 = (
            f"💘 У вас MATCH!\n\n"
            f"Возраст: {user2['age']}\n"
            f"Описание: {user2['bio']}\n\n"
        )

        if username2:

            text1 += f"📩 @{username2}"

        else:

            text1 += f"🆔 ID: {partner}\nУ пользователя нет username"

        text2 = (
            f"💘 У вас MATCH!\n\n"
            f"Возраст: {user1['age']}\n"
            f"Описание: {user1['bio']}\n\n"
        )

        if username1:

            text2 += f"📩 @{username1}"

        else:

            text2 += f"🆔 ID: {user_id}\nУ пользователя нет username"

        try:

            if user2["photo"]:

                bot.send_photo(
                    user_id,
                    user2["photo"],
                    caption=text1
                )

            else:

                bot.send_message(
                    user_id,
                    text1
                )

        except:
            pass

        try:

            if user1["photo"]:

                bot.send_photo(
                    partner,
                    user1["photo"],
                    caption=text2
                )

            else:

                bot.send_message(
                    partner,
                    text2
                )

        except:
            pass

    else:

        bot.send_message(
            message.chat.id,
            "❤️ Лайк отправлен"
        )
        # =========================================
# TEXT RELAY
# =========================================

@bot.message_handler(content_types=["text"])
def relay(message):

    if str(message.chat.id) in user_states:
        return

    if message.chat.id not in chat_pairs:
        return

    partner = chat_pairs[message.chat.id]

    try:

        bot.send_message(
            partner,
            message.text
        )

    except:
        pass

# =========================================
# VOICE
# =========================================

@bot.message_handler(content_types=["voice"])
def voice_handler(message):

    if message.chat.id not in chat_pairs:
        return

    partner = chat_pairs[message.chat.id]

    try:

        bot.send_voice(
            partner,
            message.voice.file_id
        )

    except:
        pass

# =========================================
# STICKERS
# =========================================

@bot.message_handler(content_types=["sticker"])
def sticker_handler(message):

    if message.chat.id not in chat_pairs:
        return

    partner = chat_pairs[message.chat.id]

    try:

        bot.send_sticker(
            partner,
            message.sticker.file_id
        )

    except:
        pass
        # =========================================
# ONLINE
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "📊 Онлайн"
)
def online(message):

    total = len(users)
    online_count = len(chat_pairs) // 2

    month = 0

    now = int(time.time())

    for uid in users:

        created = users[uid].get("created", now)

        if now - created <= 2592000:
            month += 1

    text = (
        f"👥 Пользователей: {total}\n"
        f"💬 Активных чатов: {online_count}\n"
        f"🔥 За месяц: {month}"
    )

    bot.send_message(
        message.chat.id,
        text
    )

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

    partner = str(chat_pairs[user_id])

    users[partner]["reports"] += 1

    if users[partner]["reports"] >= 5:

        users[partner]["banned"] = True

    save_users()

    bot.send_message(
        user_id,
        "🚫 Жалоба отправлена"
    )

# =========================================
# DELETE PROFILE
# =========================================

@bot.message_handler(
    func=lambda m: m.text == "🗑 Удалить профиль"
)
@bot.message_handler(
    func=lambda m: m.text == "🗑 Удалить профиль"
)
def delete_profile(message):

    user_id = str(message.chat.id)

    # USERS

    if user_id in users:
        del users[user_id]

    # LIKES

    if user_id in likes:
        del likes[user_id]

    for uid in likes:

        if user_id in likes[uid]:

            likes[uid].remove(user_id)

    # MATCHES

    if user_id in matches:
        del matches[user_id]

    for uid in matches:

        if user_id in matches[uid]:

            matches[uid].remove(user_id)

    # WAITING

    if int(user_id) in waiting_users:

        waiting_users.remove(int(user_id))

    # CHAT

    if int(user_id) in chat_pairs:

        partner = chat_pairs[int(user_id)]

        del chat_pairs[int(user_id)]

        if partner in chat_pairs:

            del chat_pairs[partner]

            try:

                bot.send_message(
                    partner,
                    "❌ Собеседник удалил профиль"
                )

            except:
                pass

    # STATES

    if user_id in user_states:
        del user_states[user_id]

    save_users()
    save_likes()
    save_matches()

    bot.send_message(
        message.chat.id,
        "🗑 Профиль полностью удалён",
        reply_markup=types.ReplyKeyboardRemove()
    )    # =========================================
# RUN
# =========================================

def run_flask():

    app.run(
        host="0.0.0.0",
        port=10000
    )

threading.Thread(
    target=run_flask
).start()

while True:

    try:

        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=10
        )

    except Exception as e:

        print(e)

        time.sleep(5)
        