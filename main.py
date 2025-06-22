import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from PIL import Image
from flask import Flask
from threading import Thread
import nest_asyncio

user_photos = {}

# ✅ إبقاء البوت شغال على Render
def keep_alive():
    app = Flask("")

    @app.route("/")
    def home():
        return "✅ Bot is alive!", 200

    def run():
        app.run(host="0.0.0.0", port=8080)

    Thread(target=run).start()

# ✅ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل صوراً ثم أرسل /done لتحويلها إلى PDF.")

# ✅ استقبال الصور
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    file = await update.message.photo[-1].get_file()
    os.makedirs("images", exist_ok=True)
    path = f"images/{user_id}_{len(user_photos.get(user_id, []))}.jpg"
    await file.download_to_drive(path)
    user_photos.setdefault(user_id, []).append(path)
    await update.message.reply_text("✅ تم حفظ الصورة!")

# ✅ /done
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photos = user_photos.get(user_id, [])

    if not photos:
        await update.message.reply_text("❌ لم ترسل أي صور.")
        return

    try:
        images = [Image.open(p).convert("RGB") for p in photos]
        pdf_path = f"{user_id}.pdf"
        images[0].save(pdf_path, save_all=True, append_images=images[1:])
        await update.message.reply_document(open(pdf_path, "rb"))
        await update.message.reply_text("📄 تم إنشاء ملف PDF!")

        for p in photos:
            os.remove(p)
        os.remove(pdf_path)
        user_photos[user_id] = []

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ: {e}")

# ✅ تشغيل البوت
async def run_bot():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("❌ لم يتم العثور على التوكن")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("✅ البوت يعمل الآن...")
    await app.run_polling()

# ✅ Main
if __name__ == "__main__":
    nest_asyncio.apply()
    keep_alive()
    asyncio.run(run_bot())
