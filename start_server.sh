#!/usr/bin/ksh

usage()
{
  echo "Usage: `basename $0` [JV|CD]"
  echo "       Default: JV"
}

if [ $# -gt 1 ]
then
  usage
  exit 1
fi

PLAT_FORM_SITE=JV

if [ $# -eq 1 ]
then
  if [ "$1" == "CD" -o "$1" == "JV" ]
  then
    PLAT_FORM_SITE=$1
  else
    usage
    exit 2
  fi
fi

WORK_DIR=`dirname $0`
WORK_DIR=`cd $WORK_DIR;pwd`
export PYTHONPATH=${WORK_DIR}/Platform_Map:${WORK_DIR}:.
export DJANGO_SETTINGS_MODULE=Platform_Map.settings
export PYTHONUNBUFFERED=1
export PLATFORM_MAP_SERVER=
export PLAT_FORM_SITE

# Check if there are Web servers
pids=`ps -o pid,cmd -A|grep 'python manage.py runserver'|grep -v grep|awk '{print $1}'`
if [ ! -z "$pids" ]
then
    echo "Do you want to restart the web server?[Y/N][N]"
    read USER_INPUT_FLAG
    if [ -z "${USER_INPUT_FLAG}" -o "${USER_INPUT_FLAG:0:1}" == "N" -o "${USER_INPUT_FLAG:0:1}" == "n" ]
    then
        echo "Exit Operation!"
        exit 1
    fi

    echo $pids|xargs kill -9
fi

nohup python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &

echo "Successfully!"
