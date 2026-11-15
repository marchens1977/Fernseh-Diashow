#!/bin/bash
# Richtet die Frame-Diashow auf dem Raspberry Pi ein und startet sie automatisch.
set -e
cd "$(dirname "$0")"
ORDNER="$(pwd)"
BENUTZER="$(whoami)"

echo "1/3: Benoetigte Programme installieren ..."
sudo apt-get update -q
sudo apt-get install -y python3-venv python3-pip libjpeg-dev zlib1g-dev

echo "2/3: Python-Pakete installieren (dauert ein paar Minuten) ..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt

echo "3/3: Automatischen Start einrichten ..."
sudo tee /etc/systemd/system/frame-diashow.service > /dev/null <<DIENST
[Unit]
Description=Frame-Diashow fuer Samsung The Frame
After=network-online.target
Wants=network-online.target

[Service]
User=$BENUTZER
WorkingDirectory=$ORDNER
ExecStart=$ORDNER/venv/bin/python $ORDNER/frame_diashow.py
Restart=always

[Install]
WantedBy=multi-user.target
DIENST
sudo systemctl daemon-reload
sudo systemctl enable --now frame-diashow
sudo systemctl restart frame-diashow

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "======================================================"
echo " Fertig! Oeffne jetzt auf dem Handy im Browser:"
echo "   http://$IP:8080"
echo "======================================================"
