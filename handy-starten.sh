#!/data/data/com.termux/files/usr/bin/bash
# Startet die Frame-Diashow auf dem Handy und oeffnet die Seite im Browser.
cd "$(dirname "$0")"
termux-wake-lock 2>/dev/null || true   # verhindert, dass Android das Programm einschlaefert
export FRAME_BILDER="${FRAME_BILDER:-/storage/emulated/0/Pictures/Frame}"
(sleep 4; termux-open-url http://localhost:8080) &
echo "Diashow-Programm laeuft. Zum Beenden: Strg+C (in Termux: CTRL-Taste + c)"
python frame_diashow.py
termux-wake-unlock 2>/dev/null || true
