# miniworlds für Thonny

Deutschsprachiges Lernplugin für Thonny 4.1.x (erprobt mit 4.1.7).
Die Bibliothek läuft im ausgewählten lokalen Python-Interpreter ab Version 3.10.
Das Plugin importiert die Spielebibliothek nicht in Thonnys Oberfläche.

## Installation

Die veröffentlichte Version erhältst du über **Extras → Plug-ins verwalten**:
nach dem vollständigen Namen **thonny-miniworlds** suchen und installieren.
Danach Thonny neu starten und **Ansicht → miniworlds** öffnen.

Version 0.4.1 lokal installieren:

1. Vom Repository-Stamm `venv/bin/python -m build libraries/thonny-miniworlds` ausführen.
2. In Thonny **Extras → Plug-ins verwalten → Installieren aus lokaler Datei** öffnen
   (je nach Sprache/Version im Menü für weitere Aktionen).
3. `libraries/thonny-miniworlds/dist/thonny_miniworlds-0.4.1-py3-none-any.whl` auswählen.
4. Thonny neu starten.

Auf Linux mit einer vom Betriebssystem verwalteten Python-Installation kann
PEP 668 die Plugininstallation verhindern. Die Auswahl einer Projekt-venv in
Thonny ändert dessen eigene Umgebung nicht. In diesem Fall auch Thonny selbst
in einer venv installieren und daraus starten:

```sh
python -m venv ~/.venvs/thonny
~/.venvs/thonny/bin/python -m pip install 'thonny>=4.1,<4.2' thonny-miniworlds 'setuptools<81'
~/.venvs/thonny/bin/python -m thonny
```

Ein lokales Wheel lässt sich mit `~/.venvs/thonny/bin/python -m pip install
/pfad/zum/thonny_miniworlds-0.4.1-py3-none-any.whl` aktualisieren.
Für die Entwicklung kann mit demselben Python stattdessen
`pip install -e /pfad/zu/libraries/thonny-miniworlds` verwendet werden.

Pillow liefert Bildminiaturen, pygame-ce die separate Tonvorschau.
Die setuptools-Grenze erhält die von Thonny 4.1 benötigte pkg_resources-API.
Die Spielebibliothek selbst bleibt eine getrennte Backend-Installation.

## Unterrichtsmodus und Projekt

Oben zwischen **E2 · Programmieren mit Objekten** und **Q1 · Programmieren mit
Klassen** wählen. Hilfe, Aufgaben, Vorlagen, Beispiele und Ereignisse passen
sich daran an. Bestehender Schülercode wird nicht automatisch konvertiert.

Bei einer gespeicherten lokalen Datei wird die Wahl in `.miniworlds.json`
gespeichert. Neue Projekte erhalten diese Datei automatisch. Unterordner
verwenden die nächstgelegene Projektdatei eines übergeordneten Ordners.
Ohne Projektdatei gilt zunächst der globale Standard; bei ungespeicherten
Dateien ändert die Auswahl diesen Standard. Der aktive Modus bleibt oben
sichtbar und wird beim Wechsel zwischen gespeicherten Dateien geladen.

```json
{"mode": "Q1"}
```

Die Bereichsauswahl unter dem Modus macht alle Funktionen auch in schmalen
Seitenleisten erreichbar. Der Medienbereich ist zusätzlich scrollbar.

## Bereiche

- **Installation:** Zeigt Version und Installationsort des Plugins, Thonnys
  Python sowie Version/Installationsort der Bibliothek im ausgewählten lokalen
  Ausführungsinterpreter. Erkennt venvs, PEP 668 und zu alte Python-Versionen.
  Der Status wird ausdrücklich aktualisiert; Schülercode wird nicht ausgeführt.
  Die Bibliotheksinstallation öffnet den exakten PyPI-Paketnamen `miniworlds`
  und umgeht die Top-1000-Suche. Download/Installation benötigt Internet;
  das laufende Programm zunächst stoppen. MicroPython wird nicht unterstützt.
- **Hilfe:** Thema wählen oder **Strg+F1** am Wort im Editor drücken.
  World/Actor, eigene Unterklassen, Importaliasnamen sowie `self` und
  `self.world` werden soweit statisch möglich erkannt. Zuerst erscheinen
  Erklärung, Parameter und Rückgabewert. Ein weiterer Klick zeigt einen
  Hinweis, danach ein vollständiges Beispiel. E2 erklärt Objektzustand und
  Registrierung; Q1 erklärt Instanzen, Vererbung und überschreibbare Methoden.
- **Vorlagen:** Pixel- und Kachelwelten mit einer Aufgabe und Kommentaren
  erstellen. Jedes Projekt erhält `main.py`, `images/`, `sounds/` und seine
  Unterrichtseinstellung. Bestehende Projektordner werden nicht überschrieben.
- **Ereignisse:** Nur erkannte miniworlds-Worlds/Actors beziehungsweise deren
  Klassen anbieten. Actor-Ereignisse werden für Worlds ausgeblendet. E2 fügt
  registrierte Funktionen vor `.run()` ein, Q1 Methoden in die ausgewählte
  Klasse. Bestehende Ereignisse werden geöffnet. Vor dem Einfügen erscheint
  eine Änderungsvorschau; Kommentare und Einrückung bleiben erhalten.
  Einzeilige Klassen zuerst auf mehrere Zeilen verteilen.
- **Beispiele:** Nach Thema und Schwierigkeit filtern; der aktive
  Unterrichtsmodus bestimmt die Codevariante. Erwartetes Verhalten und Aufgabe
  stehen vor Hinweis und Lösungscode. Beispiele als eigenständiges Projekt
  öffnen. Enthalten: Grundgerüst, Bewegung, Tastatur und Maus.
- **Bilder & Sounds:** Dateien importieren, Miniaturen auf Schachbretthintergrund
  ansehen sowie Bildmaße und Transparenz prüfen. PNG, JPG/JPEG, GIF, BMP und
  WebP sowie WAV, OGG und MP3 werden aufgelistet. Namenskonflikte erhalten eine
  Nummer. Ein relativer Pfad lässt sich am Cursor einfügen; fertige Kostüm-,
  Hintergrund- und Soundaufrufe werden für ein angegebenes Ziel als Vorschau
  angeboten. Den Cursor dafür auf eine leere, passend eingerückte Codezeile
  setzen. Pfade beziehen sich auf die bearbeitete Python-Datei, auch in
  Unterordnern. Sounds separat abspielen, stoppen und ihre Lautstärke ändern;
  sie belegen keinen laufenden Schülerprozess. Externes Öffnen und Entfernen
  mit Bestätigung sind ebenfalls möglich.
- **Prüfung:** Unterscheidet konkret feststellbare Fehler von Hinweisen.
  Mehrzeilige Erklärungen und Sprünge zur Codezeile ergänzen Syntaxprüfung,
  Ereignissignaturen, vermutete fehlende Registrierung, `.run()` und fehlende
  Mediendateien. Für geeignete Signaturfehler und einen fehlenden Startaufruf
  gibt es eine Korrekturvorschau. Jede übernommene Änderung ist genau ein
  Rückgängig-Schritt. Wurde der Code inzwischen bearbeitet, wird die alte
  Änderung nicht angewendet.

## Grenzen

Die Prüfung und Objekterkennung führen keinen Schülercode aus. Dynamische
Fabriken, indirekte Registrierungen, eigene Suchpfade und mehrere Dateien
lassen sich deshalb nur teilweise beurteilen. Nur bekannte miniworlds-Typen
und nachvollziehbare lokale Vererbung werden als Ereignisziele angeboten.
Hinweise sind keine vollständige Korrektheitsprüfung. Eine Signaturkorrektur
muss weiterhin hinsichtlich der Parameternutzung im Rumpf geprüft werden.
Ein vorgeschlagener `.run()`-Aufruf gehört nur ins Startprogramm.

Bild-/Audioformatunterstützung hängt auch von Pillow, pygame und dem System ab.
Sehr große oder beschädigte Bilder können nicht als Miniatur geladen werden.
Der Installationsstatus beschreibt installierte Paketmetadaten, keine
vollständige Funktionsprüfung der Bibliothek oder ihrer Grafik-/Audiotreiber.

Ein Live-Weltinspektor ist für eine spätere Version vorgesehen.

## Entwicklung und Prüfung

- `core.py`: Gemeinsame Ereignisse, Offline-Inhalte, AST-Erkennung, Codeänderungen,
  Projekt-/Medienfunktionen und Diagnose.
- `view.py`: Tk-Oberfläche und Adapter zur Paketverwaltung von Thonny 4.1.
- `audio.py`: Separater Mixerprozess für Tonvorschau.
- `__init__.py`: Registrierung unter `thonnycontrib.miniworlds`.

Vom Repository-Stamm:

```sh
venv/bin/invoke tests.thonny
venv/bin/python -m build libraries/thonny-miniworlds
```

Docker-Tests prüfen beide Modi, Beispiel-/Weltkombinationen mit der echten
Engine, Projektdaten, Alias-/Vererbungserkennung, Ereigniseinfügung, Kommentare,
Einrückung, Diagnose und Korrekturen. Echte Tk-Widgets unter Xvfb prüfen
zusätzlich Rückgängig/Wiederholen, Galerien, Filter, Tonvorschau mit Dummy-Audio,
veraltete Änderungen und den ausgewählten Statusinterpreter.

Der Paketmanageradapter verwendet interne Thonny-Methoden. Bei einer Erweiterung
des unterstützten Versionsbereichs muss er erneut geprüft werden.

## UI-Entwurf

Ein [UI-Review mit Gestaltungsvorschlag](design/ui-review.md) beschreibt die
nächste Überarbeitung. Eine [grafische Vorschau](design/ui-concept.png) zeigt
Ereignisse, Medien und eine kompakte Seitenleiste. Diese Entwürfe ändern die
laufende Version 0.2.0 noch nicht.

## Versionsprüfung und Reparatur (0.3.0)

Beim Öffnen von **Bibliothek installieren / aktualisieren** werden automatisch
installierte Version und reguläre Versionen auf PyPI verglichen. Die Anzeige
unterscheidet verfügbare Updates, aktuelle Versionen und einen fehlgeschlagenen
Onlineabruf. Python-Anforderungen und zurückgezogene Releases werden beachtet.
Die Versionsprüfung fragt den öffentlichen PyPI-Index ab; pip verwendet für die
Installation weiterhin den konfigurierten Paketserver, etwa einen Schulmirror.

**Reparieren mit Sicherung** ist für beschädigte oder unvollständige
miniworlds-Paketdateien gedacht, beispielsweise fehlende RECORD-Dateien oder
verwaiste Installationen. Nach einer Rückfrage lädt der Helfer alle benötigten
Wheels herunter, bevor er die alte Installation verändert. Er kopiert
miniworlds und seine Paketinformationen in den Ordner `miniworlds-backups` im
Thonny-Benutzerprofil und stellt die Bibliothek neu her. Die bisherigen Dateien
werden auf demselben Dateisystem zwischengelagert, damit Verschieben und
Wiederherstellen nicht an einem dateisystemübergreifenden Kopieren scheitern.
Bei einem Installationsfehler wird die bisherige miniworlds-Installation
wiederhergestellt; die Sicherung und ein Manifest bleiben zur Diagnose erhalten.
Andere von pip installierte Abhängigkeiten sind nicht Teil dieser Rücksicherung.

Die Reparatur betrifft ausschließlich das Installationsverzeichnis des
gewählten Interpreters (venv bzw. Benutzer-site-packages). Erweiterungen wie
miniworlds-physics und Schülerprojekte werden nicht bereinigt. Verknüpfte und
editierbare Entwicklungsinstallationen werden nicht automatisch angefasst.
PEP 668 wird nicht umgangen. Netzwerk-, Zertifikats-, Rechte- und
Versionsprobleme erhalten eigene Hinweise; eine Dateibereinigung behebt sie
nicht. Ohne passende binäre Pakete bleibt die vorhandene Installation erhalten.

Die Vorgänge laufen außerhalb des Schülerprogramms. Nach erfolgreicher
Installation wird der ausgewählte Backend-Interpreter neu gestartet. Das
Protokoll kann zur Fehlerdiagnose gespeichert werden.

Zusätzlicher Integrationstest mit Internet, echter pip-Installation und einer
absichtlich entfernten RECORD-Datei in einer wegwerfbaren Test-venv:

```sh
venv/bin/invoke tests.thonny --network
```

## Objektlabor / BlueJ-artiges Experimentieren (0.4.0)

Unter **Objektlabor → Objektlabor öffnen** steht ein eigener Experimentierdialog
zur Verfügung. Voraussetzung im ausgewählten lokalen Ausführungsinterpreter ist
miniworlds ab 4.4.0.12 mit der internen IDE-Anbindung. Ältere Installationen erhalten einen
Updatehinweis. Das Plugin importiert die Engine weiterhin nicht in die Oberfläche.

- **Q1:** Klassendiagramm mit Vererbung und Sprung zur Klassendefinition in der
  aktuellen Datei. **E2:** Die Objektbank steht im Vordergrund.
- Programm mit **Programm neu laden** ausführen. Die Bibliotheksfunktion
  `World.run()` läuft regulär im ausgewählten Thonny-Interpreter. Nach der
  Einrichtung werden die Welten vor dem ersten Simulationsschritt pausiert.
  Der Editorstand wird unter dem ursprünglichen Dateinamen ausgeführt.
- Objektbank zeigt Namen, Klassen und gemeinsame Referenzen. Mehrere Namen
  für dasselbe Objekt werden in einer Zeile zusammengefasst. Ein ausgewählter
  Actor erhält einen Rahmen im Weltfenster.
- Zustand zeigt öffentliche Instanzattribute sowie Position, Richtung und
  Größe von Actors. Geänderte Felder tragen einen Punkt und eine Hervorhebung.
- Eigene Methoden und ausgewählte geerbte Engine-Methoden werden mit Herkunft
  und Signatur angeboten. Argumente sind Python-Literale und bekannte
  Objektreferenzen, keine frei ausgewerteten Ausdrücke.
- Eine freiwillige Vorhersage, der Python-Aufruf und sein Ergebnis erscheinen
  im Protokoll. Eigene Klassen sowie Actor/World lassen sich über einen
  Objektnamen und Konstruktorargumente instanziieren.
- Erfolgreiche Experimente lassen sich über eine Änderungsvorschau in den
  Programmcode vor einem obersten `.run()` übernehmen. Nach einem Fehler mit
  möglichen Teiländerungen ist die Übernahme gesperrt; für einen vollständigen
  reproduzierbaren Ablauf neu laden.
- Änderungen an der Hauptdatei oder gespeicherten Python-Dateien des Projekts
  markieren die Objektbank als veraltet und sperren weitere Aufrufe bis zum
  Neuladen. Die alte Zustandsansicht bleibt erhalten. Andere ungespeicherte
  Editorpuffer und externe Abhängigkeiten werden noch nicht als Revision erfasst.
- **Experiment beenden** leert die Objektbank. Ein blockierender Schüleraufruf
  kann durch Beenden des getrennten Prozesses abgebrochen werden.

Alle Objektoperationen laufen auf dem SDL-/Hauptthread über `ExperimentSession`,
`World.invoke`, `pause` und `refresh`. Damit wird kein normaler Simulationsschritt
für einen Methodenaufruf benötigt. Andere laufende Thonny-Programme und ihre
Objekte werden nicht in das Labor übernommen. Das Programm wird tatsächlich
ausgeführt: Der Prozess ist eine getrennte Laufzeit, keine Sicherheits-Sandbox.
Benutzereingaben mit `input()` und selbst betriebene Endlosschleifen sind beim
Laden nicht interaktiv bedienbar; dafür das Experiment beenden.

Die erste Klassenübersicht umfasst die aktuelle Datei. Automatisch entdeckte
Actors ohne eigenen Namen erhalten eine passende Referenz. Bei mehreren Welten
werden alle erkannten aktiven Welten pausiert; neue Actors entstehen zunächst
im normalen, von miniworlds bestimmten Weltkontext.

## Experimentieren im Thonny-Interpreter

Im **Objektlabor** startet **Programm neu laden** den aktuellen Editorstand im
lokalen Thonny-CPython-Backend. Schülercode bleibt unverändert: `world.run()`
läuft regulär. Nach der Einrichtung pausieren alle Welten vor dem ersten
Simulationsschritt. Die Oberfläche importiert die Spielebibliothek nicht.

Die Objektbank zeigt vorhandene Worlds, Actors und eigene Instanzen mit ihren
Namen und Aliasen. Methoden lassen sich mit Zahlen, Texten, Containern und
Objektreferenzen aufrufen; auch Referenzen innerhalb von Listen und Tupeln sind
möglich. Eigene Klassen können instanziiert werden. Nichtprimitive Ergebnisse
werden, soweit vom Inspektor unterstützt, in die Objektbank aufgenommen.
Ein Aufruf pausiert die Welten; bereits ausgeführte Änderungen bleiben auch bei
einem Fehler sichtbar. Der Fehlerbericht enthält den Traceback im Schülercode.

**Pausieren** und **Fortsetzen** gelten für alle oder eine ausgewählte Welt.
Die Weltwahl bestimmt auch die Standardwelt neu erzeugter Actors. Stop/Restart
in Thonny beendet die Ausführung und leert die Objektbank. Das Schließen des
Labors trennt die Verbindung und pausiert die Welten; zum Beenden des Programms
Thonnys Stop/Restart verwenden. Lange Schüleraufrufe werden darüber abgebrochen.

Bei Editoränderungen oder geänderten Python-Dateien im Projekt erscheint der
Hinweis auf den vorherigen Programmstand. Weitere offene Projektdateien mit
ungespeicherten Änderungen müssen vor dem Start gespeichert werden: Python
importiert diese regulär vom Datenträger. Änderungen am Hauptprogramm werden
als Editorstand ausgeführt, ohne die Datei umzuschreiben. Normales F5 außerhalb
des Labors aktiviert den Experimentiermodus nicht.

Technik: Ein Backend-Plugin unter `thonnycontrib.backend` wertet nur explizit
markierte `Run`-Aufträge aus. Ein zufälliges Token schützt den lokalen
Loopback-Kanal; Request-ID und Sitzungsgeneration ordnen Antworten zu.
Ein Empfangsthread reiht Kommandos ein, die miniworlds zwischen Frames auf dem
Welt-Thread ausführt. Schülerausgaben bleiben in Thonnys Shell. Die Verbindung
benötigt miniworlds ab 4.4.0.12 mit `runtime_host.API_VERSION = 1`.
Das Plugin prüft die vorhandene Fähigkeit zusätzlich zur Paketversion.

Die Thonny-spezifischen Stellen sind auf 4.1.7 abgestimmt. Ein echter
CPython-Backend-Protokolltest liegt in `test_live_backend.py`; ohne installierte
Thonny-Testabhängigkeit wird er übersprungen. Zusätzlich prüfen Socket- und
Tk-Tests Tokenprüfung, Antwortzuordnung und Neustarts.

## Auslieferung des Objektlabors

Benötigt werden beide neu gebauten Pakete: `miniworlds` im ausgewählten
Ausführungsinterpreter und `thonny-miniworlds` in Thonnys eigener Umgebung.
Das Engine-Wheel muss `miniworlds/base/runtime_host.py` mit `API_VERSION = 1`
enthalten, das Plugin-Wheel `thonnycontrib/backend/miniworlds_experiment.py`.
Nach einem Pluginupdate Thonny vollständig neu starten. Danach im Objektlabor
„Programm neu laden“ wählen. Für die Direktverbindung wird lokaler
Loopback-Verkehr benötigt; ein Zugriff anderer Rechner ist nicht erforderlich.

Die Integration ist mit Thonny 4.1.7 und Desktop-CPython getestet.
Schulrechner mit Windows/macOS und Schulnetz-Richtlinien benötigen noch einen
Abnahmelauf; diese Plattformen wurden hier nicht tatsächlich getestet.

```sh
venv/bin/invoke tests.thonny
venv/bin/invoke tests.thonny-backend
```
