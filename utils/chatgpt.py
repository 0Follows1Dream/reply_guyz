"""
Created
@author:
@links:
@description:
"""

# ┌─────────┐
# │ Imports │
# └─────────┘

import json

import tiktoken
from decouple import config
from openai import OpenAI

# ┌────────────┐
# │ Parameters │
# └────────────┘

client = OpenAI(api_key=config("CHATGPT_SECRETKEY_PROJECT"))

gpt_model_info = {
    "gpt-4o": {"context_tokens": 128000, "output_tokens": 16000, "token_price_per_million": 2.5},
    "gpt-4o-mini": {
        "context_tokens": 128000,
        "output_tokens": 16000,
        "token_price_$_per_million": 0.15,
    },
}


def check_n_tokens(input_text, gpt_model):
    encoding = tiktoken.encoding_for_model(gpt_model)
    return len(encoding.encode(input_text))


# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘


def extract(text, gpt_model="gpt-4o-mini"):
    functions = [
        {
            "name": "extractor",
            "description": "extracts",
            "parameters": {
                "type": "object",
                "properties": {
                    "property": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "description",
                    },
                },
                "required": [
                    "property",
                ],
            },
        }
    ]

    system_message = """
    You are an assistant that extracts

    **Important**:

    - 
    """

    user_message = """
    Extract property
    """

    n_tokens = check_n_tokens(input_text=user_message + system_message, gpt_model=gpt_model)

    if (
        n_tokens < gpt_model_info[gpt_model]["context_tokens"]
    ):  # Ensure it's within token limit for the model
        messages = [
            {"role": "system", "content": system_message.strip()},
            {"role": "user", "content": user_message.strip()},
        ]

        completion = client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            functions=functions,
            function_call={"name": "identify_urls"},
        )

        first_choice = completion.choices[0]
        message = first_choice.message

        if hasattr(message, "function_call") and message.function_call is not None:
            function_call = message.function_call
            arguments_str = function_call.arguments
            urls = json.loads(arguments_str)
            return urls
        else:
            print("No function_call found in the assistant's response.")
    else:
        print(f"Input tokens exceed the limit. Current token count: {n_tokens}")
