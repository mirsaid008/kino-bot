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

# ================= НАСТРОЙКИ =================
TOKEN = "8588194727:AAGbKsQ4URpJC_7v32WX6oQrg0fKNSTGwfI"
ADMIN_ID = 8518489868   # твой Telegram ID

CHANNELS = [
    "@channel1",
    "@channel2",
    "@channel3"
]

MOVIES_FILE = "movies.json"

# ================= ВСПОМОГАТЕЛЬНЫЕ =================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def load_movies():
    try:
        with open(MOVIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_movies(data):
    with open(MOVIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def check_sub(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_sub(user_id, context):
        buttons = [
            [InlineKeyboardButton(f"➕ {ch}", url=f"https://t.me/{ch.replace('@','')}")]
            for ch in CHANNELS
        ]
        buttons.append(
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
        )

        await update.message.reply_text(
            "❗ Kino ko‘rish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    keyboard = [
        [InlineKeyboardButton("🎬 Kino olish", callback_data="get_movie")]
    ]

    if is_admin(user_id):
        keyboard.append(
            [InlineKeyboardButton("➕ Kino qo‘shish (ADMIN)", callback_data="add_movie")]
        )

    await update.message.reply_text(
        "👋 Xush kelibsiz!\n\n🎬 Kino olish uchun tugmani bosing.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= CALLBACK =================
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "check_sub":
        if await check_sub(user_id, context):
            await query.message.edit_text("✅ Obuna tasdiqlandi! /start bosing")
        else:
            await query.message.edit_text("❌ Hali ham obuna yo‘q")

    elif query.data == "get_movie":
        await query.message.reply_text("🎥 Kino kodini yuboring:")

    elif query.data == "add_movie" and is_admin(user_id):
        context.user_data["add_movie"] = True
        await query.message.reply_text(
            "📥 Kino qo‘shish formati:\n\n"
            "KOD|NOMI|REYTING|TAVSIF|VIDEO_FILE_ID|URL\n\n"
            "📌 Misol:\n"
            "123|Avatar|8.5|Fantastik kino|BAACAgIA...|https://site.com"
        )

# ================= MESSAGE =================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    movies = load_movies()

    # ===== ADMIN ADD MOVIE =====
    if context.user_data.get("add_movie") and is_admin(user_id):
        try:
            code, name, rating, desc, video_id, url = text.split("|", 5)

            movies[code] = {
                "name": name,
                "rating": rating,
                "desc": desc,
                "video": video_id,
                "url": url
            }

            save_movies(movies)
            context.user_data["add_movie"] = False

            await update.message.reply_text("✅ Kino muvaffaqiyatli qo‘shildi!")
        except:
            await update.message.reply_text("❌ Format xato. Qayta urinib ko‘ring.")
        return

    # ===== SUB CHECK =====
    if not await check_sub(user_id, context):
        await update.message.reply_text("❗ Avval obuna bo‘ling. /start")
        return

    # ===== GET MOVIE =====
    if text in movies:
        movie = movies[text]

        buttons = [
            [InlineKeyboardButton("▶️ To‘liq ko‘rish", url=movie["url"])]
        ]

        await update.message.reply_video(
            video=movie["video"],
            caption=(
                f"🎬 {movie['name']}\n"
                f"⭐ Reyting: {movie['rating']}\n\n"
                f"{movie['desc']}"
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.message.reply_text("❌ Bunday kino topilmadi")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    app.run_polling()

if __name__ == "__main__":
    main()
