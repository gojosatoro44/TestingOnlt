import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DATA_FILE = "users.json"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID not set!")

ADMIN_ID = int(ADMIN_ID)

# Data handling
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

users = load_data()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    if uid in users and users[uid] == "approved":
        keyboard = [
            [InlineKeyboardButton("🧪 Testing 1", callback_data="menu")],
            [InlineKeyboardButton("👑 Made By Zahid", callback_data="menu")],
            [InlineKeyboardButton("💻 Own Coding", callback_data="menu")]
        ]
        await update.message.reply_text(
            "📋 *Main Menu*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    keyboard = [[InlineKeyboardButton("✅ Get Approval", callback_data="get_approval")]]
    await update.message.reply_text(
        "🚫 *Access Denied*\nYou must get approval first.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def approval_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uid = str(user.id)

    users[uid] = "pending"
    save_data(users)

    keyboard = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"approve_{uid}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")
        ]
    ]

    username_display = f"@{user.username}" if user.username else "No username"
    text = f"🔔 *New Approval Request*\n\n👤 Name: {user.first_name}\n🔗 Username: {username_display}\n🆔 User ID: `{user.id}`"

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    await query.edit_message_text("⏳ Approval request sent. Please wait.")

async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.data.split("_")[1]
    users[uid] = "approved"
    save_data(users)

    await context.bot.send_message(
        chat_id=int(uid),
        text="✅ *Approval Accepted*\nYou can now use the bot. Type /start",
        parse_mode="Markdown"
    )
    await query.edit_message_text("✅ User Approved")

async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.data.split("_")[1]
    users[uid] = "rejected"
    save_data(users)

    await context.bot.send_message(
        chat_id=int(uid),
        text="❌ *Approval Rejected*\nContact 👉 @dtxzahid",
        parse_mode="Markdown"
    )
    await query.edit_message_text("❌ User Rejected")

async def menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✨ Made By @dtxzahid")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

# Main
if __name__ == "__main__":
    logger.info("Starting bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(approval_request, pattern="get_approval"))
    app.add_handler(CallbackQueryHandler(approve_user, pattern="approve_"))
    app.add_handler(CallbackQueryHandler(reject_user, pattern="reject_"))
    app.add_handler(CallbackQueryHandler(menu_click, pattern="menu"))
    app.add_error_handler(error_handler)
    
    logger.info("Bot running!")
    app.run_polling()
