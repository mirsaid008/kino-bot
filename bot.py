import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "8588194727:AAGbKsQ4URpJC_7v32WX6oQrg0fKNSTGwfI"
ADMIN_ID = 8518489868

MOVIES_FILE = "movies.json"
CHANNELS_FILE = "channels.json"


# ================= UTIL =================
def is_admin(user_id):
    return user_id == ADMIN_ID


def load_json(file, default):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================= CHECK SUB =================
async def check_sub(user_id, context):
    channels = load_json(CHANNELS_FILE, [])
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    channels = load_json(CHANNELS_FILE, [])

    if channels and not await check_sub(user_id, context):
        buttons = [
            [InlineKeyboardButton(f"➕ {ch}", url=f"https://t.me/{ch.replace('@','')}")]
            for ch in channels
        ]
        buttons.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")])

        await update.message.reply_text(
            "❗ Kino olish uchun kanallarga obuna bo‘ling:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    keyboard = [[InlineKeyboardButton("🎬 Kino olish", callback_data="get_movie")]]

    if is_admin(user_id):
        keyboard.append(
            [InlineKeyboardButton("⚙️ Kanallar (ADMIN)", callback_data="channels")]
        )
        keyboard.append(
            [InlineKeyboardButton("➕ Kino qo‘shish", callback_data="add_movie")]
        )

    await update.message.reply_text(
        "👋 Xush kelibsiz!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= CALLBACK =================
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "check_sub":
        if await check_sub(user_id, context):
            await query.message.edit_text("✅ Obuna tasdiqlandi! /start")
        else:
            await query.message.edit_text("❌ Hali ham obuna yo‘q")

    elif query.data == "get_movie":
        await query.message.reply_text("🎥 Kino kodini yuboring:")

    elif query.data == "channels" and is_admin(user_id):
        await query.message.reply_text(
            "⚙️ Kanallar boshqaruvi:\n"
            "/addchannel @kanal\n"
            "/delchannel @kanal\n"
            "/channelslist"
        )

    elif query.data == "add_movie" and is_admin(user_id):
        context.user_data["add_movie"] = True
        await query.message.reply_text("📥 Format:\nKOD|NOMI|HAVOLA")


# ================= ADMIN CHANNEL CMDS =================
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("❌ /addchannel @kanal")
        return

    channels = load_json(CHANNELS_FILE, [])
    ch = context.args[0]

    if ch not in channels:
        channels.append(ch)
        save_json(CHANNELS_FILE, channels)
        await update.message.reply_text(f"✅ Kanal qo‘shildi: {ch}")
    else:
        await update.message.reply_text("⚠️ Kanal allaqachon bor")


async def del_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("❌ /delchannel @kanal")
        return

    channels = load_json(CHANNELS_FILE, [])
    ch = context.args[0]

    if ch in channels:
        channels.remove(ch)
        save_json(CHANNELS_FILE, channels)
        await update.message.reply_text(f"🗑 Kanal o‘chirildi: {ch}")
    else:
        await update.message.reply_text("❌ Kanal topilmadi")


async def channels_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    channels = load_json(CHANNELS_FILE, [])
    text = "📢 Kanallar:\n" + "\n".join(channels) if channels else "❌ Kanal yo‘q"
    await update.message.reply_text(text)


# ================= MOVIES =================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    movies = load_json(MOVIES_FILE, {})

    if context.user_data.get("add_movie"):
        try:
            code, name, link = text.split("|", 2)
            movies[code] = {"name": name, "link": link}
            save_json(MOVIES_FILE, movies)
            context.user_data["add_movie"] = False
            await update.message.reply_text("✅ Kino qo‘shildi")
        except:
            await update.message.reply_text("❌ Format xato")
        return

    if not await check_sub(update.effective_user.id, context):
        await update.message.reply_text("❗ Avval obuna bo‘ling /start")
        return

    if text in movies:
        m = movies[text]
        await update.message.reply_text(f"🎬 {m['name']}\n🔗 {m['link']}")
    else:
        await update.message.reply_text("❌ Kino topilmadi")


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(CommandHandler("addchannel", add_channel))
    app.add_handler(CommandHandler("delchannel", del_channel))
    app.add_handler(CommandHandler("channelslist", channels_list))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    app.run_polling()


if __name__ == "__main__":
    main()
