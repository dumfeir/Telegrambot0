import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from PIL import Image
import nest_asyncio

user_photos = {}

# ✅ لوحة الأزرار
reply_keyboard = ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)

# ✅ بدء المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أرسل صورًا واحدة تلو الأخرى، ثم اكتب 'تم' عند الانتهاء لتحويلها إلى PDF.",
        reply_markup=reply_keyboard
    )

# ✅ استقبال الصور
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    file = await update.message.photo[-1].get_file()
    os.makedirs("images", exist_ok=True)
    path = f"images/{user_id}_{len(user_photos.get(user_id, []))}.jpg"
    await file.download_to_drive(path)
    user_photos.setdefault(user_id, []).append(path)
    await update.message.reply_text("✅ تم حفظ الصورة!", reply_markup=reply_keyboard)

# ✅ عند كتابة "تم" — تحويل الصور إلى PDF
async def handle_done_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().lower() != "تم":
        return  # تجاهل أي رسالة غير "تم"

    user_id = update.message.from_user.id
    photos = user_photos.get(user_id, [])

    if not photos:
        await update.message.reply_text("❌ لم ترسل أي صور.", reply_markup=reply_keyboard)
        return

    try:
        images = [Image.open(p).convert("RGB") for p in photos]
        pdf_path = f"{user_id}.pdf"
        images[0].save(pdf_path, save_all=True, append_images=images[1:])
        await update.message.reply_document(open(pdf_path, "rb"))
        await update.message.reply_text("📄 تم إنشاء ملف PDF بنجاح!", reply_markup=reply_keyboard)

        for p in photos:
            os.remove(p)
        os.remove(pdf_path)
        user_photos[user_id] = []

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ: {e}", reply_markup=reply_keyboard)

# ✅ تشغيل البوت
async def run_bot():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("❌ لم يتم العثور على توكن البوت")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_done_text))
    print("✅ البوت يعمل الآن...")
    await app.run_polling()

# ✅ نقطة التشغيل
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(run_bot())
