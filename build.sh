#!/usr/bin/env bash
set -o errexit

cd lumina
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py check --deploy