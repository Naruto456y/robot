#!/bin/bash
export PYTHONPATH=/home/pi/.local/lib/python3.11/site-packages:$PYTHONPATH
exec > /home/pi/logs/raspbot.log 2>&1
echo "=== Starting raspbot.pyc at $(date) ==="
python3 /home/pi/project_demo/raspbot/raspbot.pyc
