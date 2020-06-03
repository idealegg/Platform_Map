#!/usr/bin/ksh

# Check if there is collecting process
pids=`ps -o pid,cmd -A|grep 'python runCollect.py'|grep -v grep|awk '{print $1}'`
if [ ! -z "$pids" ]
then
    echo $pids|xargs kill
else
    echo "Collecting process is not running!"
    exit 1
fi

wait_seconds=5
stopped=0

while [ ${wait_seconds} -gt 0 ] 
do
    ps -o pid,cmd -A|grep 'python runCollect.py'|grep -v grep > /dev/null
    if [ $? -ne 0 ]
    then
      stopped=1
      break
    fi

    sleep 1
    wait_seconds=$((wait_seconds-1))
done

if [ ${stopped} -eq 0 ]
then
    ps -o pid,cmd -A|grep 'python runCollect.py'|grep -v grep|awk '{print $1}'|xargs kill -9
fi

echo "Successfully!"
