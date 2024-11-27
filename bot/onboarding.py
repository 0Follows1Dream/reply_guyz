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

import json
from collections import Counter
from datetime import datetime, timezone

import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from utils.db import pop
from utils.general import load_template_json, load_template_msg

# ┌─────────────────────┐
# │ Load & process data │
# └─────────────────────┘

# Load data
welcome_rules_msg = load_template_msg("welcome_rules.txt")
quiz_intro_msg = load_template_msg("quiz_intro.txt")
alien_races_data = load_template_json("alien_races.json")
quiz_data = load_template_json("quiz_questions.json")

# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘


def log_user_action(user_id, username, action, details, output, metadata=None):
    """Logs user actions into the database."""
    timestamp = datetime.now(timezone.utc).isoformat()

    # Serialize metadata to JSON string if it's not None
    if metadata is not None:
        metadata_json = json.dumps(metadata)
    else:
        metadata_json = None

    data = pd.DataFrame(
        [
            {
                "id": None,
                "timestamp": timestamp,
                "user_id": user_id,
                "username": username,
                "action": action,
                "details": details,
                "output": output,
                "metadata": metadata_json,
            }
        ]
    )
    pop(data, "user_actions")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and provides welcome and housekeeping rules."""
    user = update.effective_user

    # Clear user data at the start of the conversation
    context.user_data.clear()

    log_user_action(user.id, user.username, "start", "User started the bot", "Welcome message sent")

    keyboard = [[InlineKeyboardButton("Agree ✅", callback_data="agree")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_rules_msg, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return "DREAM_PROMPT"


async def dream_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts the user for their dream after acknowledgment."""
    query = update.callback_query
    user = query.from_user

    log_user_action(
        user.id,
        user.username,
        "acknowledge_rules",
        "User acknowledged the rules",
        "Dream prompt sent",
    )
    await query.answer()
    await query.edit_message_text("Let's go.")

    dream_message = (
        "An empire of $REPLY guyz can change the world and make NoM dreams come true...\n"
        "What's your dream? 🌟\n"
        "_Note: This will remain anonymous and be worked towards by the reply guyz..._"
    )
    await query.message.reply_text(dream_message, parse_mode="Markdown")
    return "COLLECT_DREAM"


async def collect_dream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's dream submission."""
    user = update.effective_user
    user_dream = update.message.text

    bot_response = "Got it. Now introducing, memetic reinforcement..."
    log_user_action(
        user.id,
        user.username,
        "dream_shared",
        "User shared their dream",
        user_dream,
    )

    await update.message.reply_text(bot_response)

    # Start the quiz by asking the first question
    return await ask_quiz_question(update, context, question_index=0)


async def ask_quiz_question(
    update: Update, context: ContextTypes.DEFAULT_TYPE, question_index: int
):
    """Displays a quiz question dynamically."""
    chat_id = update.effective_chat.id

    # Get the question from the quiz data
    try:
        question_data = quiz_data["quiz"][question_index]
    except IndexError:
        # No more questions
        await context.bot.send_message(
            chat_id=chat_id,
            text="Thank you for completing the quiz! You're all set to start your journey! 🚀",
        )
        return ConversationHandler.END

    question_text = question_data["question_text"]
    options = question_data["options"]

    # Build the keyboard dynamically
    keyboard = [
        [InlineKeyboardButton(option["text"], callback_data=str(option["alien_race_id"]))]
        for option in options
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Save the current question index in the context
    context.user_data["current_question_index"] = question_index

    # If this is the first question, send the quiz intro message
    if question_index == 0:
        await context.bot.send_message(chat_id=chat_id, text=quiz_intro_msg, parse_mode="Markdown")

    await context.bot.send_message(chat_id=chat_id, text=question_text, reply_markup=reply_markup)
    return "QUIZ_QUESTION"


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles answers to the quiz questions."""
    query = update.callback_query
    user = query.from_user
    alien_race_id = int(query.data)

    # Get the current question index
    question_index = context.user_data.get("current_question_index", 0)

    # Initialize quiz_answers if not already done
    if "quiz_answers" not in context.user_data:
        context.user_data["quiz_answers"] = []

    # Store the answer
    context.user_data["quiz_answers"].append(alien_race_id)

    # Fetch alien race details
    alien_race = next(
        (r for r in alien_races_data["alien_races"] if r["id"] == alien_race_id), None
    )
    if alien_race:
        race_name = alien_race["name"]
        race_emoji = alien_race["emoji"]
        # Map question index to the attribute
        question_attributes = {
            0: "communication_style",
            1: "work_style",
            2: "conflict_resolution",
            3: "personality_impression",
        }
        attribute_name = question_attributes.get(question_index)
        attribute_value = alien_race.get(attribute_name, "")
        response_text = (
            f"This suggests you are suited to the {race_emoji} *{race_name}*.\n_{attribute_value}_"
        )
    else:
        race_name = "Unknown"
        response_text = "You have chosen an unknown alien race."

    # Log the individual quiz answer with simplified details
    log_user_action(
        user.id,
        user.username,
        "quiz_answer",
        f"Question {question_index + 1}: Suggested alien race",
        race_name,
    )

    await query.answer()
    await query.edit_message_text(response_text, parse_mode="Markdown")

    # Proceed to the next question
    next_question_index = question_index + 1

    # Check if there are more questions
    if next_question_index < len(quiz_data["quiz"]):
        # Update the current question index
        context.user_data["current_question_index"] = next_question_index
        # Ask the next question
        return await ask_quiz_question(update, context, question_index=next_question_index)
    else:
        # All questions answered
        # Determine the most matched alien race
        await determine_matched_alien_race(update, context)
        return ConversationHandler.END


async def determine_matched_alien_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Determines which alien race the user matched with the most and logs it."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    answers = context.user_data["quiz_answers"]

    # Count the frequency of each alien race ID
    answer_counts = Counter(answers)
    max_count = max(answer_counts.values())
    # Get all alien_race_ids with the max count
    candidates = [
        alien_race_id for alien_race_id, count in answer_counts.items() if count == max_count
    ]
    # Find the first occurrence in answers among the candidates
    most_common_race_id = None
    for alien_race_id in answers:
        if alien_race_id in candidates:
            most_common_race_id = alien_race_id
            break

    # Fetch the details of the most matched alien race
    alien_race = next(
        (r for r in alien_races_data["alien_races"] if r["id"] == most_common_race_id), None
    )
    if alien_race:
        race_name = alien_race["name"]
        race_emoji = alien_race["emoji"]
        race_tagline = alien_race["tagline"]
        final_message = f"You are suited to the {race_emoji} *{race_name}*.\n_{race_tagline}_"
    else:
        race_name = "Unknown"
        final_message = "You've been matched with an unknown alien race."

    # Log the final matched alien race with simplified details
    log_user_action(
        user.id,
        user.username,
        "alien_race",
        "Selected alien race",
        race_name,
    )

    # Send the final message to the user
    await context.bot.send_message(chat_id=chat_id, text=final_message, parse_mode="Markdown")
    await context.bot.send_message(
        chat_id=chat_id,
        text="Thank you for completing the quiz! You're all set to start your journey! 🚀",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the current conversation."""
    user = update.effective_user
    log_user_action(
        user.id,
        user.username,
        "conversation_cancelled",
        "User cancelled the conversation",
        "Cancelled",
    )

    await update.message.reply_text("Conversation cancelled. You can restart anytime with /start.")
    return ConversationHandler.END
