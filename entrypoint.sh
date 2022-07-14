#!/bin/bash

echo "Starting Marsbots Launcher..."

if [[ -n $REQUIREMENTS_FILE ]]; then
    echo "Installing requirements..."
    pip install -r $REQUIREMENTS_FILE
fi

if [[ -n $PM2_CONFIG_PATH ]]; then
    pm2 start $PM2_CONFIG_PATH
fi

sleep infinity
