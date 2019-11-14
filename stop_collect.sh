#!/usr/bin/ksh

# Check if there is collecting process
pids=`ps -o pid,cmd -A|grep 'python runCollect.py'|grep -v grep|awk '{print $1}'`
if [ ! -z "$pids" ]
then
    echo $pids|xargs kill -9
else
    echo "Collecting process is not running!"
    exit 1
fi

echo "Successfully!"
