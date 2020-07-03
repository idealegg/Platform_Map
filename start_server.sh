#!/usr/bin/ksh

WORK_DIR=`dirname $0`
WORK_DIR=`cd $WORK_DIR;pwd`
export PYTHONPATH=${WORK_DIR}/Platform_Map:${WORK_DIR}:.
export DJANGO_SETTINGS_MODULE=Platform_Map.settings
export PYTHONUNBUFFERED=1
export PLATFORM_MAP_SERVER=

cd ${WORK_DIR}

host=`hostname`
if [  "${host:2:2}" == "cd" ]
then
  export PLAT_FORM_SITE=CD
fi

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
