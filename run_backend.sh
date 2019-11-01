#!/usr/bin/ksh

cd GetPlatformInfo
export PYTHONUNBUFFERED=1
export PYTHONPATH=/tmp/huangd/Platform_Map/GetPlatformInfo:/tmp/huangd/Platform_Map:.
python runCollect.py
