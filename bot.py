from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ConversationHandler, ContextTypes, filters
)
import json
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: BOT_TOKEN chưa được thiết lập trong file .env!")
    exit(1)

DATA_FILE = "data.json"

# Đọc file JSON
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Ghi vào file JSON
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# =========================== SEARCH ===========================

def search_data(query):
    query = query.lower()
    data = load_data()
    return [item for item in data if query in json.dumps(item, ensure_ascii=False).lower()]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return

    query = update.message.text.strip()
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
        elif loai == "Note":
            part = f"📝 {module}:\n{mo_ta}"
        elif loai == "Logic":
            part = f"⚙️ {module}:\n"
            for line in mo_ta.split(";"):
                part += f" - {line.strip()}\n"
        else:
            continue
        response_parts.append(part.strip())

    full_response = "\n\n---\n\n".join(response_parts)
    max_len = 4000
    if len(full_response) <= max_len:
        await update.message.reply_text(full_response)
    else:
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

# =========================== ADD ===========================

(LOAI, TEN, MODULE, MOTA, GIAI_PHAP, VERSION) = range(6)

async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"] = {}
    await update.message.reply_text("🔹 Nhập loại (Issue / Note / Logic):")
    return LOAI

async def get_loai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loai = update.message.text.strip().capitalize()
    context.user_data["new_entry"]["Loại"] = loai
    if loai == "Issue":
        await update.message.reply_text("🔹 Nhập tên Issue:")
        return TEN
    else:
        context.user_data["new_entry"]["Tên"] = ""
        await update.message.reply_text("🔹 Nhập Module:")
        return MODULE

async def get_ten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Tên"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập Module:")
    return MODULE

async def get_module(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Module"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập mô tả:")
    return MOTA

async def get_mo_ta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Mô Tả"] = update.message.text.strip()
    if context.user_data["new_entry"]["Loại"] == "Issue":
        await update.message.reply_text("🔹 Nhập giải pháp:")
        return GIAI_PHAP
    else:
        context.user_data["new_entry"]["Giải Pháp"] = ""
        context.user_data["new_entry"]["Version"] = ""
        return await save_entry(update, context)

async def get_giai_phap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Giải Pháp"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập Version:")
    return VERSION

async def get_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Version"] = update.message.text.strip()
    return await save_entry(update, context)

async def save_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_entry = context.user_data["new_entry"]
    data = load_data()
    data.append(new_entry)
    save_data(data)
    await update.message.reply_text("✅ Đã lưu dữ liệu mới!")
    return ConversationHandler.END

# =========================== MAIN ===========================

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Handler cho tìm kiếm
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Handler cho thêm dữ liệu
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", start_add)],
        states={
            LOAI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_loai)],
            TEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ten)],
            MODULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_module)],
            MOTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mo_ta)],
            GIAI_PHAP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_giai_phap)],
            VERSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_version)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)

    print("🤖 Bot is running...")
    app.run_polling()
