"""
Created 27 November 2024
@description: Handles thread creation, replies, and category management for the Telegram bot.
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

from utils.data_checks import check_url
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
    """
    Insert a new thread or reply into the database using the pop function.

    Args:
        category (str): The category of the thread. For replies, it will be fetched from the original thread.
        twitter_link (str): The Twitter link of the thread or reply.
        user_id (int): The Telegram user ID.
        username (str): The Telegram username.
        thread_id (int, optional): The ID of the original thread. None for new threads.

    Returns:
        int: The ID of the newly inserted thread.
    """
    # Adjust timestamp to match database format (without microseconds)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat(sep=" ")

    if thread_id is not None:
        # Fetch category from the original thread
        original_thread = db_query(
            """
            SELECT category FROM threads
            WHERE id = :thread_id
            """,
            {"thread_id": thread_id},
        )
        if original_thread.empty:
            raise ValueError(f"Original thread with id {thread_id} not found.")
        category = original_thread.iloc[0]["category"]
        print(f"Fetched category '{category}' for reply to thread ID {thread_id}.")
    else:
        print(f"Creating new thread in category '{category}'.")

    data = pd.DataFrame(
        [
            {
                "id": None,  # Auto-incremented
                "timestamp": timestamp,
                "thread_id": thread_id,  # None for new threads
                "user_id": int(user_id),
                "username": username,
                "category": category,
                "twitter_link": twitter_link,
            }
        ]
    )

    # Insert the thread or reply
    try:
        pop(data, "threads")
        print(f"Inserted thread with Twitter link: {twitter_link}")
    except Exception as e:
        print(f"Error inserting thread: {e}")
        return None  # Or handle accordingly

    # Retrieve the new thread's ID without relying on exact timestamp
    new_thread_df = db_query(
        """
        SELECT id FROM threads
        WHERE user_id = :user_id AND twitter_link = :twitter_link
        ORDER BY id DESC LIMIT 1
        """,
        {"user_id": user_id, "twitter_link": twitter_link},
    )

    if new_thread_df.empty:
        raise ValueError("Failed to insert thread.")

    new_thread_id = int(new_thread_df.iloc[0]["id"])
    print(f"New thread ID: {new_thread_id}")
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
    print(f"Fetched {len(threads_df)} original threads from the last 24 hours.")

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
    print(f"User {user_id} has replied to threads: {replied_thread_ids}")

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
    print(f"User {user_id} has created threads: {user_created_thread_ids}")

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
            print(f"Topic '{topic}' has {len(unreplied_thread_ids)} unreplied threads.")
        else:
            topic_has_unreplied[topic] = False
            print(f"Topic '{topic}' has no unreplied threads.")

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
    await update.effective_message.reply_text("Topics:", reply_markup=reply_markup)


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
    print(f"Fetched {len(threads_df)} threads in category '{category}'.")

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
    print(f"User {user_id} has replied to threads: {replied_thread_ids}")

    # Delete the previous message (the one with the topic selection)
    await query.message.delete()

    # Send a heading with a border
    heading_text = f"───────────\n*{category}*\n───────────"
    await query.message.chat.send_message(
        heading_text,
        parse_mode=ParseMode.MARKDOWN,
    )

    # Provide the option to create a new thread and go back to menu
    keyboard = [
        [
            InlineKeyboardButton("Create 🧵", callback_data=f"create_thread_{category}"),
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
                print(f"Thread ID {thread_id} already replied by user {user_id}.")
            else:
                # User has not replied to this thread
                reply_button = InlineKeyboardButton("Reply 𝕏", url=xcom_tweet_link)
                submit_reply_button = InlineKeyboardButton(
                    "Submit Reply", callback_data=f"reply_thread_{thread_id}"
                )
                reply_markup_thread = InlineKeyboardMarkup([[reply_button, submit_reply_button]])
                print(f"Thread ID {thread_id} available for reply by user {user_id}.")

            # Send the link as a message with the reply buttons
            await query.message.chat.send_message(vxtwitter_link, reply_markup=reply_markup_thread)

        # Send the message with the selection buttons
        await query.message.chat.send_message(
            "Or:",
            reply_markup=reply_markup,
        )


async def reply_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Submit Reply' button under a thread."""
    query = update.callback_query
    thread_id = int(query.data.split("_", 2)[2])
    user_id = query.from_user.id

    print(f"User {user_id} is attempting to reply to thread ID {thread_id}.")

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
        print(f"User {user_id} has already replied to thread ID {thread_id}.")
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
    print(f"Prompted user {user_id} to paste their reply URL.")


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
    print(f"Prompted user {query.from_user.id} to paste their new thread URL.")


async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user inputs for creating threads or replying."""
    user_input = update.message.text.strip()
    action = context.user_data.get("action")

    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Unknown"

    if action == "create_thread":
        # Validate the URL
        if not check_url(user_input):
            # Delete the user's invalid message
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=update.message.message_id
            )
            # Optionally delete the previous prompt message
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=context.user_data["prompt_message_id"]
            )
            # Inform the user and re-prompt
            force_reply = ForceReply(selective=True)
            prompt_message = await update.message.chat.send_message(
                "The URL you provided is not formatted correctly. Please try again:",
                reply_markup=force_reply,
            )
            # Store the new prompt message ID
            context.user_data["prompt_message_id"] = prompt_message.message_id
            print(f"User {user_id} provided invalid URL for creating thread: {user_input}")
            return  # Do not proceed further

        # Delete the prompt message and user's reply to keep the chat clean
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=context.user_data["prompt_message_id"]
        )
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=update.message.message_id
        )

        category = context.user_data["category"]
        # Convert user input to x.com link for storage
        xcom_link = get_xcom_link(user_input)

        # Insert the new thread
        new_thread_id = insert_thread(
            category=category,
            twitter_link=xcom_link,
            user_id=user_id,
            username=username,
        )

        if new_thread_id:
            await update.message.chat.send_message(
                f"Your thread has been created in *{category}*.",
                parse_mode=ParseMode.MARKDOWN,
            )
            print(f"User {user_id} created new thread ID {new_thread_id} in category '{category}'.")
        else:
            await update.message.chat.send_message(
                "There was an error creating your thread. Please try again.",
                parse_mode=ParseMode.MARKDOWN,
            )
            print(f"Failed to create thread for user {user_id}.")

        context.user_data.clear()

    elif action == "reply":
        # Validate the URL
        if not check_url(user_input):
            # Delete the user's invalid message
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=update.message.message_id
            )
            # Optionally delete the previous prompt message
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=context.user_data["prompt_message_id"]
            )
            # Inform the user and re-prompt
            force_reply = ForceReply(selective=True)
            prompt_message = await update.message.chat.send_message(
                "The URL you provided is not formatted correctly. Please try again:",
                reply_markup=force_reply,
            )
            # Store the new prompt message ID
            context.user_data["prompt_message_id"] = prompt_message.message_id
            print(f"User {user_id} provided invalid URL for replying: {user_input}")
            return  # Do not proceed further

        # Delete the prompt message and user's reply to keep the chat clean
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=context.user_data["prompt_message_id"]
        )
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=update.message.message_id
        )

        thread_id = context.user_data["thread_id"]
        # Convert user input to x.com link for storage
        xcom_link = get_xcom_link(user_input)

        # Insert the reply
        new_reply_id = insert_thread(
            category=None,  # Not needed for replies as it's fetched from the original thread
            twitter_link=xcom_link,
            user_id=user_id,
            username=username,
            thread_id=thread_id,
        )

        if new_reply_id:
            await update.message.chat.send_message("Your reply has been posted.")
            print(f"User {user_id} replied to thread ID {thread_id} with reply ID {new_reply_id}.")
        else:
            await update.message.chat.send_message(
                "There was an error posting your reply. Please try again.",
                parse_mode=ParseMode.MARKDOWN,
            )
            print(f"Failed to post reply for user {user_id} to thread ID {thread_id}.")

        context.user_data.clear()
    else:
        # Handle unexpected user inputs
        await update.message.reply_text("Please select an action from the menu.")
        print(f"User {user_id} sent unexpected input: {user_input}")


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to the main menu."""
    query = update.callback_query
    await query.answer()
    # Delete the previous message if needed
    await query.message.delete()
    await menu(update, context)
    print(f"User {query.from_user.id} navigated back to the main menu.")


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """No operation callback handler."""
    await update.callback_query.answer()
    print("Received noop callback.")


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
