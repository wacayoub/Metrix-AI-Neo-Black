# Metrix Neo AI — independent OpenATV plugin (v0.4.0)

A **separate Enigma2 plugin**, not a replacement for the official MetrixHD skin.
It controls the installed MyMetrixLite-generated *appearance* with reversible
color and font overlays. It never changes service lists, HDMI/4K video mode,
EPG data, or Enigma2 core files.

## Scope and limits

- Tested in an isolated Python/XML harness, **not yet tested on the actual Vu+ Zero 4K**.
- For Vu+ Zero 4K, OpenATV 8.0.1, primary skin `MetrixHD/skin.MySkin.xml`, FHD UI.
- Three themes: **Neo Black, Neo Blue, Neo Violet**; anti-glare semi-opaque
  panels, cyan/teal progress bars, Raleway titles where available and native
  gradient color values for *light* 3D-like shading.
- **No native 3840x2160 OSD claim**: HDMI can remain 2160p50 independently.
- Native MyMetrixLite remains present; if the user runs *Apply Changes* there,
  it regenerates its own XML. The separate plugin will detect the change and
  refuse destructive restoration until the user reviews it.
- The first install replaces only the legacy `# metrix-neo-auto-update` cron
  entry to avoid parallel color modifications. It saves a copy of the old
  crontab, preserves unrelated jobs, and leaves older updater files/backups in place.

## First installation, no IPK

Run on the receiver, via SSH:

```sh
wget -qO /tmp/metrix-neo-plugin.sh https://raw.githubusercontent.com/wacayoub/Metrix-AI-Neo-Black/main/neo-plugin/install-neo-plugin.sh && sh /tmp/metrix-neo-plugin.sh
```

Restart only **Enigma2 GUI** through OpenATV, then open Plugins > Metrix Neo AI.
Select a profile, press **GREEN** to apply, **YELLOW** to restore and **BLUE**
for online updates. The plugin asks before GUI restart and saves the original
XML/config metadata in `/etc/enigma2/MetrixNeoAI/`.

## Future updates

```sh
python3 /usr/lib/enigma2/python/Plugins/Extensions/MetrixNeoAI/neo_update.py check
python3 /usr/lib/enigma2/python/Plugins/Extensions/MetrixNeoAI/neo_update.py update
python3 /usr/lib/enigma2/python/Plugins/Extensions/MetrixNeoAI/neo_update.py rollback
```

A daily cron at **12:37 receiver time** attempts installation only if
`/proc/stb/power/standby` exactly confirms standby (`1`). No GUI restart is
performed automatically; updated plugin code takes effect after the next
GUI restart. The update is verified using SHA-256 from `manifest.json`.

## Compatibility note

The previously published V3 CLI updater (`/home/root/metrix_neo_updater.py`)
is a distinct legacy path and is not required for this new plugin. The new
installer disables its marked cron schedule automatically. If there was an
unmarked custom schedule, it can be disabled separately with:

```sh
python3 /home/root/metrix_neo_updater.py auto-off
```

The old script and backups remain available unless explicitly removed.