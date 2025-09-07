import aiosqlite
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL = os.getenv("LOG_CHANNEL")

async def init_db():
    async with aiosqlite.connect("files.db") as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, file_id TEXT)"
        )
        await db.commit()

async def add_file(title: str, file_id: str):
    async with aiosqlite.connect("files.db") as db:
        await db.execute("INSERT INTO files (title, file_id) VALUES (?, ?)", (title, file_id))
        await db.commit()

async def search_files(query: str):
    async with aiosqlite.connect("files.db") as db:
        async with db.execute("SELECT title, file_id FROM files WHERE title LIKE ?", (f"%{query}%",)) as cursor:
            return await cursor.fetchall()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 I’m an Auto Filter Bot. Add me to your group and send a file to save it!")

async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        file = update.message.document
        await add_file(file.file_name, file.file_id)
        await update.message.reply_text(f"✅ File saved: {file.file_name}")
        await context.bot.send_message(LOG_CHANNEL, f"📂 File Saved:\n{file.file_name}\nBy: {update.effective_user.id}")

async def search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    results = await search_files(query)
    if not results:
        return
    buttons = []
    for title, file_id in results[:10]:
        buttons.append([InlineKeyboardButton(title, callback_data=f"get_{file_id}")])
    await update.message.reply_text(f"🔎 Results for: {query}", reply_markup=InlineKeyboardMarkup(buttons))
    await context.bot.send_message(LOG_CHANNEL, f"🔎 User {update.effective_user.id} searched: {query}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("get_"):
        file_id = query.data.replace("get_", "")
        await query.message.reply_document(document=file_id)
        await context.bot.send_message(LOG_CHANNEL, f"📤 Sent file {file_id} to user {query.from_user.id}")

async def main():
    await init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, save_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_query))
    app.add_handler(CallbackQueryHandler(button_click))
    print("🤖 Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
