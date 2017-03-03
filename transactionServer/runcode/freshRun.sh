#!/bin/bash

if [ "$1" != "" ]; then
    killall python

    # need to also reset the rabbitMQ queues

    python runScript.py $1
else
    echo "need workload file to run"
    echo "example:   ./freshRun.sh workload.txt"
fi