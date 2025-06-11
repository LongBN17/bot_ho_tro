from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import json
import os
from dotenv import load_dotenv

# Constants for conversation steps
LOAI, TEN, MODULE, MO_TA, GIAI_PHAP, VERSION = range(6)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Load data from JSON
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save data to JSON
def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Main search function
def search_data(query):
    query = query.lower()
    return [item for item in load_data() if query in json.dumps(item, ensure_ascii=False).lower()]

# --- ADD FUNCTIONALITY ---

async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["Issue", "Note", "Logic"]], one_time_keyboard=True)
    await update.message.reply_text("📌 Chọn loại dữ liệu muốn thêm:", reply_markup=reply_markup)
    return LOAI

async def get_loai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loai = update.message.text.strip()
    context.user_data["new_entry"] = {"Loại": loai}
    if loai == "Issue":
        await update.message.reply_text("🔹 Nhập tên issue:")
        return TEN
    else:
        await update.message.reply_text("🔹 Nhập module:")
        return MODULE

async def get_ten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Tên"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập module:")
    return MODULE

async def get_module(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Module"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập mô tả:")
    return MO_TA

async def get_mo_ta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Mô Tả"] = update.message.text.strip()
    if context.user_data["new_entry"]["Loại"] == "Issue":
        await update.message.reply_text("🔹 Nhập giải pháp:")
        return GIAI_PHAP
    else:
        context.user_data["new_entry"]["Giải Pháp"] = ""
        context.user_data["new_entry"]["Version"] = ""
        await save_entry(update, context)
        return ConversationHandler.END

async def get_giai_phap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Giải Pháp"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập version:")
    return VERSION

async def get_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_entry"]["Version"] = update.message.text.strip()
    await save_entry(update, context)
    return ConversationHandler.END

async def save_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = context.user_data["new_entry"]
    data = load_data()
    data.append(entry)
    save_data(data)
    await update.message.reply_text("✅ Đã lưu dữ liệu mới!")

# --- SEARCH FUNCTIONALITY ---

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
            part = f"📝 {module}:\n{mo_ta}"
            response_parts.append(part)
        elif loai == "Logic":
            part = f"⚙️ {module}:\n"
            for line in mo_ta.split(";"):
                line = line.strip()
                if line:
                    part += f" - {line}\n"
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

# --- MAIN ---

if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN chưa được thiết lập trong biến môi trường!")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", start_add)],
        states={
            LOAI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_loai)],
            TEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ten)],
            MODULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_module)],
            MO_TA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mo_ta)],
            GIAI_PHAP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_giai_phap)],
            VERSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_version)],
        },
        fallbacks=[],
    )

    app.add_handler(add_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
