from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import json
import os
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

# Load dữ liệu đã chuẩn hóa
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Hàm tìm kiếm
def search_data(query):
    query = query.lower()
    return [item for item in data if query in json.dumps(item, ensure_ascii=False).lower()]

# Hàm xử lý message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return

    query = update.message.text
    results = search_data(query)

    if not results:
        await update.message.reply_text("❌ Không tìm thấy kết quả phù hợp.")
        return

    response_parts = []

    for item in results:
        loai = item.get("Loại", "").capitalize()
        module = item.get("Module", "")
        mo_ta = item.get("Mô Tả", "")
        version = item.get("Version", "")
        ten = item.get("Tên", "")
        giai_phap = item.get("Giải Pháp", "")

        if loai == "Issue":
            part = (
                f"[{version}] {module}\n"
                f"❗ Issue: {ten}\n"
                f"📌 Nguyên nhân: {mo_ta}\n"
                f"✅ Giải pháp: {giai_phap}"
            )
            response_parts.append(part)

        elif loai == "Note":
            # Note không có tên, lấy module làm tiêu đề, mô tả làm nội dung
            part = f"📝 {module}:\n{mo_ta}"
            response_parts.append(part)

        elif loai == "Logic":
            # Logic cũng không có tên, chỉ module + mô tả
            # Mô tả có thể chứa nhiều phần, tách theo dấu ";" cho dễ đọc
            part = f"⚙️ {module}:\n"
            for line in mo_ta.split(";"):
                line = line.strip()
                if line:
                    part += f" - {line}\n"
            response_parts.append(part.strip())

        else:
            continue  # Bỏ qua loại khác

    # Ghép các phần, ngắt bằng "---"
    full_response = "\n\n---\n\n".join(response_parts)

    # Telegram giới hạn 4096 ký tự cho 1 tin nhắn
    max_len = 4000
    if len(full_response) <= max_len:
        await update.message.reply_text(full_response)
    else:
        # Cắt theo đoạn (---) để gửi từng phần
        parts = full_response.split("\n\n---\n\n")
        buffer = ""
        for part in parts:
            if len(buffer) + len(part) + 5 < max_len:
                buffer += part + "\n\n---\n\n"
            else:
                await update.message.reply_text(buffer.strip())
                buffer = part + "\n\n---\n\n"
        if buffer.strip():
            await update.message.reply_text(buffer.strip())

# Khởi chạy bot
if __name__ == '__main__':
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN chưa được thiết lập trong biến môi trường!")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
