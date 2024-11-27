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


# ┌────────────┐
# │ Parameters │
# └────────────┘

# put all these into the .env file or a config file
explorer_link = "https://zenonhub.io/explorer/token/zts1s69da8505vjrzjh8w2770v"
max_token_supply = 1272312723
alien_races = ["reptoidz", "meowz", "greyz", "avianz", "wuffz"]
number_of_races = len(alien_races)

daily_per_race = 12723
daily_total_supply = daily_per_race * number_of_races

# High Level Summary Stats
number_of_days_supply = max_token_supply / daily_total_supply
print(f"Total $REPLY supply: {max_token_supply}")
print(f"Explorer link: {explorer_link}")
print(f"Number of races: {number_of_races}")
print(f"Alien race names: {alien_races}")
print(f"Daily supply for each race: {daily_per_race}")
print(f"Daily supply for all races: {daily_total_supply}")
print(f"Number of years supply: {int(round(number_of_days_supply/365, 0))}")

# weighting multiplier
n_user_multiplier = 3


# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘
# ┌─────────────────────┐
# │ Load & process data │
# └─────────────────────┘
# ┌──────────┐
# │ Programs │
# └──────────┘
