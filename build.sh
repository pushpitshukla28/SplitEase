#!/usr/bin/env bash
# Render runs this script during every deploy

set -o errexit   # exit on any error

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
