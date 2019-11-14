#!/usr/bin/ksh

# Check if there are Web servers
pids=`ps -o pid,cmd -A|grep 'python manage.py runserver'|grep -v grep|awk '{print $1}'`
if [ ! -z "$pids" ]
then
    echo $pids|xargs kill -9
else
    echo "Web server is not running!"
    exit 1
fi

echo "Successfully!"
