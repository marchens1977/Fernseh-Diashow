#!/usr/bin/env python3
"""
Frame-Diashow
=============
Ein kleines Programm fuer den Raspberry Pi.
Es zeigt Bilder aus dem Ordner "bilder" als Diashow auf einem
Samsung "The Frame" Fernseher. Bedient wird es ueber eine Webseite,
die man mit dem Handy im WLAN oeffnet.

Starten:  python3 frame_diashow.py
Dann im Handy-Browser: http://<IP-des-Raspberry>:8080
"""

import io
import json
import logging
import os
import random
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, send_file, url_for
from PIL import Image, ImageOps

try:
    from samsungtvws import SamsungTVArt
except ImportError:  # damit die Webseite auch ohne Bibliothek startet
    SamsungTVArt = None

# ------------------------------------------------------------------
# Ordner und Dateien
# ------------------------------------------------------------------
HIER = Path(__file__).resolve().parent
STANDARD_ORDNER = str(os.environ.get("FRAME_BILDER", HIER / "bilder"))
VORBEREITET = HIER / ".vorbereitet"          # verkleinerte Kopien fuer den TV
EINSTELLUNGEN = HIER / "einstellungen.json"  # TV-Adresse, Intervall ...
HOCHGELADEN = HIER / "hochgeladen.json"      # welches Bild hat auf dem TV welche Nummer
TOKEN_DATEI = HIER / "tv-token.txt"          # "Schluessel" nach dem Erlauben am TV

ERLAUBTE_ENDUNGEN = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".bmp"}
STANDARD = {"tv_ip": "", "minuten": 3, "zufall": False, "passepartout": "none",
            "ordner": STANDARD_ORDNER, "tv_selbst": False}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("frame")

try:  # HEIC-Fotos (iPhone) optional unterstuetzen
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass


def lade_json(datei, standard):
    try:
        return {**standard, **json.loads(Path(datei).read_text())}
    except Exception:
        return dict(standard)


def speichere_json(datei, daten):
    Path(datei).write_text(json.dumps(daten, indent=2, ensure_ascii=False))


def bilder_ordner():
    """Der Ordner mit den Bildern (in den Einstellungen aenderbar)."""
    return Path(lade_json(EINSTELLUNGEN, STANDARD)["ordner"]).expanduser()


def bilder_liste():
    ordner = bilder_ordner()
    ordner.mkdir(parents=True, exist_ok=True)
    return sorted(
        p.name for p in ordner.iterdir()
        if p.is_file() and p.suffix.lower() in ERLAUBTE_ENDUNGEN
    )


def bild_vorbereiten(name):
    """Dreht das Bild richtig herum und verkleinert es auf 4K (3840x2160) als JPG."""
    VORBEREITET.mkdir(exist_ok=True)
    quelle = bilder_ordner() / name
    ziel = VORBEREITET / (Path(name).stem + ".jpg")
    if ziel.exists() and ziel.stat().st_mtime >= quelle.stat().st_mtime:
        return ziel
    with Image.open(quelle) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((3840, 2160) if img.width >= img.height else (2160, 3840))
        img.save(ziel, "JPEG", quality=92)
    return ziel


# ------------------------------------------------------------------
# Verbindung zum Fernseher
# ------------------------------------------------------------------
class Fernseher:
    def __init__(self):
        self.sperre = threading.Lock()  # immer nur ein Befehl gleichzeitig

    def verbinden(self, ip):
        if SamsungTVArt is None:
            raise RuntimeError("Bibliothek 'samsungtvws' fehlt. Bitte installieren.")
        if not ip:
            raise RuntimeError("Bitte zuerst die IP-Adresse des Fernsehers eintragen.")
        return SamsungTVArt(host=ip, port=8002, token_file=str(TOKEN_DATEI),
                            timeout=20, name="Frame-Diashow")

    def test(self, ip):
        with self.sperre:
            tv = self.verbinden(ip)
            try:
                if not tv.supported():
                    raise RuntimeError("Der Fernseher meldet: kein Kunst-Modus (kein The Frame?)")
                return {"kunstmodus": tv.get_artmode(), "api": tv.get_api_version()}
            finally:
                tv.close()

    def hochladen(self, ip, namen, passepartout, fortschritt=None):
        """Laedt Bilder auf den TV, die dort noch nicht sind. Gibt Zuordnung zurueck."""
        zuordnung = lade_json(HOCHGELADEN, {})
        neu = [n for n in namen if n not in zuordnung]
        with self.sperre:
            tv = self.verbinden(ip)
            try:
                for i, name in enumerate(neu, 1):
                    if fortschritt:
                        fortschritt(f"Lade hoch {i}/{len(neu)}: {name}")
                    datei = bild_vorbereiten(name)
                    cid = tv.upload(str(datei), file_type="JPEG",
                                    matte=passepartout, portrait_matte=passepartout)
                    zuordnung[name] = cid
                    speichere_json(HOCHGELADEN, zuordnung)
                    log.info("Hochgeladen: %s -> %s", name, cid)
            finally:
                tv.close()
        return zuordnung

    def zeigen(self, ip, content_id):
        with self.sperre:
            tv = self.verbinden(ip)
            try:
                tv.select_image(content_id, show=True)
            finally:
                tv.close()

    def tv_diashow(self, ip, minuten, zufall, erstes_bild):
        """Laesst den Fernseher die Diashow selbst abspielen (Ordner 'Meine Fotos').
        Dann muss das Handy/der Pi nicht eingeschaltet bleiben."""
        with self.sperre:
            tv = self.verbinden(ip)
            try:
                tv.select_image(erstes_bild, category="MY-C0002", show=True)
                dauer = max(1, round(float(minuten)))
                try:
                    tv.set_slideshow_status(duration=dauer, type=zufall, category_id="MY-C0002")
                except Exception:  # aeltere Modelle kennen nur diesen Befehl
                    tv.set_auto_rotation_status(duration=dauer, type=zufall, category_id="MY-C0002")
            finally:
                tv.close()

    def tv_diashow_aus(self, ip):
        with self.sperre:
            tv = self.verbinden(ip)
            try:
                try:
                    tv.set_slideshow_status(duration=0, category_id="MY-C0002")
                except Exception:
                    tv.set_auto_rotation_status(duration=0, category_id="MY-C0002")
            finally:
                tv.close()

    def kunstmodus(self, ip, an):
        with self.sperre:
            tv = self.verbinden(ip)
            try:
                tv.set_artmode(an)
            finally:
                tv.close()

    def loeschen(self, ip, content_ids):
        with self.sperre:
            tv = self.verbinden(ip)
            try:
                tv.delete_list(content_ids)
            finally:
                tv.close()


TV = Fernseher()


# ------------------------------------------------------------------
# Die Diashow selbst (laeuft im Hintergrund)
# ------------------------------------------------------------------
class Diashow:
    def __init__(self):
        self.laeuft = False
        self.status = "Bereit."
        self.aktuell = ""
        self._stopp = threading.Event()
        self._thread = None

    def starten(self):
        self.stoppen()
        self._stopp.clear()
        self.laeuft = True
        self._thread = threading.Thread(target=self._schleife, daemon=True)
        self._thread.start()

    def stoppen(self):
        self._stopp.set()
        self.laeuft = False
        if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)

    def _schleife(self):
        cfg = lade_json(EINSTELLUNGEN, STANDARD)
        try:
            namen = bilder_liste()
            if not namen:
                raise RuntimeError("Im Ordner 'bilder' liegen keine Bilder.")
            zuordnung = TV.hochladen(cfg["tv_ip"], namen, cfg["passepartout"],
                                     fortschritt=self._setze_status)
        except Exception as e:
            self._setze_status(f"Fehler: {e}")
            self.laeuft = False
            return

        if cfg["tv_selbst"]:
            try:
                erstes = zuordnung[[n for n in namen if n in zuordnung][0]]
                TV.tv_diashow(cfg["tv_ip"], cfg["minuten"], cfg["zufall"], erstes)
                self._setze_status("✅ Der Fernseher spielt die Diashow jetzt selbst ab "
                                   "(alle Bilder unter 'Meine Fotos'). Du kannst das Handy weglegen.")
            except Exception as e:
                self._setze_status(f"Fehler: Der Fernseher kann die Diashow nicht selbst abspielen ({e}). "
                                   "Schalte in den Einstellungen 'Fernseher spielt selbst ab' aus.")
            self.laeuft = False
            return

        reihenfolge = []
        while not self._stopp.is_set():
            if not reihenfolge:
                reihenfolge = [n for n in bilder_liste() if n in zuordnung]
                if cfg["zufall"]:
                    random.shuffle(reihenfolge)
                if not reihenfolge:
                    self._setze_status("Keine Bilder mehr vorhanden.")
                    break
            name = reihenfolge.pop(0)
            try:
                TV.zeigen(cfg["tv_ip"], zuordnung[name])
                self.aktuell = name
                self._setze_status(f"Diashow laeuft – zeige: {name}")
            except Exception as e:
                self._setze_status(f"Fehler beim Anzeigen (versuche weiter): {e}")
            self._stopp.wait(max(0.25, float(cfg["minuten"])) * 60)
        self.laeuft = False

    def _setze_status(self, text):
        self.status = text
        log.info(text)


SHOW = Diashow()


# ------------------------------------------------------------------
# Webseite fuers Handy
# ------------------------------------------------------------------
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # bis 500 MB auf einmal hochladen

SEITE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Frame-Diashow</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;background:#f4f1ea;color:#222}
 header{background:#2f3e46;color:#fff;padding:14px 16px;font-size:1.3em}
 section{background:#fff;margin:12px;padding:14px;border-radius:12px;box-shadow:0 1px 3px #0002}
 h2{margin:0 0 10px;font-size:1.1em}
 button,.knopf{font-size:1em;padding:12px 16px;border:0;border-radius:10px;margin:4px 4px 4px 0;
   background:#52796f;color:#fff;cursor:pointer;display:inline-block;text-decoration:none}
 .rot{background:#b5523b}.grau{background:#888}
 input,select{font-size:1em;padding:8px;border:1px solid #bbb;border-radius:8px;max-width:100%}
 label{display:block;margin:8px 0 4px}
 #status{padding:10px;background:#e9f5db;border-radius:8px;word-break:break-word}
 .raster{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px}
 .raster div{position:relative;font-size:.75em;text-align:center}
 .raster img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:6px;background:#ddd}
 .raster .an{outline:3px solid #52796f}
 .klein{font-size:.85em;color:#555}
</style></head><body>
<header>🖼️ Frame-Diashow</header>

<section><h2>Status</h2><div id="status">{{ status }}</div>
 <p>
 <form method="post" action="{{ url_for('start') }}" style="display:inline"><button>▶️ Diashow starten</button></form>
 <form method="post" action="{{ url_for('stopp') }}" style="display:inline"><button class="rot">⏹️ Stopp</button></form>
 </p>
 <form method="post" action="{{ url_for('artmode', an=1) }}" style="display:inline"><button class="grau">Kunst-Modus an</button></form>
 <form method="post" action="{{ url_for('artmode', an=0) }}" style="display:inline"><button class="grau">Kunst-Modus aus</button></form>
</section>

<section><h2>Fotos vom Handy hinzufügen</h2>
 <form method="post" action="{{ url_for('hinzufuegen') }}" enctype="multipart/form-data">
  <input type="file" name="fotos" accept="image/*" multiple required>
  <button>⬆️ Hochladen</button>
 </form>
 <p class="klein">Die Fotos werden in den Bilder-Ordner (siehe Einstellungen) kopiert.</p>
</section>

<section><h2>Bilder im Ordner ({{ bilder|length }})</h2>
 <div class="raster">
 {% for b in bilder %}
  <div><img loading="lazy" src="{{ url_for('vorschau', name=b) }}" class="{{ 'an' if b == aktuell }}">
   {{ b[:18] }}{% if b in hochgeladen %} ✅{% endif %}
   <form method="post" action="{{ url_for('jetzt', name=b) }}"><button style="padding:6px 8px;font-size:.8em">Zeigen</button></form>
   <form method="post" action="{{ url_for('entfernen', name=b) }}" onsubmit="return confirm('Bild löschen?')">
    <button class="rot" style="padding:6px 8px;font-size:.8em">Löschen</button></form>
  </div>
 {% else %}<p>Noch keine Bilder. Lade oben welche hoch.</p>{% endfor %}
 </div>
 <p class="klein">✅ = schon auf dem Fernseher gespeichert.</p>
</section>

<section><h2>Einstellungen</h2>
 <form method="post" action="{{ url_for('einstellungen') }}">
  <label>IP-Adresse des Fernsehers (z.B. 192.168.178.45)</label>
  <input name="tv_ip" value="{{ cfg.tv_ip }}" placeholder="192.168.x.x">
  <label>Jedes Bild zeigen für … Minuten (0.5 = 30 Sekunden)</label>
  <input name="minuten" type="number" step="0.25" min="0.25" value="{{ cfg.minuten }}">
  <label><input type="checkbox" name="zufall" {{ 'checked' if cfg.zufall }}> Zufällige Reihenfolge</label>
  <label><input type="checkbox" name="tv_selbst" {{ 'checked' if cfg.tv_selbst }}>
   Fernseher spielt die Diashow selbst ab (Handy kann danach aus sein; ganze Minuten; zeigt alle Bilder unter „Meine Fotos“)</label>
  <label>Bilder-Ordner</label>
  <input name="ordner" value="{{ cfg.ordner }}" style="width:100%">
  <span class="klein">Auf dem Handy z.B. <code>/storage/emulated/0/Pictures/Frame</code> oder <code>/storage/emulated/0/DCIM/Camera</code></span>
  <label>Passepartout (Rahmen um das Bild)</label>
  <select name="passepartout">
   {% for wert, text in [('none','kein Rahmen'),('shadowbox_polar','Schattenbox weiß'),('modern_polar','Modern weiß'),('modern_warm','Modern warm'),('flexible_polar','Schmal weiß')] %}
    <option value="{{ wert }}" {{ 'selected' if cfg.passepartout == wert }}>{{ text }}</option>
   {% endfor %}
  </select>
  <p><button>💾 Speichern</button></p>
 </form>
 <form method="post" action="{{ url_for('testen') }}"><button class="grau">📡 Verbindung testen</button></form>
 <form method="post" action="{{ url_for('tv_aufraeumen') }}" onsubmit="return confirm('Alle von diesem Programm hochgeladenen Bilder vom Fernseher löschen?')">
  <button class="rot">🧹 Bilder vom Fernseher entfernen</button></form>
</section>

<script>
 setInterval(async()=>{try{const r=await fetch('{{ url_for("status_json") }}');const j=await r.json();
  document.getElementById('status').textContent=j.status;}catch(e){}},3000);
</script>
</body></html>"""


def im_hintergrund(funktion, *args):
    """Fuehrt eine langsamere Aufgabe aus, ohne dass die Webseite haengt."""
    def lauf():
        try:
            funktion(*args)
        except Exception as e:
            SHOW.status = f"Fehler: {e}"
            log.exception("Fehler")
    threading.Thread(target=lauf, daemon=True).start()


def sicherer_name(name):
    name = Path(name).name
    if name not in bilder_liste():
        raise FileNotFoundError(name)
    return name


@app.get("/")
def startseite():
    return render_template_string(
        SEITE, status=SHOW.status, bilder=bilder_liste(), aktuell=SHOW.aktuell,
        hochgeladen=lade_json(HOCHGELADEN, {}), cfg=lade_json(EINSTELLUNGEN, STANDARD))


@app.get("/status")
def status_json():
    return jsonify(status=SHOW.status, laeuft=SHOW.laeuft, aktuell=SHOW.aktuell)


@app.get("/vorschau/<path:name>")
def vorschau(name):
    with Image.open(bilder_ordner() / sicherer_name(name)) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((320, 320))
        puffer = io.BytesIO()
        img.save(puffer, "JPEG", quality=75)
    puffer.seek(0)
    return send_file(puffer, mimetype="image/jpeg")


@app.post("/start")
def start():
    SHOW.status = "Starte Diashow … (neue Bilder werden zuerst zum Fernseher geschickt)"
    SHOW.starten()
    return redirect(url_for("startseite"))


@app.post("/stopp")
def stopp():
    SHOW.stoppen()
    cfg = lade_json(EINSTELLUNGEN, STANDARD)
    if cfg["tv_selbst"]:
        im_hintergrund(TV.tv_diashow_aus, cfg["tv_ip"])
    SHOW.status = "Diashow gestoppt. Das letzte Bild bleibt auf dem Fernseher stehen."
    return redirect(url_for("startseite"))


@app.post("/zeigen/<path:name>")
def jetzt(name):
    name = sicherer_name(name)
    cfg = lade_json(EINSTELLUNGEN, STANDARD)

    def aufgabe():
        z = TV.hochladen(cfg["tv_ip"], [name], cfg["passepartout"],
                         fortschritt=lambda t: setattr(SHOW, "status", t))
        TV.zeigen(cfg["tv_ip"], z[name])
        SHOW.aktuell = name
        SHOW.status = f"Zeige: {name}"
    im_hintergrund(aufgabe)
    return redirect(url_for("startseite"))


@app.post("/hinzufuegen")
def hinzufuegen():
    ordner = bilder_ordner()
    ordner.mkdir(parents=True, exist_ok=True)
    anzahl = 0
    for datei in request.files.getlist("fotos"):
        name = Path(datei.filename or "").name
        if name and Path(name).suffix.lower() in ERLAUBTE_ENDUNGEN:
            datei.save(ordner / name)
            anzahl += 1
    SHOW.status = f"{anzahl} Foto(s) gespeichert."
    return redirect(url_for("startseite"))


@app.post("/entfernen/<path:name>")
def entfernen(name):
    name = sicherer_name(name)
    zuordnung = lade_json(HOCHGELADEN, {})
    cid = zuordnung.pop(name, None)
    (bilder_ordner() / name).unlink(missing_ok=True)
    (VORBEREITET / (Path(name).stem + ".jpg")).unlink(missing_ok=True)
    speichere_json(HOCHGELADEN, zuordnung)
    if cid:
        im_hintergrund(TV.loeschen, lade_json(EINSTELLUNGEN, STANDARD)["tv_ip"], [cid])
    SHOW.status = f"Gelöscht: {name}"
    return redirect(url_for("startseite"))


@app.post("/einstellungen")
def einstellungen():
    cfg = lade_json(EINSTELLUNGEN, STANDARD)
    cfg["tv_ip"] = request.form.get("tv_ip", "").strip()
    try:
        cfg["minuten"] = max(0.25, float(request.form.get("minuten", 3)))
    except ValueError:
        pass
    cfg["zufall"] = "zufall" in request.form
    cfg["tv_selbst"] = "tv_selbst" in request.form
    if request.form.get("ordner", "").strip():
        cfg["ordner"] = request.form["ordner"].strip()
    cfg["passepartout"] = request.form.get("passepartout", "none")
    speichere_json(EINSTELLUNGEN, cfg)
    SHOW.status = "Einstellungen gespeichert. (Gilt ab dem nächsten Start der Diashow.)"
    return redirect(url_for("startseite"))


@app.post("/testen")
def testen():
    ip = lade_json(EINSTELLUNGEN, STANDARD)["tv_ip"]

    def aufgabe():
        SHOW.status = "Verbinde … Falls am Fernseher eine Frage erscheint: mit der Fernbedienung „Zulassen“ wählen!"
        info = TV.test(ip)
        SHOW.status = f"✅ Verbindung klappt! Kunst-Modus: {info['kunstmodus']}"
    im_hintergrund(aufgabe)
    return redirect(url_for("startseite"))


@app.post("/kunstmodus/<int:an>")
def artmode(an):
    im_hintergrund(TV.kunstmodus, lade_json(EINSTELLUNGEN, STANDARD)["tv_ip"], bool(an))
    SHOW.status = "Kunst-Modus wird " + ("eingeschaltet." if an else "ausgeschaltet.")
    return redirect(url_for("startseite"))


@app.post("/aufraeumen")
def tv_aufraeumen():
    SHOW.stoppen()
    ids = list(lade_json(HOCHGELADEN, {}).values())

    def aufgabe():
        if ids:
            TV.loeschen(lade_json(EINSTELLUNGEN, STANDARD)["tv_ip"], ids)
        speichere_json(HOCHGELADEN, {})
        SHOW.status = f"{len(ids)} Bild(er) vom Fernseher entfernt."
    im_hintergrund(aufgabe)
    return redirect(url_for("startseite"))


if __name__ == "__main__":
    port = int(os.environ.get("FRAME_PORT", 8080))
    log.info("Webseite laeuft auf Port %s. Bilder-Ordner: %s", port, bilder_ordner())
    app.run(host="0.0.0.0", port=port, threaded=True)
