#!/bin/bash

if [ "$1" != "" ]; then
    killall python

    python runScript.py
