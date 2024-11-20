# -*- coding: utf-8 -*-
"""
Created 20 November 2024
@author:
@links:
@description:
"""
# ┌─────────┐
# │ Imports │
# └─────────┘

from decouple import config
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.onboarding import (
    cancel,
    collect_dream,
    dream_prompt,
    handle_quiz_answer,
    start,
)
from utils.db import create_database_table

# ┌────────────┐
# │ Parameters │
# └────────────┘

BOT_TOKEN = config("BOT_TOKEN")

# ┌──────────┐
# │ Programs │
# └──────────┘


def main():
    """Main function to start the bot."""
    create_database_table("user_actions")  # Initialise the database table

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            "DREAM_PROMPT": [CallbackQueryHandler(dream_prompt, pattern="^agree$")],
            "COLLECT_DREAM": [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_dream)],
            "QUIZ_QUESTION": [CallbackQueryHandler(handle_quiz_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conversation_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
