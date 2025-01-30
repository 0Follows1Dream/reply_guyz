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

from bot.features import alien_race_command
from bot.onboarding import (
    cancel,
    collect_dream,
    collect_twitter_username,
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
create_database_table("threads")  # need to add a try if trigger already exists during restart etc
create_database_table("daily_tweet_counts")
create_database_table("weekly_categories")

dat = db_query("select * from user_actions order by timestamp desc")


def main():
    """Main function to start the bot."""

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start, filters=filters.ChatType.PRIVATE)],
        states={
            "DREAM_PROMPT": [CallbackQueryHandler(dream_prompt, pattern="^agree$")],
            "COLLECT_DREAM": [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, collect_dream)],
            "QUIZ_QUESTION": [CallbackQueryHandler(handle_quiz_answer)],
            "COLLECT_TWITTER_USERNAME": [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, collect_twitter_username)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel, filters=filters.ChatType.PRIVATE)],
        conversation_timeout=300,
        per_message=False,
        per_chat=True,
        per_user=True
    )

    application.add_handler(conversation_handler)

    add_replies_handlers(application)

    application.add_handler(CommandHandler("alien_races", alien_race_command, filters=filters.ChatType.PRIVATE))

    application.run_polling()


if __name__ == "__main__":
    main()
