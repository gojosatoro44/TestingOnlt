import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Admin ID - Replace with your Telegram ID
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Set this in Railway environment variables

# File to store approved users
APPROVED_USERS_FILE = 'approved_users.json'

# Load approved users
def load_approved_users():
    try:
        if os.path.exists(APPROVED_USERS_FILE):
            with open(APPROVED_USERS_FILE, 'r') as f:
                return set(json.load(f))
        return set()
    except:
        return set()

# Save approved users
def save_approved_users(users):
    with open(APPROVED_USERS_FILE, 'w') as f:
        json.dump(list(users), f)

approved_users = load_approved_users()

# Check if user is approved
def is_approved(user_id):
    return user_id in approved_users or user_id == ADMIN_ID

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Admin is always approved
    if user_id == ADMIN_ID:
        await show_main_menu(update, context)
        return
    
    # Check if user is approved
    if is_approved(user_id):
        await show_main_menu(update, context)
        return
    
    # User needs approval
    keyboard = [
        [InlineKeyboardButton("🔐 Get Approval", callback_data='request_approval')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ **Access Denied**\n\n"
        "You need approval from the admin to use this bot.\n"
        "Click the button below to request access.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Show main menu
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧪 Testing 1", callback_data='testing1')],
        [InlineKeyboardButton("👨‍💻 Made By Zahid", callback_data='made_by')],
        [InlineKeyboardButton("💻 Own Coding", callback_data='own_coding')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = "✅ **Welcome to the Bot!**\n\nSelect an option below:"
    
    if update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.edit_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

# Handle button callbacks
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    # Request approval
    if query.data == 'request_approval':
        if is_approved(user_id):
            await query.message.edit_text("✅ You are already approved!")
            await show_main_menu(update, context)
            return
        
        # Send approval request to admin
        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f'approve_{user_id}'),
                InlineKeyboardButton("❌ Reject", callback_data=f'reject_{user_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 **New Approval Request**\n\n"
                     f"👤 Name: {user.first_name} {user.last_name or ''}\n"
                     f"🆔 User ID: `{user_id}`\n"
                     f"📱 Username: @{user.username or 'No username'}\n\n"
                     f"Do you want to approve this user?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            await query.message.edit_text(
                "📩 **Approval Request Sent!**\n\n"
                "Your request has been sent to the admin.\n"
                "Please wait for approval."
            )
        except Exception as e:
            logger.error(f"Error sending approval request: {e}")
            await query.message.edit_text(
                "❌ Error sending approval request. Please try again later."
            )
    
    # Admin approves user
    elif query.data.startswith('approve_'):
        if user_id != ADMIN_ID:
            await query.answer("⛔ Only admin can approve users!", show_alert=True)
            return
        
        target_user_id = int(query.data.split('_')[1])
        approved_users.add(target_user_id)
        save_approved_users(approved_users)
        
        await query.message.edit_text(
            f"✅ **User Approved!**\n\n"
            f"User ID: `{target_user_id}` has been approved.",
            parse_mode='Markdown'
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="🎉 **Congratulations!**\n\n"
                     "Your request has been approved by the admin.\n"
                     "You can now use the bot. Send /start to begin!",
                parse_mode='Markdown'
            )
        except:
            pass
    
    # Admin rejects user
    elif query.data.startswith('reject_'):
        if user_id != ADMIN_ID:
            await query.answer("⛔ Only admin can reject users!", show_alert=True)
            return
        
        target_user_id = int(query.data.split('_')[1])
        
        await query.message.edit_text(
            f"❌ **User Rejected!**\n\n"
            f"User ID: `{target_user_id}` has been rejected.",
            parse_mode='Markdown'
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="❌ **Approval Rejected!**\n\n"
                     "Your request has been rejected by the owner.\n\n"
                     "Contact: @dtxzahid",
                parse_mode='Markdown'
            )
        except:
            pass
    
    # Main menu options
    elif query.data in ['testing1', 'made_by', 'own_coding']:
        if not is_approved(user_id):
            await query.answer("⛔ You need approval to use this bot!", show_alert=True)
            return
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            "✨ **Made By @dtxzahid with own coding**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # Back to menu
    elif query.data == 'back_to_menu':
        if not is_approved(user_id):
            await query.answer("⛔ You need approval to use this bot!", show_alert=True)
            return
        await show_main_menu(update, context)

# Handle any message from unapproved users
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_approved(user_id):
        keyboard = [
            [InlineKeyboardButton("🔐 Get Approval", callback_data='request_approval')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ **Access Denied**\n\n"
            "You need approval from the admin to use this bot.\n"
            "Click the button below to request access.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Main function
def main():
    # Get bot token from environment variable
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return
    
    if ADMIN_ID == 0:
        logger.error("ADMIN_ID environment variable not set!")
        return
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
