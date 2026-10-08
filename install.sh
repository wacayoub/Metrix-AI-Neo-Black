#!/bin/sh
# One-time installer: subsequent updates are fetched by metrix-neo.
set -eu
BASE='https://raw.githubusercontent.com/wacayoub/Metrix-AI-Neo-Black/main'
TARGET='/home/root/metrix_neo_updater.py'
command -v python3 >/dev/null 2>&1 || { echo 'Python 3 missing'; exit 1; }
[ -f /etc/image-version ] || { echo 'OpenATV image not detected'; exit 1; }
grep -q '^box_type=vuzero4k$' /etc/image-version || { echo 'Not Vu+ Zero 4K'; exit 1; }
grep -q '^version=8.0.1$' /etc/image-version || { echo 'Not OpenATV 8.0.1'; exit 1; }
[ -f /etc/enigma2/settings ] || { echo 'Missing enigma2 settings'; exit 1; }
mkdir -p /home/root/.metrix-neo
if [ -f "$TARGET" ]; then cp "$TARGET" "$TARGET.backup"; fi
wget -q -O "$TARGET.tmp" "$BASE/metrix_neo_updater.py"
python3 -m py_compile "$TARGET.tmp" || { rm -f "$TARGET.tmp"; exit 1; }
mv -f "$TARGET.tmp" "$TARGET"
chmod 755 "$TARGET"
python3 "$TARGET" status
if ! python3 "$TARGET" auto-on; then
    echo "WARNING: daily cron could not be configured; use python3 $TARGET auto-on later."
fi
printf '\nInstalled. Commands: python3 %s check | update | rollback | status\n' "$TARGET"
