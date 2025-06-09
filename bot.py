from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os

# Load data
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Tìm kiếm
def search_data(query):
    query = query.lower()
    results = []

    for item in data:
        if query in json.dumps(item, ensure_ascii=False).lower():
            results.append(item)

    return results

# Xử lý tin nhắn
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    results = search_data(query)

    if results:
        response = ""
        for item in results:
            for k, v in item.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        response += f"{sub_k}: {sub_v}\n"
                elif isinstance(v, list):
                    response += f"{k}:\n" + "\n".join(f"- {x}" if isinstance(x, str) else json.dumps(x, ensure_ascii=False) for x in v) + "\n"
                else:
                    response += f"{k}: {v}\n"
            response += "\n---\n"
        await update.message.reply_text(response[:4000])  # Giới hạn Telegram (4096 ký tự)
    else:
        await update.message.reply_text("❌ Không tìm thấy kết quả phù hợp.")

# Khởi tạo bot
if __name__ == '__main__':
    TOKEN = "8186170651:AAFuvO2Tth5510cZK6H1GhhyXQrAr9bVsoA"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
