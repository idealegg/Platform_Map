#!/usr/bin/ksh

mv db.sqlite3 db.sqlite3`date +%y%m%d%H%M%S`
python manage.py makemigrations
python manage.py migrate


./start_collect.sh
