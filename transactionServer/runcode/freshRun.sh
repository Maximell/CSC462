#!/bin/bash

if [ "$1" != "" ]; then
    killall python

    python runScript.py $1

fi