# -*- coding: utf-8 -*-
"""
Created 24 November 2024
@author:
@links:
@description:
"""
# ┌─────────┐
# │ Imports │
# └─────────┘

from utils.db import db_query

# ┌────────────┐
# │ Parameters │
# └────────────┘

# ┌────────────────────────┐
# │ High level information │
# └────────────────────────┘

explorer_link = "https://zenonhub.io/explorer/token/zts1s69da8505vjrzjh8w2770v"  # explorer ZTS link
max_token_supply = 1272312723  # max $reply supply
alien_races = ["reptoidz", "meowz", "greyz", "avianz", "wuffz"]  # alien race names
number_of_races = len(alien_races)  # 5 races
weekly_distribution_per_race = 12723  # 12723 $reply baseline to each race
weekly_total_supply = (
    weekly_distribution_per_race * number_of_races
)  # baseline 63615 $reply per day across all races
min_n_tweets = 1  # if a user sends 1 tweet per day they are able to get the share of baseline weekly distribution

# ┌──────────────────┐
# │ Bonus parameters │
# └──────────────────┘

# tweet target
daily_n_tweet_target = 5  # daily number of tweets target
n_tweet_multiplier_weekly = 7  # compound daily if met -- might delete and make it stricter
n_tweet_multiplier_daily_accrual = n_tweet_multiplier_weekly ** (
    1 / 7
)  # this metric can accrue daily if you miss a 5 day tweet it's ok

# categories target
all_categories_weekly_bonus_multiplier = 2

# swarm day multiplier
swarm_day_multiplier = 5
swarm_day_tweet_target = 10
swarm_days = ["Wed", "Fri"]


# to track the challenges progress i need tables that

# daily 5 tweet count bonus
# [1] counts between midnight to 23:59:59 UTC each day
# number of threads + replies if > 5 bonus

# weekly topics bonus
# [2] counts between midnight monday UTC and 23:59:59 UTC sunday
# the unique categories posted in

# swarm days bonus
# [3] for the swarm day it can simply take from [2] and check if 5 completed on a swarm day a second trigger to log in another db


# High Level Summary Stats
number_of_weeks_supply = max_token_supply / weekly_total_supply
max_multiplier = (
    n_tweet_multiplier_weekly * swarm_day_multiplier * all_categories_weekly_bonus_multiplier
)
print(f"Total $REPLY supply: {max_token_supply}")
print(f"Explorer link: {explorer_link}")
print(f"Number of races: {number_of_races}")
print(f"Alien race names: {alien_races}")
print(f"Weekly supply for each race: {weekly_distribution_per_race}")
print(f"Weekly supply for all races: {weekly_total_supply}")
print(f"Number of years supply: {int(round(number_of_weeks_supply/52, 0))}")
print(f"Max multiplier: {max_multiplier}")
print(
    f"Number of years supply if all users hit max multiplier every week: {round(number_of_weeks_supply/52/max_multiplier, 2)}"
)


# clean the dataset to ensure the only tweets that are considered are the ones that are from those tied to handle
tweets = db_query("select * from threads")

alien_info = db_query(
    "select timestamp, user_id, action, output from user_actions where action in ('alien_race', 'twitter_username');"
).pivot(index=["timestamp", "user_id"], columns="action")

# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘
# ┌─────────────────────┐
# │ Load & process data │
# └─────────────────────┘
# ┌──────────┐
# │ Programs │
# └──────────┘
