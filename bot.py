from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import json
import os
from dotenv import load_dotenv

# Load .env nếu có
load_dotenv()

# Load data từ file đã chuẩn hóa
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Tìm kiếm dữ liệu
def search_data(query):
    query = query.lower()
    results = []
    for item in data:
        if query in json.dumps(item, ensure_ascii=False).lower():
            results.append(item)
    return results

# Xử lý tin nhắn từ user
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return

    query = update.message.text
    results = search_data(query)

    if results:
        response = ""
        for item in results:
            type_ = item.get("type")

            if type_ == "issue":
                response += (
                    f"[{item.get('version')}] {item.get('module')}\n"
                    f"Issue: {item.get('issue')}\n"
                    f"Nguyên nhân: {item.get('cause')}\n"
                    f"Giải pháp: {item.get('solution')}\n"
                )

            elif type_ == "note":
                response += f"{item.get('title')}: {item.get('content')}\n"

            elif type_ == "logic":
                response += f"{item.get('title')}:\n"
                for k, v in item.get("details", {}).items():
                    response += f" - {k}: {v}\n"

            elif type_ == "list_note":
                response += f"{item.get('title')}:\n"
                for v in item.get("items", []):
                    if isinstance(v, str):
                        response += f" - {v}\n"
                    elif isinstance(v, dict):
                        for sub_k, sub_v in v.items():
                            response += f" - {sub_k}: {sub_v}\n"

            else:
                response += f"(Không rõ định dạng): {json.dumps(item, ensure_ascii=False)}\n"

            response += "\n---\n"

        await update.message.reply_text(response[:4000])
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
