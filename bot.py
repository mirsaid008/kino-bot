import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================== НАСТРОЙКИ ==================
TOKEN = "8588194727:AAEzUO6WvRiWYvOI8StQPjau5xeuWrx-Uh4"
ADMIN_ID = 8518489868  # твой Telegram ID

CHANNELS = [
    "@channel1",
    "@channel2",
    "@channel3"
]

MOVIES_FILE = "movies.json"

# ================== ФАЙЛЫ ==================
def load_movies():
    try:
        with open(MOVIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_movies(data):
    with open(MOVIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

movies = load_movies()

# ================== ПРОВЕРКИ ==================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def check_sub(user_id: int, bot) -> bool:
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ================== /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Kino olish", callback_data="get_movie")]
    ]

    if is_admin(update.effective_user.id):
        keyboard.append(
            [InlineKeyboardButton("➕ Kino qo‘shish (ADMIN)", callback_data="add_movie")]
        )

    await update.message.reply_text(
        "👋 Xush kelibsiz!\n\n"
        "🎞 Kino kodini olish uchun tugmani bosing.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== КНОПКИ ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_movie":
        await query.message.reply_text("🎟 Kino kodini yuboring:")
        context.user_data["mode"] = "get"

    elif query.data == "add_movie":
        if not is_admin(query.from_user.id):
            await query.message.reply_text("❌ Siz admin emassiz")
            return
        await query.message.reply_text("📌 Kino kodini yuboring:")
        context.user_data["mode"] = "add_code"

# ================== СООБЩЕНИЯ ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    # --- ПОЛУЧЕНИЕ КИНО ---
    if mode == "get":
        if not await check_sub(update.effective_user.id, context.bot):
            buttons = [
                [InlineKeyboardButton("📢 Kanal 1", url=f"https://t.me/{CHANNELS[0][1:]}")],
                [InlineKeyboardButton("📢 Kanal 2", url=f"https://t.me/{CHANNELS[1][1:]}")]
            ]
            await update.message.reply_text(
                "❗ Kino ko‘rish uchun kanallarga obuna bo‘ling:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        movie = movies.get(text)
        if not movie:
            await update.message.reply_text("❌ Bunday kod topilmadi")
            return

        await update.message.reply_video(
            video=movie["file_id"],
            caption=movie["caption"]
        )

    # --- ДОБАВЛЕНИЕ КИНО ---
    elif mode == "add_code":
        context.user_data["new_code"] = text
        context.user_data["mode"] = "add_video"
        await update.message.reply_text("🎥 Endi videoni yuboring")

    elif mode == "add_video":
        await update.message.reply_text("❌ Video yuboring")

# ================== ВИДЕО ОТ АДМИНА ==================
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode") != "add_video":
        return

    code = context.user_data["new_code"]
    video = update.message.video

    movies[code] = {
        "file_id": video.file_id,
        "caption": "🎬 Kino shu yerda\n👉 @your_bot"
    }

    save_movies(movies)

    context.user_data.clear()
    await update.message.reply_text("✅ Kino muvaffaqiyatli qo‘shildi!")

# ================== ЗАПУСК ==================
def main():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot ishga tushdi")
    app.run_polling()

if __name__ == "__main__":
    main()