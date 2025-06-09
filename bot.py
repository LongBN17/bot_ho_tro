from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os
from dotenv import load_dotenv

# Load .env nếu có
load_dotenv()

# Load data
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Tìm kiếm dữ liệu
def search_data(query):
    query = query.lower()
    results = []

    for item in data:
        # Chuyển item sang chuỗi JSON và tìm query trong đó
        if query in json.dumps(item, ensure_ascii=False).lower():
            results.append(item)

    return results

# Xử lý tin nhắn từ user
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return  # tránh lỗi nếu message rỗng

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
                    response += f"{k}:\n"
                    for x in v:
                        if isinstance(x, str):
                            response += f"- {x}\n"
                        else:
                            response += f"- {json.dumps(x, ensure_ascii=False)}\n"
                else:
                    response += f"{k}: {v}\n"
            response += "\n---\n"
        await update.message.reply_text(response[:4000])  # Giới hạn 4000 ký tự
    else:
        await update.message.reply_text("❌ Không tìm thấy kết quả phù hợp.")

# Khởi tạo bot và chạy
if __name__ == '__main__':
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN chưa được thiết lập trong biến môi trường!")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    # Thêm handler cho tin nhắn text (không phải command)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
