#!/data/data/com.termux/files/usr/bin/bash
# Richtet die Frame-Diashow in der App "Termux" auf dem Android-Handy ein.
set -e
echo "1/4: Programme installieren ..."
pkg update -y
pkg install -y python python-pillow git

echo "2/4: Python-Pakete installieren ..."
if ! pip install flask samsungtvws; then
  echo "Zweiter Versuch mit Compiler ..."
  pkg install -y clang
  pip install flask samsungtvws
fi

echo "3/4: Zugriff auf die Handy-Fotos erlauben ..."
echo ">>> Gleich fragt Android nach einer Berechtigung: bitte ERLAUBEN <<<"
termux-setup-storage || true
sleep 5
mkdir -p /storage/emulated/0/Pictures/Frame || true

echo "4/4: Startbefehl einrichten ..."
ORDNER="$(cd "$(dirname "$0")" && pwd)"
grep -q "alias diashow=" ~/.bashrc 2>/dev/null || \
  echo "alias diashow='bash $ORDNER/handy-starten.sh'" >> ~/.bashrc

echo ""
echo "======================================================"
echo " Fertig! Termux einmal schliessen und neu oeffnen,"
echo " dann einfach eintippen:   diashow"
echo "======================================================"
