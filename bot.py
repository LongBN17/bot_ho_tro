from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import json
import os
import re
from dotenv import load_dotenv
import logging

# --- Custom Logging Filter ---
class CustomEditAddFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        return any(keyword in msg for keyword in [
            "🆕 Thêm mới Note",
            "🆕 Thêm mới Logic",
            "🆕 Thêm mới Issue",
            "✏️ Đã cập nhật"
        ])

# --- Logging setup ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("bot_tele_log.txt", mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
file_handler.addFilter(CustomEditAddFilter())

logger.handlers = []  # Clear default handlers
logger.addHandler(file_handler)

# --- Constants ---
LOAI, VERSION, TEN, MODULE, MO_TA, GIAI_PHAP = range(6)
EDIT_ID = range(1)

# --- Load environment ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# --- Load & Save data ---
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def search_data(query):
    query = query.strip().lower()
    data = load_data()
    match = re.search(r"id[:=\s]*([0-9]+)", query)
    if match:
        id_number = int(match.group(1))
        return [item for item in data if item.get("ID") == id_number]
    if query.isdigit():
        id_number = int(query)
        return [item for item in data if item.get("ID") == id_number]
    return [item for item in data if query in json.dumps(item, ensure_ascii=False).lower()]

# --- Command: /add ---
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(
        [["Issue", "Note", "Logic"], ["Huỷ"]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text("📌 Chọn loại dữ liệu muốn thêm:", reply_markup=reply_markup)
    return LOAI

async def get_loai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loai = update.message.text.strip()
    if loai == "Huỷ":
        return await cancel(update, context)
    context.user_data["new_entry"] = {"Loại": loai}
    if loai == "Issue":
        await update.message.reply_text("🔹 Nhập Version:", reply_markup=ReplyKeyboardMarkup([["Huỷ"]], one_time_keyboard=True, resize_keyboard=True))
        return VERSION
    else:
        context.user_data["new_entry"]["Version"] = ""
        context.user_data["new_entry"]["Giải Pháp"] = ""
        await update.message.reply_text("🔹 Nhập Module:", reply_markup=ReplyKeyboardMarkup([["Huỷ"]], one_time_keyboard=True, resize_keyboard=True))
        return MODULE

async def get_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == "Huỷ":
        return await cancel(update, context)
    context.user_data["new_entry"]["Version"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập Tên Issue:", reply_markup=ReplyKeyboardMarkup([["Huỷ"]], one_time_keyboard=True, resize_keyboard=True))
    return TEN

async def get_ten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == "Huỷ":
        return await cancel(update, context)
    context.user_data["new_entry"]["Tên"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập Module:", reply_markup=ReplyKeyboardMarkup([["Huỷ"]], one_time_keyboard=True, resize_keyboard=True))
    return MODULE

async def get_module(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == "Huỷ":
        return await cancel(update, context)
    context.user_data["new_entry"]["Module"] = update.message.text.strip()
    await update.message.reply_text("🔹 Nhập Mô tả/Nguyên nhân:", reply_markup=ReplyKeyboardMarkup([["Huỷ"]], one_time_keyboard=True, resize_keyboard=True))
    return MO_TA

async def get_mo_ta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == "Huỷ":
        return await cancel(update, context)
    context.user_data["new_entry"]["Mô Tả"] = update.message.text.strip()
    if context.user_data["new_entry"]["Loại"] == "Issue":
        await update.message.reply_text("🔹 Nhập Giải pháp/Hướng xử lý:", reply_markup=ReplyKeyboardMarkup([["Huỷ"]], one_time_keyboard=True, resize_keyboard=True))
        return GIAI_PHAP
    else:
        await save_entry(update, context)
        context.user_data.clear()
        return ConversationHandler.END

async def get_giai_phap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == "Huỷ":
        return await cancel(update, context)
    context.user_data["new_entry"]["Giải Pháp"] = update.message.text.strip()
    await save_entry(update, context)
    context.user_data.clear()
    return ConversationHandler.END

async def save_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = context.user_data["new_entry"]
    data = load_data()
    max_id = max([item.get("ID", 0) for item in data], default=0)
    entry["ID"] = max_id + 1
    data.append(entry)
    save_data(data)
    logging.info(f"🆕 Thêm mới {entry['Loại']}: {json.dumps(entry, ensure_ascii=False)}")
    await update.message.reply_text(f"✅ Đã lưu dữ liệu mới! (🆔 ID: {entry['ID']})")

# --- Edit ---
async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✏️ Nhập ID của bản ghi bạn muốn chỉnh sửa:")
    return EDIT_ID

async def edit_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ ID không hợp lệ. Vui lòng nhập số.")
        return EDIT_ID
    data = load_data()
    entry_id = int(text)
    entry = next((item for item in data if item.get("ID") == entry_id), None)
    if not entry:
        await update.message.reply_text(f"❌ Không tìm thấy bản ghi với ID {entry_id}.")
        return ConversationHandler.END
    context.user_data["edit_entry"] = entry
    context.user_data["data"] = data
    await update.message.reply_text("📋 Chọn trường bạn muốn chỉnh sửa:", reply_markup=ReplyKeyboardMarkup([
        ["Loại", "Tên", "Module"], ["Mô Tả", "Version", "Giải Pháp"], ["Huỷ"]
    ], one_time_keyboard=True, resize_keyboard=True))
    return "CHOOSE_FIELD"

async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.strip()
    valid_fields = ["Loại", "Tên", "Module", "Mô Tả", "Version", "Giải Pháp"]
    if field not in valid_fields:
        return await cancel(update, context)
    context.user_data["editing_field"] = field
    await update.message.reply_text(f"✍️ Nhập giá trị mới cho {field}:")
    return "SET_FIELD"

async def set_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text.strip()
    field = context.user_data["editing_field"]
    entry = context.user_data["edit_entry"]
    data = context.user_data["data"]
    entry[field] = new_value
    save_data(data)

    log_data = {
        "ID": entry.get("ID"),
        "Trường": field,
        "Giá trị mới": new_value
    }
    logging.info("✏️ Đã cập nhật: %s", json.dumps(log_data, ensure_ascii=False))

    await update.message.reply_text(f"✅ Đã cập nhật {field} thành:\n➡️ {new_value}")
    context.user_data.clear()
    return ConversationHandler.END

# --- Cancel ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Đã huỷ thao tác.", reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True))
    return ConversationHandler.END

# --- Search ---
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
        part = f"🔖 Loại: {item.get('Loại', '')}\n📌 Module: {item.get('Module', '')}\n🆔 ID: {item.get('ID', '')}"
        if item.get("Version"): part += f"\n🧩 Version: {item.get('Version')}"
        if item.get("Tên"): part += f"\n📎 Tên: {item.get('Tên')}"
        if item.get("Mô Tả"): part += f"\n📄 Mô tả: {item.get('Mô Tả')}"
        if item.get("Giải Pháp"): part += f"\n✅ Giải pháp: {item.get('Giải Pháp')}"
        response_parts.append(part)
    full_response = "\n\n---\n\n".join(response_parts)
    max_len = 4000
    if len(full_response) <= max_len:
        await update.message.reply_text(full_response)
    else:
        buffer = ""
        for part in response_parts:
            if len(buffer) + len(part) + 5 < max_len:
                buffer += part + "\n\n---\n\n"
            else:
                await update.message.reply_text(buffer.strip())
                buffer = part + "\n\n---\n\n"
        if buffer.strip():
            await update.message.reply_text(buffer.strip())

# --- Error handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("❌ Có lỗi xảy ra. Vui lòng thử lại sau.")

# --- Main ---
if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN chưa được thiết lập trong biến môi trường!")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    cancel_text = MessageHandler(filters.Regex("^Huỷ$"), cancel)

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", start_add)],
        states={
            LOAI: [cancel_text, MessageHandler(filters.TEXT & ~filters.COMMAND, get_loai)],
            VERSION: [cancel_text, MessageHandler(filters.TEXT & ~filters.COMMAND, get_version)],
            TEN: [cancel_text, MessageHandler(filters.TEXT & ~filters.COMMAND, get_ten)],
            MODULE: [cancel_text, MessageHandler(filters.TEXT & ~filters.COMMAND, get_module)],
            MO_TA: [cancel_text, MessageHandler(filters.TEXT & ~filters.COMMAND, get_mo_ta)],
            GIAI_PHAP: [cancel_text, MessageHandler(filters.TEXT & ~filters.COMMAND, get_giai_phap)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", start_edit)],
        states={
            EDIT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_entry)],
            "CHOOSE_FIELD": [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_field)],
            "SET_FIELD": [MessageHandler(filters.TEXT & ~filters.COMMAND, set_field)],
        },
        fallbacks=[CommandHandler("cancel", cancel), cancel_text],
    )

    app.add_handler(add_conv)
    app.add_handler(edit_conv)
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("🤖 Bot is running...")
    app.run_polling()
