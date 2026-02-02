import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= LOGGING =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DATA_FILE = "users.json"

# Validation
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID environment variable is not set!")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("ADMIN_ID must be a valid integer!")

# ================= DATA HANDLING =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Error reading users.json, starting fresh")
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

users = load_data()

# ================= START COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    # Approved users can see menu
    if uid in users and users[uid] == "approved":
        await show_menu(update)
        return

    # Not approved → show get approval button
    keyboard = [[InlineKeyboardButton("✅ Get Approval", callback_data="get_approval")]]
    await update.message.reply_text(
        "🚫 *Access Denied*\nYou must get approval first.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ================= GET APPROVAL =================
async def approval_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    uid = str(user.id)

    # Save as pending
    users[uid] = "pending"
    save_data(users)

    # Buttons for admin
    keyboard = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"approve_{uid}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")
        ]
    ]

    username_display = f"@{user.username}" if user.username else "No username"
    text = (
        "🔔 *New Approval Request*\n\n"
        f"👤 Name: {user.first_name}\n"
        f"🔗 Username: {username_display}\n"
        f"🆔 User ID: `{user.id}`"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        await query.edit_message_text("⏳ Approval request sent. Please wait for admin response.")
    except Exception as e:
        logger.error(f"Error sending approval request: {e}")
        await query.edit_message_text("❌ Error sending approval request. Please try again.")

# ================= APPROVE USER =================
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.data.split("_")[1]
    users[uid] = "approved"
    save_data(users)

    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text="✅ *Approval Accepted*\nYou can now use the bot. Type /start to continue.",
            parse_mode="Markdown"
        )
        await query.edit_message_text("✅ User Approved")
    except Exception as e:
        logger.error(f"Error approving user: {e}")
        await query.edit_message_text(f"⚠️ User approved but couldn't notify them.")

# ================= REJECT USER =================
async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.data.split("_")[1]
    users[uid] = "rejected"
    save_data(users)

    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text="❌ *Approval Rejected*\nApproval rejected by owner.\nContact 👉 @dtxzahid",
            parse_mode="Markdown"
        )
        await query.edit_message_text("❌ User Rejected")
    except Exception as e:
        logger.error(f"Error rejecting user: {e}")
        await query.edit_message_text(f"⚠️ User rejected but couldn't notify them.")

# ================= MENU =================
async def show_menu(update):
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

# ================= MENU CLICK =================
async def menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✨ Made By @dtxzahid with own coding")

# ================= ERROR HANDLER =================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")

# ================= MAIN =================
if __name__ == "__main__":
    logger.info("Starting bot...")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(approval_request, pattern="get_approval"))
    app.add_handler(CallbackQueryHandler(approve_user, pattern="approve_"))
    app.add_handler(CallbackQueryHandler(reject_user, pattern="reject_"))
    app.add_handler(CallbackQueryHandler(menu_click, pattern="menu"))
    
    # Add error handler
    app.add_error_handler(error_handler)

    logger.info("Bot started successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES
