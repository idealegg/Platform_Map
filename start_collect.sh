#!/usr/bin/ksh

WORK_DIR=`dirname $0`
WORK_DIR=`cd $WORK_DIR;pwd`
cd GetPlatformInfo
export PYTHONUNBUFFERED=1
export PYTHONPATH=${WORK_DIR}/GetPlatformInfo:${WORK_DIR}:.

# Check if there is collecting process
pids=`ps -o pid,cmd -A|grep 'python runCollect.py'|grep -v grep|awk '{print $1}'`
if [ ! -z "$pids" ]
then
    echo "Do you want to restart the collecting process?[Y/N][N]"
    read USER_INPUT_FLAG
    if [ -z "${USER_INPUT_FLAG}" -o "${USER_INPUT_FLAG:0:1}" == "N" -o "${USER_INPUT_FLAG:0:1}" == "n" ]
    then
        echo "Exit Operation!"
        exit 1
    fi

    echo $pids|xargs kill -9
fi

nohup python runCollect.py > /dev/null 2>&1 &

echo "Successfully!"
