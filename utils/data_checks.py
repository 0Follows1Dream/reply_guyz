# -*- coding: utf-8 -*-
"""
Created 04 December 2024
@author:
@links:
@description:
"""
# ┌─────────┐
# │ Imports │
# └─────────┘

import re

# ┌────────────┐
# │ Parameters │
# └────────────┘
# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘

url = "https://xx.com/aalasady_/status/1863993644555882825"
url = "https://x.com/aalasady_/status/1863993644555882825?s=46&t=IOFZel46hzT0N_93kr8PLg"


def check_url(url):

    url = url.strip().rstrip("/")

    # Define the regex pattern for validation
    pattern = r"^(https?:\/\/)?(x\.com|twitter\.com|vxtwitter\.com|fixupx\.com)\/[a-zA-Z0-9_]+\/status\/\d+(\?.*)?$"

    # Match the URL against the pattern
    if re.match(pattern, url):
        return True
    return False


# ┌─────────────────────┐
# │ Load & process data │
# └─────────────────────┘
# ┌──────────┐
# │ Programs │
# └──────────┘
