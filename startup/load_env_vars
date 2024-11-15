#!/bin/bash

# Load environment variables from the .env file
load_env_file_vars() {
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    else
        echo ".env file not found. Make sure it exists."
        exit 1
    fi
}

# Call the function to load environment variables
load_env_file_vars