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

import calendar
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from utils.db import db_query

# ┌────────────────────────┐
# │ High level information │
# └────────────────────────┘

explorer_link = "https://zenonhub.io/explorer/token/zts1s69da8505vjrzjh8w2770v"
max_token_supply = 1272312723
alien_races = ["reptoidz", "meowz", "greyz", "avianz", "wuffz"]
tweet_categories = [
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
number_of_races = len(alien_races)
weekly_distribution_per_race = 12723
min_n_tweets = 1

# Bonus parameters
daily_n_tweet_target = 5
n_tweet_multiplier_weekly = 3

all_categories_weekly_bonus_multiplier = 2

swarm_day_multiplier = 3.5
swarm_day_tweet_target = 10
swarm_days = [2, 4]  # Wednesday=2, Friday=4

# High Level Summary Stats
weekly_total_supply = weekly_distribution_per_race * number_of_races
number_of_weeks_supply = max_token_supply / weekly_total_supply
max_multiplier = (
    n_tweet_multiplier_weekly * swarm_day_multiplier * all_categories_weekly_bonus_multiplier
)

# Print summary stats (optional)
print(f"Total $REPLY supply: {max_token_supply}")
print(f"Explorer link: {explorer_link}")
print(f"Number of races: {number_of_races}")
print(f"Alien race names: {alien_races}")
print(f"Weekly supply for each race: {weekly_distribution_per_race}")
print(f"Weekly supply for all races: {weekly_total_supply}")
print(f"Number of years supply: {int(round(number_of_weeks_supply/52, 0))}")
print(
    f"Daily tweet target {daily_n_tweet_target} for full week multiplier: {n_tweet_multiplier_weekly}"
)
print(
    f"Swarm days {[calendar.day_name[day] for day in swarm_days]} {swarm_day_tweet_target} tweet target multiplier: {swarm_day_multiplier}"
)
print(f"All categories weekly multiplier: {all_categories_weekly_bonus_multiplier}")
print(f"Max weekly multiplier: {max_multiplier}")
print(
    f"Number of years supply if all users hit max multiplier every week: {round(number_of_weeks_supply/52/max_multiplier, 2)}"
)


def calculate_distribution():
    # ┌───────────────────┐
    # │ Data Preparation  │
    # └───────────────────┘
    # Set up the date range for the current week
    today_date = datetime.utcnow()
    start_of_week = today_date - timedelta(days=today_date.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week_str = start_of_week.strftime("%Y-%m-%d %H:%M:%S")
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    end_of_week_str = end_of_week.strftime("%Y-%m-%d %H:%M:%S")

    # Load data from the database
    alien_teams = db_query("SELECT user_id, alien_race FROM alien_race_teams")

    daily_tweets = db_query(  # nosec
        f"""SELECT * FROM daily_tweet_counts WHERE timestamp >= '{start_of_week_str}' AND timestamp <= '{end_of_week_str}';"""  # nosec
    )  # nosec

    daily_tweets["timestamp"] = pd.to_datetime(daily_tweets["timestamp"])
    daily_tweets["day_of_week"] = daily_tweets["timestamp"].dt.dayofweek  # Monday=0, Sunday=6
    daily_tweets = daily_tweets.merge(alien_teams, on="user_id", how="left")

    weekly_categories = db_query(  # nosec
        f"""SELECT * FROM weekly_categories WHERE week_start_date >= '{start_of_week_str}' AND week_start_date <= '{end_of_week_str}';"""  # nosec
    )  # nosec

    # Ensure 'alien_race' is not missing
    daily_tweets = daily_tweets.dropna(subset=["alien_race"])

    # ┌─────────────────────────┐
    # │ Condition 1: 5 Tweets/Day │
    # └─────────────────────────┘
    # Create all combinations of user_id and day_of_week
    user_ids = daily_tweets["user_id"].unique()
    days_of_week = [0, 1, 2, 3, 4, 5, 6]  # Monday=0, Sunday=6

    index = pd.MultiIndex.from_product([user_ids, days_of_week], names=["user_id", "day_of_week"])
    user_day_df = pd.DataFrame(index=index).reset_index()

    # Get daily total tweet counts per user per day
    daily_tweet_counts = (
        daily_tweets.groupby(["user_id", "day_of_week"])["tweet_count"].sum().reset_index()
    )

    # Merge with user_day_df
    user_day_df = user_day_df.merge(daily_tweet_counts, on=["user_id", "day_of_week"], how="left")
    user_day_df["tweet_count"] = user_day_df["tweet_count"].fillna(0)

    # Check if tweet_count >= daily_n_tweet_target
    user_day_df["met_daily_n_tweet"] = user_day_df["tweet_count"] >= daily_n_tweet_target

    # For each user, check if they met the condition for all days in the week
    user_daily_n_tweets = user_day_df.groupby("user_id")["met_daily_n_tweet"].all().reset_index()
    user_daily_n_tweets.rename(
        columns={"met_daily_n_tweet": "met_daily_n_tweet_target"}, inplace=True
    )

    # ┌───────────────────────────┐
    # │ Condition 2: All Categories │
    # └───────────────────────────┘
    # Get per user the set of categories they have tweeted in
    user_categories = weekly_categories.groupby("user_id")["category"].apply(set).reset_index()
    tweet_categories_set = set(tweet_categories)
    user_categories["met_all_categories"] = user_categories["category"].apply(
        lambda x: tweet_categories_set.issubset(x)
    )

    # ┌─────────────────────────────┐
    # │ Condition 3: Swarm Day Tweets │
    # └─────────────────────────────┘
    # Get swarm day tweets
    swarm_day_tweets = daily_tweets[daily_tweets["day_of_week"].isin(swarm_days)]
    # Sum tweets per user on swarm days
    swarm_tweet_counts = swarm_day_tweets.groupby("user_id")["tweet_count"].sum().reset_index()
    # Check if tweet_count >= swarm_day_tweet_target
    swarm_tweet_counts["met_swarm_day_target"] = (
        swarm_tweet_counts["tweet_count"] >= swarm_day_tweet_target
    )

    # Ensure all users are included
    user_swarm_targets = pd.DataFrame({"user_id": user_ids})
    user_swarm_targets = user_swarm_targets.merge(
        swarm_tweet_counts[["user_id", "met_swarm_day_target"]], on="user_id", how="left"
    )
    user_swarm_targets["met_swarm_day_target"] = user_swarm_targets["met_swarm_day_target"].fillna(
        False
    )

    # ┌───────────────────────────┐
    # │ Merge Conditions and Data │
    # └───────────────────────────┘
    # Get users and their alien races
    users_per_race = daily_tweets[["user_id", "alien_race"]].drop_duplicates()

    # Calculate the number of unique users per alien race
    users_per_race_count = users_per_race.groupby("alien_race")["user_id"].nunique().reset_index()
    users_per_race_count.rename(columns={"user_id": "num_users"}, inplace=True)

    # Merge the number of users back into the per-user DataFrame
    users_per_race = users_per_race.merge(users_per_race_count, on="alien_race", how="left")

    # Merge conditions into users_per_race
    user_conditions = users_per_race.merge(
        user_daily_n_tweets[["user_id", "met_daily_n_tweet_target"]], on="user_id", how="left"
    )
    user_conditions = user_conditions.merge(
        user_categories[["user_id", "met_all_categories"]], on="user_id", how="left"
    )
    user_conditions = user_conditions.merge(
        user_swarm_targets[["user_id", "met_swarm_day_target"]], on="user_id", how="left"
    )

    # Fill NaN with False
    user_conditions["met_daily_n_tweet_target"] = user_conditions[
        "met_daily_n_tweet_target"
    ].fillna(False)
    user_conditions["met_all_categories"] = user_conditions["met_all_categories"].fillna(False)
    user_conditions["met_swarm_day_target"] = user_conditions["met_swarm_day_target"].fillna(False)

    # ┌─────────────────────┐
    # │ Assign Multipliers  │
    # └─────────────────────┘
    # Apply multipliers based on conditions
    user_conditions["multiplier_daily_n_tweets"] = np.where(
        user_conditions["met_daily_n_tweet_target"], n_tweet_multiplier_weekly, 1
    )
    user_conditions["multiplier_all_categories"] = np.where(
        user_conditions["met_all_categories"], all_categories_weekly_bonus_multiplier, 1
    )
    user_conditions["multiplier_swarm_day"] = np.where(
        user_conditions["met_swarm_day_target"], swarm_day_multiplier, 1
    )

    # ┌────────────────────────────┐
    # │ Calculate Final Earnings   │
    # └────────────────────────────┘
    # Calculate the baseline earning per user
    user_conditions["baseline_earning"] = (
        weekly_distribution_per_race / user_conditions["num_users"]
    )

    # Calculate final earning by applying all multipliers
    user_conditions["final_earning"] = (
        user_conditions["baseline_earning"]
        * user_conditions["multiplier_daily_n_tweets"]
        * user_conditions["multiplier_all_categories"]
        * user_conditions["multiplier_swarm_day"]
    )

    # Display the final summary with individual multipliers
    print(
        user_conditions[
            [
                "user_id",
                "alien_race",
                "baseline_earning",
                "met_daily_n_tweet_target",
                "multiplier_daily_n_tweets",
                "met_all_categories",
                "multiplier_all_categories",
                "met_swarm_day_target",
                "multiplier_swarm_day",
                "final_earning",
            ]
        ]
    )


if __name__ == "__main__":

    calculate_distribution()
