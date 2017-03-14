#!/bin/bash

if [ "$1" == "" ]; then
    killall python
    python runScript.py
else
    echo "no workload file to needed"
fi