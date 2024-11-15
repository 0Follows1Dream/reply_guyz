#!/bin/bash

# Tools > Terminal (unclick activate virtual environment)
# echo $SHELL
# Shell path: /bin/zsh -l

# Check if the activation script exists
if [ -f "$ENV_PATH" ]; then
    echo "Activating virtual environment..."
    source "$ENV_PATH"
    echo "Virtual environment activated: $(which python)"
else
    echo "Error: Virtual environment activation script not found at $ENV_PATH"
    exit 1
fi

# Start PyCharm in the background and silence the logs
echo "Starting PyCharm..."
"$PYCHARM_PATH" > /dev/null 2>&1 &

# Notify the user
echo "PyCharm launched with virtual environment activated."
