# Metrix AI Neo Black — OpenATV 8.0.1

Color-only MetrixHD/MyMetrixLite refinement for Vu+ Zero 4K.

- **Keeps** existing screen layouts, bouquets, IPTV plugins, picons, Arabic font fallback, HDMI output mode and FHD UI resolution.
- Applies selected black/navy/royal-blue palette with reversible settings and generated XML modifications.
- Checks for new releases online through an HTTPS `latest.json` manifest and **verifies SHA-256** of downloaded release scripts before use.
- Keeps local scripts for rollback. Does not require a new IPK on every update.
- Automatic daily check at 12:15 local receiver time; **unattended apply only when `/proc/stb/power/standby` confirms standby**. Otherwise the update is downloaded and ready for manual application.

## One-time setup (only after files are published to this repository)

On your Vu+ Zero 4K over SSH:

```sh
wget -qO /tmp/metrix-neo-install.sh https://raw.githubusercontent.com/wacayoub/Metrix-AI-Neo-Black/main/install.sh
sh /tmp/metrix-neo-install.sh
```

This installs `/home/root/metrix_neo_updater.py`, then attempts to register the daily check. It does **not** apply a release during initial setup: run the next command when convenient.

## Commands

```sh
python3 /home/root/metrix_neo_updater.py check       # inspect current release
python3 /home/root/metrix_neo_updater.py update      # download, verify, apply
python3 /home/root/metrix_neo_updater.py status      # current state
python3 /home/root/metrix_neo_updater.py rollback    # restore prior appearance
python3 /home/root/metrix_neo_updater.py auto-on     # enable daily check
python3 /home/root/metrix_neo_updater.py auto-off    # disable daily check
```

Current initial release is **0.3.0** (V3). If it was already applied manually, the updater detects the existing V3 backup and enrolls it without repeating modifications.

## What is and isn't "automatic"

The updater checks/downloading each day after a successful cron setup. Replacing skin files and restarting Enigma2 **must not be done during active viewing**. For that reason, unattended installation only happens if the box reports standby. On images without a reliable standby indicator, run `update` manually when ready. This is deliberate, not a failed update.

## Release process

1. Put the tested update Python script in `releases/X.Y.Z/...py`.
2. Update `latest.json` with compatibility (`openatv-8.0.1`, `vuzero4k`), its version/path and the SHA-256 of exact bytes.
3. Do **not** publish a new release until `apply`, `restore`, XML parsing and rollback have been verified in a test environment.
4. Avoid unreviewed or third-party code in the release; the updater executes downloaded Python with root privileges.

## Safety limits

- This is **not** a true UHD / 3840×2160 OSD skin. HDMI 2160p50 remains as configured by OpenATV.
- The included V3 uses built-in MyMetrixLite colors and doesn't change Enigma2 core, decoder or renderer.
- No automatic cron trigger should be enabled without confirming the receiver has a functional crontab facility.
- MyMetrixLite "Apply changes" may regenerate the skin, so re-run `update` only after incrementing a release or handle it through manual color settings; updates do not silently overwrite local changes on the same version.
- SHA-256 is an integrity check against mismatched downloads, **not a cryptographic signature against a compromised GitHub account**.
