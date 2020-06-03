#!/usr/bin/ksh

WORK_DIR=`dirname $0`
WORK_DIR=`cd $WORK_DIR;pwd`
cd ${WORK_DIR}

mv db.sqlite3 db.sqlite3`date +%y%m%d%H%M%S`
python manage.py makemigrations
python manage.py migrate


./start_collect.sh
