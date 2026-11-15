#!/data/data/com.termux/files/usr/bin/bash
# Startet die Frame-Diashow auf dem Handy und oeffnet die Seite im Browser.
cd "$(dirname "$0")"
URL=http://localhost:8080

# Laeuft das Programm schon? Dann nur die Seite oeffnen.
if python -c "import urllib.request;urllib.request.urlopen('$URL/status',timeout=2)" 2>/dev/null; then
  termux-open-url "$URL"
  exit 0
fi

termux-wake-lock 2>/dev/null || true   # verhindert, dass Android das Programm einschlaefert
export FRAME_BILDER="${FRAME_BILDER:-/storage/emulated/0/Pictures/Frame}"
(sleep 4; termux-open-url "$URL") &
echo "Diashow-Programm laeuft. Zum Beenden: CTRL-Taste + c"
python frame_diashow.py
termux-wake-unlock 2>/dev/null || true
