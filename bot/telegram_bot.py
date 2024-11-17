# -*- coding: utf-8 -*-
"""
Created 17 November 2024
@author:
@links:
@description:
"""
# ┌─────────┐
# │ Imports │
# └─────────┘

from datetime import datetime, timezone

import pandas as pd
from decouple import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from utils.db import create_database_table, pop

create_database_table("user_actions")  # to do init-db

# ┌────────────┐
# │ Parameters │
# └────────────┘

# from the BotFather
BOT_TOKEN = config("BOT_TOKEN")

# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘


def log_user_action(user_id, username, action, details, output, metadata=None):
    """
    Logs user actions into the database using the pop function.

    :param user_id: ID of the user performing the action
    :param username: Username of the user
    :param action: The action being performed
    :param details: Additional details about the action
    :param output: Response or result of the action
    :param metadata: Optional metadata for the action
    """
    # Get the current UTC timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    # Prepare the data as a DataFrame for the pop function
    data = pd.DataFrame(
        [
            {
                "id": None,  # MySQL will auto-generate the ID
                "timestamp": timestamp,
                "user_id": user_id,
                "username": username,
                "action": action,
                "details": details,
                "output": output,
                "metadata": metadata,
            }
        ]
    )

    # Insert the data into the database
    pop(data, "user_actions")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and provides welcome and housekeeping rules."""
    user = update.effective_user
    log_user_action(
        user_id=user.id,
        username=user.username,
        action="start",
        details="User started the bot",
        output="Welcome message sent",
    )

    welcome_message = (
        "*Welcome 👽...*"
        "\n\n_To reply guyz with a dream._"
        "\n\nWhich we are ambitiously calling..."
        "\n*Phase I community awareness campaign.*"
        "\n\n*Community built...*"
        "\n*Community guided...*"
        "\n*Community everything.*"
        "\n\nReply guyz with a dream, embark on a humble mission..."
        "\n*To spread the good word of Zenon and the Network of Momentum.*"
        "\n\nThis bot enables users to..."
        "\n\n*Design their own missions...*"
        "\n*Approach their own way...*"
        "\n*And to make this campaign their own...*"
        "\n*Who knows where it will lead.*"
        "\n\n*Housekeeping rules:*"
        "\n0️⃣1️⃣ _Always like others' posts._"
        "\n0️⃣2️⃣ _Always retweet others' posts._"
        "\n0️⃣3️⃣ _Always comment on others' posts._"
        "\n0️⃣4️⃣ _Use the lists to scroll through alien comrades scribing:_ [🐦 List](https://x.com/i/lists/1854575831080730698)"
        "\n0️⃣5️⃣ _Focus on simple messages with media._"
        "\n0️⃣6️⃣ _Break up text for easy reading._"
        "\n0️⃣7️⃣ _Always use $ZNN to assist degenerates across the crypto cosmic ecosystem._"
        "\n0️⃣8️⃣ _Try things even if they are weird._"
        "\n0️⃣9️⃣ _Quantity > Quality (unless you tweet from main)._"
        "\n0️⃣🔟 _Always be positive and warm._"
        "\n1️⃣1️⃣ _Never fade reply guyz with a dream._"
    )

    # Create a button for the user to acknowledge the rules
    keyboard = [[InlineKeyboardButton("3... 2... 1... Agree ✅", callback_data="agree")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_message, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def acknowledge_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user acknowledgment of the rules."""
    query = update.callback_query
    user = query.from_user

    log_user_action(
        user_id=user.id,
        username=user.username,
        action="acknowledge_rules",
        details="User acknowledged the rules",
        output="Acknowledgment message sent",
    )

    await query.answer()  # Acknowledge the callback
    await query.edit_message_text("Thank you for agreeing to the rules. Enjoy using the bot! 🎉")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles regular text messages."""
    user = update.effective_user
    user_message = update.message.text

    log_user_action(
        user_id=user.id,
        username=user.username,
        action="message",
        details=f"User sent message: {user_message}",
        output="Message echoed",
    )

    await update.message.reply_text(f"You said: {user_message}")


def main():
    """Main function to start the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))

    # CallbackQueryHandler for button clicks
    application.add_handler(CallbackQueryHandler(acknowledge_rules, pattern="^agree$"))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
