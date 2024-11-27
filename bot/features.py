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

import pandas as pd
from telegram import Update
from telegram.ext import ContextTypes

from utils.db import db_query

# ┌────────────┐
# │ Parameters │
# └────────────┘


# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘

# /alien_races
# 1. see the information on each race (with the current reward rate)
# 2. select new race


async def alien_race_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /alien_race command and shows the list of users with their alien race."""
    # Query the alien_race_teams table
    alien_race_df = db_query("SELECT user_id, username, alien_race FROM alien_race_teams")

    if alien_race_df.empty:
        await update.message.reply_text("No users have been assigned to any alien races yet.")
        return

    # Get the most recent Twitter username for each user
    twitter_usernames_df = db_query(
        """
        SELECT user_id, output AS twitter_username
        FROM user_actions
        WHERE action = 'twitter_username'
        ORDER BY timestamp DESC
    """
    )

    # Keep only the most recent Twitter username per user
    twitter_usernames_df = twitter_usernames_df.drop_duplicates(subset="user_id", keep="first")

    # Merge alien_race_df with twitter_usernames_df on user_id
    merged_df = pd.merge(alien_race_df, twitter_usernames_df, on="user_id", how="left")

    # Group by alien_race
    grouped = merged_df.groupby("alien_race")

    message_lines = []

    for alien_race, group in grouped:
        alien_emoji = {
            "Reptoidz": "🦎",
            "Meowz": "😺",
            "Greyz": "👽",
            "Avianz": "🦅",
            "Wuffz": "🐕",
        }
        message_lines.append(f"Alien Race: {alien_race}{alien_emoji[alien_race]}")
        for idx, row in group.iterrows():
            username = row["username"] or "<>"
            twitter_username = row["twitter_username"] or "<>"
            message_lines.append(f" - Telegram: {username}, Twitter: @{twitter_username}")
        message_lines.append("")  # Add an empty line between alien races

    message_text = "\n".join(message_lines)

    # Send the message
    await update.message.reply_text(message_text)


# report_user
# report a user here

# leaderboard
# show the earning stats

# bot sending messages functions
# new replies (this can be the audit trail)
# reminder functions (automated)
# new joiner (user just joined race), alien race day, 100th_monkey_syndrome
# the bot needs to fire a message to all the people in each race on their day to remind them to


# ┌─────────────────────┐
# │ Load & process data │
# └─────────────────────┘


# ┌──────────┐
# │ Programs │
# └──────────┘
