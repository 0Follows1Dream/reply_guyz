"""
Created 27 November 2024
@author:
@links:
@description:
"""

# ┌─────────┐
# │ Imports │
# └─────────┘

from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse

import pandas as pd
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from utils.db import db_query, pop

# ┌────────────┐
# │ Parameters │
# └────────────┘

# List of topics
TOPICS = [
    "Anything Goes",
    "Big Targets",
    "NoM History",
    "Feeless Network",
    "Bitcoin LN Roots",
    "Taproot Opportunity",
    "Celebrate the Builders",
    "Daily Meta",
    "Multichain Expansion",
    "Roadmap",
    "Schizo",
]

# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘
# ┌─────────────────────┐
# │ Load & process data │
# └─────────────────────┘
# ┌──────────┐
# │ Programs │
# └──────────┘


def insert_thread(category, twitter_link, user_id, username, thread_id=None):
    """Insert a new thread or reply into the database using the pop function."""
    timestamp = datetime.now(timezone.utc).isoformat()

    data = pd.DataFrame(
        [
            {
                "id": None,  # Auto-incremented
                "timestamp": timestamp,
                "thread_id": thread_id,  # None for new threads
                "user_id": int(user_id),
                "username": username,
                "category": category if thread_id is None else None,  # Only for new threads
                "twitter_link": twitter_link,
            }
        ]
    )

    pop(data, "threads")

    # Optionally retrieve the new thread's ID
    new_thread_df = db_query(
        """
        SELECT id FROM threads
        WHERE twitter_link = :twitter_link AND user_id = :user_id
        ORDER BY timestamp DESC LIMIT 1
        """,
        {"twitter_link": twitter_link, "user_id": int(user_id)},
    )

    if new_thread_df.empty:
        raise ValueError("Failed to insert thread.")

    new_thread_id = int(new_thread_df.iloc[0]["id"])
    return new_thread_id


def get_xcom_link(twitter_link):
    """Convert Twitter link to x.com link for app redirection."""
    parsed_url = urlparse(twitter_link)
    netloc = parsed_url.netloc

    if "twitter.com" in netloc or "vxtwitter.com" in netloc or "mobile.twitter.com" in netloc:
        netloc = "x.com"
    # Rebuild the URL with the new netloc
    new_url = urlunparse(parsed_url._replace(netloc=netloc))
    return new_url


def get_vxtwitter_link(twitter_link):
    """Convert Twitter link to vxtwitter.com for embedding."""
    parsed_url = urlparse(twitter_link)
    netloc = parsed_url.netloc

    if "twitter.com" in netloc or "x.com" in netloc or "mobile.twitter.com" in netloc:
        netloc = "vxtwitter.com"
    # Rebuild the URL with the new netloc
    new_url = urlunparse(parsed_url._replace(netloc=netloc))
    return new_url


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the main menu with topics."""
    user_id = update.effective_user.id

    # Calculate the timestamp for 24 hours ago
    time_threshold = datetime.now(timezone.utc) - timedelta(days=1)
    time_threshold_str = time_threshold.strftime("%Y-%m-%d %H:%M:%S")

    # Get all threads (original posts) from the last 24 hours
    threads_df = db_query(
        """
        SELECT id, category
        FROM threads
        WHERE thread_id IS NULL AND timestamp >= :time_threshold
        """,
        {"time_threshold": time_threshold_str},
    )

    # Get all thread IDs that the user has replied to
    user_replies_df = db_query(
        """
        SELECT DISTINCT thread_id
        FROM threads
        WHERE user_id = :user_id AND thread_id IS NOT NULL
        """,
        {"user_id": user_id},
    )

    replied_thread_ids = set(user_replies_df["thread_id"].tolist())

    # Get all thread IDs that the user has created
    user_created_threads_df = db_query(
        """
        SELECT id
        FROM threads
        WHERE user_id = :user_id AND thread_id IS NULL
        """,
        {"user_id": user_id},
    )

    user_created_thread_ids = set(user_created_threads_df["id"].tolist())

    # Now, for each topic, determine if there are unreplied threads
    topic_has_unreplied = {}
    for topic in TOPICS:
        # Get thread IDs in this topic
        topic_threads = threads_df[threads_df["category"] == topic]
        topic_thread_ids = set(topic_threads["id"].tolist())
        # Compute unreplied thread IDs, excluding user's threads
        unreplied_thread_ids = topic_thread_ids - replied_thread_ids - user_created_thread_ids
        if unreplied_thread_ids:
            topic_has_unreplied[topic] = True
        else:
            topic_has_unreplied[topic] = False

    # Create the keyboard with two buttons per row and add 🌱 emoji where needed
    keyboard = []
    for i in range(0, len(TOPICS), 2):
        row = []
        for topic in TOPICS[i : i + 2]:
            display_text = topic
            if topic_has_unreplied.get(topic):
                display_text += " 🌱"
            row.append(InlineKeyboardButton(display_text, callback_data=f"topic_{topic}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text("Choose a topic:", reply_markup=reply_markup)


async def topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle topic selection and display threads with reply status."""
    query = update.callback_query
    category = query.data.split("_", 1)[1]
    user_id = query.from_user.id
    await query.answer()

    # Calculate the timestamp for 24 hours ago
    time_threshold = datetime.now(timezone.utc) - timedelta(days=1)
    time_threshold_str = time_threshold.strftime("%Y-%m-%d %H:%M:%S")

    # Retrieve all threads in the category from the last 24 hours
    threads_df = pd.DataFrame(
        db_query(
            """
            SELECT t.id, t.twitter_link
            FROM threads t
            WHERE t.category = :category AND t.thread_id IS NULL AND t.timestamp >= :time_threshold
            ORDER BY t.timestamp DESC LIMIT 3
            """,
            {"category": category, "time_threshold": time_threshold_str},
        )
    )

    # Retrieve thread IDs that the user has replied to
    replied_thread_ids = set(
        db_query(
            """
            SELECT DISTINCT r.thread_id
            FROM threads r
            WHERE r.user_id = :user_id AND r.thread_id IS NOT NULL
            """,
            {"user_id": user_id},
        )["thread_id"].tolist()
    )

    # Delete the previous message (the one with the topic selection)
    await query.message.delete()

    # Provide the option to create a new thread and go back to menu
    keyboard = [
        [
            InlineKeyboardButton("Create New Thread", callback_data=f"create_thread_{category}"),
            InlineKeyboardButton("Back to Topics", callback_data="back_to_menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if threads_df.empty:
        await query.message.chat.send_message(
            f"No threads in *{category}* from the last 24 hours.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,  # Include the keyboard here
        )
    else:
        # Send each thread individually with reply buttons
        for index, thread in threads_df.iterrows():
            twitter_link = thread["twitter_link"]
            thread_id = thread["id"]
            # Prepare the reply buttons
            xcom_tweet_link = get_xcom_link(twitter_link)
            vxtwitter_link = get_vxtwitter_link(twitter_link)

            if thread_id in replied_thread_ids:
                # User has already replied to this thread
                reply_button = InlineKeyboardButton("✅ Replied", url=xcom_tweet_link)
                # Disable the "Submit Reply" button by providing empty callback data
                submit_reply_button = InlineKeyboardButton("Already Replied", callback_data="noop")
                reply_markup_thread = InlineKeyboardMarkup([[reply_button, submit_reply_button]])
            else:
                # User has not replied to this thread
                reply_button = InlineKeyboardButton("Reply", url=xcom_tweet_link)
                submit_reply_button = InlineKeyboardButton(
                    "Submit Reply", callback_data=f"reply_thread_{thread_id}"
                )
                reply_markup_thread = InlineKeyboardMarkup([[reply_button, submit_reply_button]])

            # Send the link as a message with the reply buttons
            await query.message.chat.send_message(vxtwitter_link, reply_markup=reply_markup_thread)

        # Send the message with the selection buttons
        await query.message.chat.send_message(
            "Select an option:",
            reply_markup=reply_markup,
        )


async def reply_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Submit Reply' button under a thread."""
    query = update.callback_query
    thread_id = int(query.data.split("_", 2)[2])
    user_id = query.from_user.id

    # Check if the user has already replied to this thread
    existing_reply = db_query(
        """
        SELECT id FROM threads
        WHERE thread_id = :thread_id AND user_id = :user_id
        """,
        {"thread_id": thread_id, "user_id": user_id},
    )

    if not existing_reply.empty:
        await query.answer("You have already replied to this thread.", show_alert=True)
        return

    await query.answer()
    context.user_data["action"] = "reply"
    context.user_data["thread_id"] = thread_id

    # Use ForceReply to prompt the user
    force_reply = ForceReply(selective=True)
    prompt_message = await query.message.reply_text(
        "Please paste your Twitter reply URL:",
        reply_markup=force_reply,
    )

    # Store the message ID to delete it later
    context.user_data["prompt_message_id"] = prompt_message.message_id


async def create_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate the process to create a new thread."""
    query = update.callback_query
    await query.answer()
    category = query.data.split("_", 2)[2]
    context.user_data["action"] = "create_thread"
    context.user_data["category"] = category

    # Use ForceReply to prompt the user
    force_reply = ForceReply(selective=True)
    prompt_message = await query.message.reply_text(
        "Please paste your Twitter URL link to create a new thread:",
        reply_markup=force_reply,
    )

    # Store the message ID to delete it later
    context.user_data["prompt_message_id"] = prompt_message.message_id


async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user inputs for creating threads or replying."""
    user_input = update.message.text.strip()
    action = context.user_data.get("action")

    if action == "create_thread":
        # Delete the prompt message and user's reply to keep the chat clean
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=context.user_data["prompt_message_id"]
        )
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=update.message.message_id
        )

        category = context.user_data["category"]
        user = update.message.from_user
        # Convert user input to x.com link for storage
        xcom_link = get_xcom_link(user_input)
        insert_thread(
            category=category,
            twitter_link=xcom_link,
            user_id=user.id,
            username=user.username,
        )
        await update.message.chat.send_message(
            f"Your thread has been created in *{category}*.",
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data.clear()

    elif action == "reply":
        # Delete the prompt message and user's reply to keep the chat clean
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=context.user_data["prompt_message_id"]
        )
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=update.message.message_id
        )

        thread_id = context.user_data["thread_id"]
        user = update.message.from_user
        # Convert user input to x.com link for storage
        xcom_link = get_xcom_link(user_input)
        # Insert the reply
        insert_thread(
            category=None,  # Not needed for replies
            twitter_link=xcom_link,
            user_id=user.id,
            username=user.username,
            thread_id=thread_id,
        )
        await update.message.chat.send_message("Your reply has been posted.")
        context.user_data.clear()
    else:
        # Handle unexpected user inputs
        await update.message.reply_text("Please select an action from the menu.")


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to the main menu."""
    query = update.callback_query
    await query.answer()
    # Delete the previous message if needed
    await query.message.delete()
    await menu(update, context)


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """No operation callback handler."""
    await update.callback_query.answer()


def add_replies_handlers(application):
    """Register all handlers for the bot."""
    # Updated command from "menu" to "reply"
    application.add_handler(CommandHandler("reply", menu))
    application.add_handler(CallbackQueryHandler(topic_handler, pattern="^topic_"))
    application.add_handler(CallbackQueryHandler(reply_thread, pattern="^reply_thread_"))
    application.add_handler(CallbackQueryHandler(create_thread, pattern="^create_thread_"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    application.add_handler(CallbackQueryHandler(noop, pattern="^noop$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
