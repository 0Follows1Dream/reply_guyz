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
from bot.replies import add_replies_handlers
from utils.db import create_database_table, db_query

# ┌────────────┐
# │ Parameters │
# └────────────┘

BOT_TOKEN = config("BOT_TOKEN")

# ┌──────────┐
# │ Programs │
# └──────────┘

create_database_table("user_actions")
create_database_table("alien_race_teams")
create_database_table("threads")


dat = db_query("select * from user_actions order by timestamp desc")


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

    add_replies_handlers(application)

    application.run_polling()


if __name__ == "__main__":
    main()
