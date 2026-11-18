# Projekt-Tagebuch: Fernseh-Diashow

## 1. Worum es geht
Ein kleines Programm, das Fotos aus einem Ordner als **Diashow im Kunst-Modus** eines
**Samsung „The Frame“**-Fernsehers zeigt. Bedient wird es über eine Webseite im Handy-Browser.

- **Wo läuft es?** Nicht online im Internet, sondern lokal:
  - **Hauptweg:** direkt auf dem Samsung-Smartphone in der App **Termux** (aus F-Droid).
    Seite: `http://localhost:8080`. Start über das Startbildschirm-Icon **„Diashow“** (Termux:Widget).
  - **Alternative:** auf dem Raspberry Pi 400 (`installieren.sh`, startet automatisch), Seite `http://<IP-des-Pi>:8080`.
- **Code:** GitHub-Projekt `marchens1977/Fernseh-Diashow`, Branch `main`.

### Technischer Aufbau (wichtige Dateien)
| Datei | Zweck |
|---|---|
| `frame_diashow.py` | Das ganze Programm: Webseite (Flask), Bildaufbereitung (Pillow), Verbindung zum TV (`samsungtvws`, Port 8002), Diashow im Hintergrund |
| `handy-einrichten.sh` | Einmalige Einrichtung in Termux (Pakete, Foto-Zugriff, Befehl `diashow`) |
| `handy-starten.sh` | Startet das Programm und öffnet die Seite (läuft es schon, nur Seite öffnen) |
| `knopf-einrichten.sh` | Legt `~/.shortcuts/Diashow` für das Termux:Widget-Icon an |
| `installieren.sh` | Einrichtung auf dem Raspberry Pi inkl. Autostart (systemd) |
| `README.md` | Anleitung für den Nutzer |
| `einstellungen.json`, `hochgeladen.json`, `variante.txt`, `tv-token.txt`, `.vorbereitet/` | Laufzeit-Dateien, nicht in Git |

## 2. Wichtige Regeln und Entscheidungen
- **Fotos werden nie verzerrt:** jedes Bild wird auf 3840×2160 (16:9) gesetzt, Ränder gefüllt
  (Standard: unscharfe Kopie des Fotos; wählbar: Schwarz/Weiß/Grau).
- **Original-Fotos werden nie gelöscht.** Der Knopf heißt „Ausblenden“ und nimmt ein Bild nur aus der Diashow.
- **Ordner-Auswahl** über einen eigenen Ordner-Browser auf der Seite (die Android-Dateiauswahl zeigt nur Google Fotos).
- Ändern sich Ordner, Ränder oder Passepartout, werden die alten Bilder vom TV gelöscht und neu hochgeladen.
- **IP des Fernsehers:** wird gespeichert; ist er dort nicht erreichbar, sucht das Programm ihn im WLAN
  (Abfrage `http://<ip>:8001/api/v2/`, `FrameTVSupport`). Empfehlung: feste IP in der FritzBox.
- Beim ersten Verbinden muss am Fernseher **„Zulassen“** gewählt werden (Token in `tv-token.txt`).
- Option „Fernseher spielt die Diashow selbst ab“ (Kategorie „Meine Fotos“, `MY-C0002`): Handy kann danach aus sein.
- Zeit pro Bild wird in **Minuten** eingestellt (0.5 = 30 Sekunden) – hat schon einmal zu Verwechslung geführt.
- **Im Kunst-Modus schaltet der Frame den Ton ab** (getestet mit Spotify Connect). Musik also nur über
  externen Lautsprecher oder über eine Diashow außerhalb des Kunst-Modus.
- Termux braucht unter *Apps → Termux*: **„Am Anfang anzeigen“** (= über anderen Apps anzeigen) **an**
  und **Akku: Nicht eingeschränkt**. Die Termux-Benachrichtigung bitte nicht abschalten; Beenden über „Exit“.

## 3. Verlauf
- **15.11.2026** – Programm gebaut (zuerst im Projekt Angel-Adventure, dann in dieses eigene Projekt verschoben).
  Handy-Variante mit Termux eingerichtet, Verbindung zum Frame (IP 192.168.178.26) klappt.
- **15.11.2026** – Verzerrung behoben (16:9 + Ränder füllen).
- **15.11.2026** – Startbildschirm-Icon über Termux:Widget.
- **15.11.2026** – Ordner-Browser, „Ausblenden“ statt Löschen, automatische Fernseher-Suche.
- Bisher keine Pull Requests; Änderungen wurden direkt auf `main` gespeichert.
- **18.11.2026** – Regel „Hilfsprogramme und Tests gehören ins Projekt“ ins Tagebuch aufgenommen (Abschnitt 8).

## 4. Offene Ideen / nächste Schritte
- Musik zur Diashow: Nutzer entscheidet zwischen Bluetooth-Lautsprecher/Soundbar (kein Code nötig)
  oder einer Diashow im TV-Browser (normaler TV-Modus, mit Ton).
- Zeit pro Bild evtl. in **Sekunden** statt Minuten anzeigen.
- Feste IP für den Fernseher in der FritzBox einstellen (Aufgabe des Nutzers).

## 5. Zusammenarbeit
- Der Nutzer ist **Programmier-Laie**. Immer **einfaches Deutsch**, Fachbegriffe kurz erklären,
  **kleine nummerierte Schritte**, klar sagen, **was Claude übernimmt und was der Nutzer selbst tun muss**.
- Claude übernimmt alles, was möglich ist (inkl. Pull Request anlegen und mergen).
- Hardware des Nutzers: **nur Samsung-Smartphone (Chrome)** und **Raspberry Pi 400**.
- Der Nutzer schickt oft Bildschirmfotos – darauf genau eingehen.

## 6. Regel zum Modell
Wenn du nicht auf Opus läufst (z. B. Fable) und eine Aufgabe abgeschlossen ist, erinnere den Nutzer
am Ende der Antwort: **„Tipp: Du kannst jetzt mit /model claude-opus-5-5 zurückstellen.“**

## 7. Pflege
Nach jeder größeren Änderung dieses Tagebuch aktualisieren.

## 8. Hilfsprogramme und Tests gehören ins Projekt
1. Automatische Prüfungen (Tests) und Hilfsprogramme, die über eine einzelne Aufgabe hinaus nützlich sind,
   werden im Projekt gespeichert (z. B. Ordner `werkzeuge/` oder `test/`) – nicht nur im Arbeitsbereich
   der Sitzung, der beim Archivieren verloren geht.
2. Im Tagebuch steht, wie man sie startet und was sie prüfen.
3. Nach jeder Code-Änderung die vorhandenen Prüfungen laufen lassen; bei neuen Funktionen passende Prüfpunkte ergänzen.
4. Gibt es noch keine automatische Prüfung, bei der nächsten Code-Änderung eine einfache anlegen.
5. Was Claude nicht selbst testen kann (z. B. echte Anmeldungen, das echte Handy, den Raspberry Pi),
   im Tagebuch als Test für den Nutzer vermerken.

### Vorhandene Prüfungen
- **Stand 18.11.2026:** noch keine automatischen Prüfungen und keine Hilfsprogramme vorhanden.
  Die erste einfache Prüfung kommt mit der nächsten Code-Änderung.

### Tests für den Nutzer (kann Claude nicht selbst prüfen)
- Verbindung zum echten Fernseher (Frame), Start über das Termux-Icon auf dem Handy, Autostart auf dem Raspberry Pi.
