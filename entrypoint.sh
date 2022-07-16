#!/bin/bash

echo "Starting Marsbots Launcher..."

if [[ -n $SUPERVISOR_CONFIG_PATH ]]; then
    echo "Using supervisor config from $SUPERVISOR_CONFIG_PATH"
    supervisord -c $SUPERVISOR_CONFIG_PATH
fi

sleep infinity
