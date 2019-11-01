#!/usr/bin/ksh

export PYTHONPATH=/tmp/huangd/Platform_Map/Platform_Map:/tmp/huangd/Platform_Map:.
export DJANGO_SETTINGS_MODULE=Platform_Map.settings
export PYTHONUNBUFFERED=1
python manage.py runserver 0.0.0.0:8000

