# -*- coding: utf-8 -*-
"""
Created
@author:
@links:
@description:
Contains functions to help generate consistent scripts.
"""

# ┌─────────┐
# │ Imports │
# └─────────┘

from datetime import datetime
from typing import List, Optional

# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘


def format_heading(heading: str) -> str:
    """
    Formats headings.
    :param heading: The heading text to format and print.
    :return: The formatted heading string.
    """
    if heading:  # Ensure heading is not empty or None
        formatted_heading = (
            f"# ┌{'─' * (len(heading) + 2)}┐\n"
            f"# │ {heading.capitalize()} │\n"
            f"# └{'─' * (len(heading) + 2)}┘"
        )
        print(formatted_heading)  # Print the formatted heading
        return formatted_heading  # Return the formatted heading
    return ""


def script_template_builder(titles: Optional[List[str]] = None) -> None:
    """
    Script template generator for the usual structure of python files.
    :param titles: Optionally define the required headings.
    :return: Print the script template to console and copy it to the clipboard.
    """
    if titles is None:
        titles = [
            "Imports",
            "Parameters",
            "Program Functions",
            "Load & Process Data",
            "Programs",
        ]

    template = f'''# -*- coding: utf-8 -*-
"""
Created {datetime.today().strftime('%d %B %Y')}
@author: 
@links:
@description:

"""
'''

    for t in titles:
        template += format_heading(t) + "\n"  # Concatenate and add a newline for each heading

    # Print the template to the console
    print(template)


if __name__ == "__main__":

    print("Hello, world")
