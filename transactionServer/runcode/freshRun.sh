#!/bin/bash

if [ "$1" != "" ]; then
    killall python

    rabbitmqctl stop_app
    rabbitmqctl reset
    rabbitmqctl start_app

    python runScript.py $1
else
    echo "need workload file to run"
    echo "example:   ./freshRun.sh workload.txt"
fi