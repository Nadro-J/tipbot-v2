#!/bin/bash

pgrep python3 | grep -v $$ | xargs kill -9
python3 bot.py
