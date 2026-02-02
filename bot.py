import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")           # Telegram bot token
ADMIN_ID = int(os.getenv("ADMIN_ID"))        # Admin Telegram ID (as integer)
DATA_FILE = "users.json"

# ================= DATA HANDLING =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

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

    text = (
        "🔔 *New Approval Request*\n\n"
        f"👤 Name: {user.first_name}\n"
        f"🔗 Username: @{user.username}\n"
        f"🆔 User ID: `{user.id}`"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    await query.edit_message_text("⏳ Approval request sent. Please wait for admin response.")

# ================= APPROVE USER =================
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.data.split("_")[1]
    users[uid] = "approved"
    save_data(users)

    await context.bot.send_message(
        chat_id=int(uid),
        text="✅ *Approval Accepted*\nYou can now use the bot.",
        parse_mode="Markdown"
    )

    await query.edit_message_text("✅ User Approved")

# ================= REJECT USER =================
async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.data.split("_")[1]
    users[uid] = "rejected"
    save_data(users)

    await context.bot.send_message(
        chat_id=int(uid),
        text="❌ *Approval Rejected*\nApproval rejected by owner.\nContact 👉 @dtxzahid",
        parse_mode="Markdown"
    )

    await query.edit_message_text("❌ User Rejected")

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

# ================= MAIN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(approval_request, pattern="get_approval"))
app.add_handler(CallbackQueryHandler(approve_user, pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject_user, pattern="reject_"))
app.add_handler(CallbackQueryHandler(menu_click, pattern="menu"))

app.run_polling()
