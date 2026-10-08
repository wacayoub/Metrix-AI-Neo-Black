#!/bin/sh
# One-time install; subsequent upgrades work from the plugin Blue button or cron.
set -eu
URL='https://raw.githubusercontent.com/wacayoub/Metrix-AI-Neo-Black/main/neo-plugin/bootstrap.py'
command -v python3 >/dev/null 2>&1 || { echo 'Python3 required'; exit 1; }
wget -q -O /tmp/metrixneo-bootstrap.py "$URL"
python3 /tmp/metrixneo-bootstrap.py
printf '\nRestart the Enigma2 GUI to open Plugins > Metrix Neo AI.\n'