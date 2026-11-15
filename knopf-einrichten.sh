#!/data/data/com.termux/files/usr/bin/bash
# Legt den Knopf "Diashow" fuer die App "Termux:Widget" an.
ORDNER="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/Diashow <<KNOPF
#!/data/data/com.termux/files/usr/bin/bash
bash "$ORDNER/handy-starten.sh"
KNOPF
chmod +x ~/.shortcuts/Diashow
echo ""
echo "Fertig! Jetzt auf dem Startbildschirm das Widget 'Termux:Widget' hinzufuegen"
echo "und darin 'Diashow' antippen."
