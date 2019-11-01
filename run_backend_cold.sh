#!/usr/bin/ksh

mv db.sqlite3 db.sqlite3`date +%y%m%d%H%M%S`
python manage.py makemigrations
python manage.py migrate

cd GetPlatformInfo
export PYTHONUNBUFFERED=1
export PYTHONPATH=/tmp/huangd/Platform_Map/GetPlatformInfo:/tmp/huangd/Platform_Map:.
python runCollect.py
