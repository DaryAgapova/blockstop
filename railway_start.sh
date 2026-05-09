#!/bin/bash
# Этот скрипт запускается при старте на Railway
python seed.py
exec gunicorn run:app --bind 0.0.0.0:$PORT
