#!/bin/bash

if [ -f "$ENV_PATH" ]; then
    echo "Activating environment from: $ENV_PATH"
    # Activate the virtual environment
    source "$ENV_PATH"
    echo "Environment activated. Python path: $(which python)"
else
    echo "Error: Environment activation script not found at $ENV_PATH"
    exit 1
fi
