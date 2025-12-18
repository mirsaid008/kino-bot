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
        await query.message.reply_text("📥 Kino qo‘shish boshlandi.\nKino kodini kiriting:")

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
    user_id = update.effective_user.id
    text = update.message.text.strip()
    movies = load_json(MOVIES_FILE, {})

    # ===== ADD MOVIE (ADMIN STEP BY STEP) =====
    if context.user_data.get("add_movie") and is_admin(user_id):
        step = context.user_data.get("step", "code")

        if step == "code":
            context.user_data["code"] = text
            context.user_data["step"] = "name"
            await update.message.reply_text("🎬 Kino nomini kiriting:")
            return

        if step == "name":
            context.user_data["name"] = text
            context.user_data["step"] = "rating"
            await update.message.reply_text("⭐ Reyting kiriting (masalan 8.5):")
            return
        if step == "rating":
    context.user_data["rating"] = text
    context.user_data["step"] = "trailer"
    await update.message.reply_text("▶️ Treyler videosini yuboring (2–3 daqiqa):")
    return

if step == "trailer":
    if not update.message.video:
        await update.message.reply_text(
            "❌ Iltimos, 2–3 daqiqalik video yuboring"
        )
        return

    context.user_data["trailer"] = update.message.video.file_id
    context.user_data["step"] = "link"
    await update.message.reply_text("🔗 To‘liq film linkini yuboring:")
    return
            save_json(MOVIES_FILE, movies)
            context.user_data.clear()
            await update.message.reply_text("✅ Kino qo‘shildi")
            return

    # ===== CHECK SUB =====
    if not await check_sub(user_id, context):
        await update.message.reply_text("❗ Avval obuna bo‘ling /start")
        return

    # ===== GET MOVIE =====
    if text in movies:
    m = movies[text]

    await update.message.reply_video(
        video=m["trailer"],
        caption=(
            f"🎬 <b>{m['name']}</b>\n"
            f"⭐ Reyting: {m['rating']}"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 To‘liq ko‘rish", url=m["link"])]
        ]),
        parse_mode="HTML"
    )
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




