import logging
import os

from telegram import (
    BotCommand, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")

# Bir nechta adminlar
ADMIN_IDS = {7355079609, 6468400089}

user_states = {}
user_phones = {}
blocked_users = set()  # Bloklangan foydalanuvchilar

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# ==================== START ====================
async def start_function(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in blocked_users:
        return await update.message.reply_text("🚫 Siz botdan foydalanishdan bloklangansiz.")

    commands = [
        BotCommand(command='start', description="For starting the bot"),
        BotCommand(command='help', description="For getting help"),
        BotCommand(command='info', description="For getting info"),
        BotCommand(command='comment', description="For write comments"),
        BotCommand(command='admin', description="Admin panel (admin only)")
    ]
    await context.bot.set_my_commands(commands=commands)

    buttons = [
        [InlineKeyboardButton(text="Police number", callback_data="police")],
        [InlineKeyboardButton(text="Emergency number", callback_data="emergency")],
        [InlineKeyboardButton(text="Fire service", callback_data="fire")],
        [InlineKeyboardButton(text="Ambulance", callback_data="ambulance")],
        [InlineKeyboardButton(text="Gas emergency", callback_data="gas")],
        [InlineKeyboardButton(text="Search all numbers", callback_data="all_numbers")]
    ]
    await update.message.reply_text(
        text="Choose the button from the following list:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    logging.info(f"User {update.message.from_user.id} started bot!")
    return None


# ==================== HELP ====================
async def help_function(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in blocked_users:
        return await update.message.reply_text("🚫 Siz botdan foydalanishdan bloklangansiz.")
    await update.message.reply_text("For using bot please type /start!")
    logging.info(f"User {update.message.from_user.id} get help from bot!")
    return None


# ==================== COMMENT ====================
async def comment_function(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in blocked_users:
        return await update.message.reply_text("🚫 Siz botdan foydalanishdan bloklangansiz.")

    reply_text = '📌 Iltimos, komment yozishda hurmatli bo‘ling.\n❗ Haqoratli so‘z ishlatsangiz bloklanasiz.\n\n☎ Telefon raqamingizni ulashing:'
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton(text="📱 Share phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(reply_text, reply_markup=reply_markup)
    logging.info(f"User {update.message.from_user.id} start commenting!")
    return None


async def phone_handler(update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact:
        user_id = update.message.from_user.id
        if user_id in blocked_users:
            return await update.message.reply_text("🚫 Siz botdan foydalanishdan bloklangansiz.")

        user_states[user_id] = "waiting_for_comment"
        user_phones[user_id] = contact.phone_number
        await update.message.reply_text("✅ Phone number received!\n✏️ Now please write your comment:")
        logging.info(f"User {user_id} shared phone: {contact.phone_number}")
        return None
    return None


async def text_handler(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in blocked_users:
        return await update.message.reply_text("🚫 Siz botdan foydalanishdan bloklangansiz.")

    phone_number = user_phones.get(user_id, "No phone number")

    if user_states.get(user_id) == "waiting_for_comment":
        message = update.message.text

        # Har bir admin uchun komment yuborish
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📩 New comment from {update.message.from_user.full_name} ({user_id}):\n"
                     f"📞 Phone: {phone_number}\n\n"
                     f"{message}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 Block User", callback_data=f"block_{user_id}")]
                ])
            )

        logging.info(f"User {update.message.from_user.id} write {message}!")

        await update.message.reply_text("✅ Thank you for commenting. Your comment has been sent to the admin.")
        logging.info(f"User {user_id} comment sent to admins!")
        user_states[user_id] = None
        return None
    else:
        await update.message.reply_text("Sorry, I can't do that.")
        logging.info(f"User {user_id} type invalid text: {update.message.text}!")
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🚫 Invalid text from @EmergencyNumbersBot:\n"
                     f"First name: {update.effective_user.first_name}\n"
                     f"Last name: {update.effective_user.last_name or 'No lastname'}\n"
                     f"Username: {update.message.from_user.username or 'No username'}\n"
                     f"📞 Phone: {phone_number}\n"
                     f"Message: {update.message.text}"
            )
        return None


# ==================== INLINE MESSAGES ====================
async def inline_messages(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("block_") and query.from_user.id in ADMIN_IDS:
        block_id = int(query.data.split("_")[1])
        blocked_users.add(block_id)
        await context.bot.send_message(chat_id=block_id, text="🚫 Siz botdan foydalanishdan bloklandingiz.")
        await query.message.reply_text(f"✅ User {block_id} blocked.")
        return

    if query.data == 'police':
        await query.message.reply_text("Police number: 102!")
    elif query.data == 'emergency':
        await query.message.reply_text("Emergency number (General help): 112!")
    elif query.data == 'fire':
        await query.message.reply_text("Fire service number: 101!")
    elif query.data == 'ambulance':
        await query.message.reply_text("Ambulance number: 103!")
    elif query.data == 'gas':
        await query.message.reply_text("Gas emergency number: 104!")
    elif query.data == 'all_numbers':
        await query.message.reply_text(
            "Police number: 102!\n"
            "Emergency number (General help): 112!\n"
            "Fire service number: 101!\n"
            "Ambulance number: 103!\n"
            "Gas emergency number: 104!"
        )


# ==================== ADMIN PANEL ====================
async def admin_panel(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        return await update.message.reply_text("❌ You are not authorized to use this command.")
    await update.message.reply_text("✅ Welcome to Admin Panel.")
    return None


# ==================== MAIN ====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_function))
    app.add_handler(CommandHandler('help', help_function))
    app.add_handler(CommandHandler('info', lambda u, c: u.message.reply_text("Bot info.")))
    app.add_handler(CommandHandler("comment", comment_function))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.CONTACT, phone_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(inline_messages))

    print("Bot is working...")
    app.run_polling()


if __name__ == '__main__':
    main()
