# Frame-Diashow – Fotos vom Handy auf dem Samsung The Frame

## So funktioniert das Ganze

Ein kleines Programm schickt deine Fotos über das WLAN in den **Kunst-Modus** des Frame
und wechselt sie im eingestellten Takt. Bedient wird es über eine Webseite im Handy-Browser.
Das Programm kann **direkt auf dem Handy** laufen (Variante A) oder auf einem Raspberry Pi (Variante B).

> 💡 Ganz ohne Programm geht es übrigens auch: In der Samsung-App **SmartThings** →
> deinen Frame antippen → **Art Mode / Kunst-Modus** → **Meine Fotos** → Fotos hinzufügen
> und dort die Diashow einstellen. Dieses Programm ist praktisch, wenn du einen ganzen
> Ordner bequem und automatisch abspielen willst.

## Variante A: Alles nur mit dem Handy (ohne Raspberry Pi)

```
 📱 Handy (Programm + Fotos + Bedienung)  ──WLAN──▶  🖼️ The Frame
```

Das Programm läuft in der kostenlosen App **Termux**. Das ist ein „Mini-Computer“ im Handy.

**Du:**
1. **F-Droid** installieren: im Handy-Browser `f-droid.org` öffnen und die App herunterladen.
   (Die Termux-Version aus dem Google Play Store ist veraltet. Bitte nicht die nehmen.)
2. In F-Droid **Termux** suchen und installieren.
3. Termux öffnen und diese Zeilen eintippen (jeweils mit Enter bestätigen):
   ```bash
   pkg install -y git
   git clone https://github.com/marchens1977/fernseh-diashow.git
   bash fernseh-diashow/handy-einrichten.sh
   ```
   Wenn Android nach dem Zugriff auf Fotos fragt: **Erlauben**.
4. Termux schließen und neu öffnen. Ab jetzt startest du das Programm immer mit:
   ```bash
   diashow
   ```
   Der Browser öffnet sich automatisch mit der Diashow-Seite (`http://localhost:8080`).
5. Weiter wie unten bei „Mit dem Fernseher verbinden“.

**Wo kommen die Fotos hin?** In den Handy-Ordner **Bilder → Frame**
(`/storage/emulated/0/Pictures/Frame`). Du kannst in den Einstellungen auf der Seite
auch einen anderen Ordner eintragen, z.B. `/storage/emulated/0/DCIM/Camera` für die Kamerafotos.

**Damit das Handy nicht dauernd laufen muss:** In den Einstellungen das Häkchen
**„Fernseher spielt die Diashow selbst ab“** setzen. Dann schickt das Handy die Bilder einmal
zum Fernseher, und der Fernseher wechselt sie danach von selbst. Termux kannst du dann schließen.
(Ohne Häkchen muss Termux im Hintergrund weiterlaufen.)

## Variante B: Mit dem Raspberry Pi (läuft dauerhaft)

**Du:** Programm auf den Raspberry Pi holen – im Terminal des Pi eingeben:
```bash
git clone https://github.com/marchens1977/fernseh-diashow.git
cd fernseh-diashow
./installieren.sh
```
Am Ende zeigt das Fenster eine Adresse wie `http://192.168.178.20:8080`.

Diese Adresse im Handy-Browser öffnen und weiter wie unten.

## Mit dem Fernseher verbinden (für beide Varianten gleich)
1. Fernseher und Handy (bzw. Pi) müssen im **selben WLAN** sein.
2. Am Fernseher die IP-Adresse nachsehen: *Einstellungen → Allgemein → Netzwerk →
   Netzwerkstatus → IP-Einstellungen* (z.B. `192.168.178.45`).
3. Auf der Diashow-Seite unter **Einstellungen** eintragen → **Speichern**.
4. **Verbindung testen** drücken. Am Fernseher erscheint eine Frage → mit der Fernbedienung
   **„Zulassen“** wählen. Das ist nur einmal nötig.
5. **Diashow starten** drücken. 🎉

## Gut zu wissen
- Beim ersten Start dauert es etwas: jedes Bild wird einmal zum Fernseher geschickt
  (✅ = schon dort). Danach geht der Wechsel schnell.
- Der Fernseher sollte im **Kunst-Modus** sein (oder per Knopf auf der Seite einschalten).
- Wenn der Pi neu startet, startet die Webseite automatisch mit. Die Diashow startest
  du dann wieder per Knopf.
- Bilder kannst du auch direkt (z.B. per USB-Stick) in den Ordner
  `fernseh-diashow/bilder` auf dem Pi kopieren.

## Wenn etwas nicht klappt
| Problem | Lösung |
|---|---|
| „Connection refused/reset“ | IP richtig? Fernseher an (nicht komplett aus)? Gleiches WLAN? |
| Handy: Diashow stoppt nach einer Weile | Häkchen „Fernseher spielt selbst ab“ setzen, oder in den Android-Einstellungen bei Termux den Akku-Sparmodus ausschalten (*Apps → Termux → Akku → Nicht eingeschränkt*) |
| „Fernseher kann die Diashow nicht selbst abspielen“ | Ältere Modelle: Häkchen wieder entfernen, dann wechselt das Handy die Bilder |
| Keine Frage am Fernseher | *Einstellungen → Allgemein → Externe Geräteverwaltung → Gerätverbindungs-Manager*: Zugriff erlauben, ggf. Pi aus der Liste löschen und neu testen |
| Webseite geht nicht auf | Handy: läuft `diashow` noch in Termux? Pi: `sudo systemctl status frame-diashow` und Adresse prüfen |
