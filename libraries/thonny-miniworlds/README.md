# miniworlds für Thonny

Deutschsprachiges Lernplugin für Thonny 4.1.x (erprobt mit 4.1.7).
Die Bibliothek läuft im ausgewählten lokalen Python-Interpreter ab Version 3.10.
Das Plugin importiert die Spielebibliothek nicht in Thonnys Oberfläche.

## Installation

Die veröffentlichte Version erhältst du über **Extras → Plug-ins verwalten**:
nach dem vollständigen Namen **thonny-miniworlds** suchen und installieren.
Danach Thonny neu starten und **Ansicht → miniworlds** öffnen.

Version 0.10.0 lokal installieren:

1. Vom Repository-Stamm `venv/bin/python -m build libraries/thonny-miniworlds` ausführen.
2. In Thonny **Extras → Plug-ins verwalten → Installieren aus lokaler Datei** öffnen
   (je nach Sprache/Version im Menü für weitere Aktionen).
3. `libraries/thonny-miniworlds/dist/thonny_miniworlds-0.10.0-py3-none-any.whl` auswählen.
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
/pfad/zum/thonny_miniworlds-0.10.0-py3-none-any.whl` aktualisieren.
Für die Entwicklung kann mit demselben Python stattdessen
`pip install -e /pfad/zu/libraries/thonny-miniworlds` verwendet werden.

Pillow liefert Bildminiaturen, pygame-ce die separate Tonvorschau.
Die setuptools-Grenze erhält die von Thonny 4.1 benötigte pkg_resources-API.
Die Spielebibliothek selbst bleibt eine getrennte Backend-Installation.

## Unterrichtsmodus und Projekt

Unter **Mehr** zwischen **Objekte (E2)** und **Klassen (Q1)** wählen. Hilfe, Aufgaben, Vorlagen, Beispiele und Ereignisse passen
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

Die Seitenleiste zeigt die drei Bereiche **Start**, **Code** und **Medien**.
Der aktive Modus bleibt als E2/Q1-Kennung sichtbar. **Objektlabor starten** lädt
das aktuelle Programm direkt im Labor. Installation, Updates und Interpreter
stehen unter **Mehr**.

## Die kurzen Wege

- **Start:** Eigenes Pixel-/Kachelprojekt oder ein Beispiel auswählen. Ein
  gemeinsamer Dialog fragt Projektname und Speicherort ab. Jedes neue Projekt
  erhält `main.py`, `images/`, `sounds/` und seine E2/Q1-Einstellung. Bestehende
  Ordner werden nicht überschrieben. Codevorschau und Beispielfilter werden
  erst auf Wunsch eingeblendet.
- **Code → Hilfe:** Erklärung zum Wort am Cursor oder Thema auswählen.
  **Strg+F1** springt direkt hierher. „Hinweis zeigen“ und „Beispielcode zeigen“
  öffnen die Hilfe schrittweise.
- **Code → Aktion:** Erkanntes World-/Actor-Ziel und Ereignis auswählen.
  Die Ziele werden beim Öffnen und nach Codeänderungen automatisch aktualisiert.
  E2 fügt eine registrierte Funktion vor `.run()` ein, Q1 eine Klassenmethode.
  Bereits vorhandene Ereignisse werden geöffnet; sonst erscheint eine Vorschau.
- **Code → Prüfen:** Die aktuelle Datei wird beim Öffnen automatisch geprüft.
  Erklärungen, Sprünge zur Codezeile und geeignete Korrekturvorschauen helfen
  bei Syntax, Ereignissignaturen, fehlenden Dateien und vermuteten Startfehlern.
  „Erneut prüfen“ aktualisiert die Ergebnisse nach eigenen Änderungen.
- **Medien:** Bildgalerie oder Soundliste wählen. Dateien werden beim ersten
  Öffnen für das aktuelle Projekt automatisch geladen. „Dateien hinzufügen“
  importiert Medien ohne Überschreiben vorhandener Dateien; die neue Datei wird
  ausgewählt. Ziel und Verwendung wählen und **In Code einfügen** drücken.
  Bilder bieten Kostüm/Hintergrund, Sounds den passenden Sound-Aufruf. Für
  vollständige Aufrufe den Cursor auf eine leere, passend eingerückte Codezeile
  setzen. Unter **Dateiaktionen** liegen Pfad-Einfügung, externe Vorschau,
  Entfernen, manuelle Aktualisierung und die alternative Bild-Dateiliste.
  Galerie und Tabelle werden nicht mehr gleichzeitig gezeigt.
- **Objektlabor starten:** Ein Klick öffnet das Labor und lädt das aktuelle
  Programm. Ein bereits geöffnetes Labor wird nur in den Vordergrund geholt,
  damit seine Objekte erhalten bleiben. Ungespeicherte Dateien und ein bereits
  laufendes Programm müssen gegebenenfalls zuerst gespeichert bzw. gestoppt
  werden. Das Labor verwendet den ausgewählten lokalen Thonny-Interpreter.
- **Mehr:** E2/Q1 wechseln, Installation/Updates oder Interpreter/Einstellungen
  öffnen. Installationsstatus und Paketdetails belegen keinen Platz mehr in
  der normalen Navigation.

Alle drei Hauptbereiche und die drei Code-Werkzeuge werden auch bei einer
184 Pixel breiten Seitenleiste auf sichtbare, erreichbare Tab-Köpfe geprüft.

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

Über **Objektlabor starten** steht ein angedocktes Objektlabor
zur Verfügung. Voraussetzung im ausgewählten lokalen Ausführungsinterpreter ist
miniworlds ab 4.4.0.12 mit der internen IDE-Anbindung. Ältere Installationen erhalten einen
Updatehinweis. Das Plugin importiert die Engine weiterhin nicht in die Oberfläche.

- **Q1:** Klassendiagramm mit Vererbung und Sprung zur Klassendefinition in der
  aktuellen Datei. **E2:** Die Objektbank steht im Vordergrund.
- Programm mit **Laden / Neu laden** ausführen. Die Bibliotheksfunktion
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

## Schüleroberfläche im Objektlabor (0.5.0)

Der Ablauf lautet **Objekt auswählen → Methode wählen → Parameter eingeben →
Ausführen**. Für bekannte Parameter erscheinen eigene, beschriftete Felder mit
Standardwerten und einer Wahl zwischen **Wert** und **Objekt**. Der Objektwähler
pro Parameter ist unabhängig vom Empfänger in der Objektbank. Pflichtfelder
und einfache Zahl-/Text-/Wahrheitswert-Eingaben werden vor dem Aufruf geprüft.
Die Vorschau zeigt den tatsächlichen Python-Aufruf. Für dynamische Signaturen,
zusätzliche Argumente und erfahrenere Lernende bleibt die **Python-Eingabe**
verfügbar. Sie wertet weiterhin keine beliebigen Funktionsaufrufe aus.

Die Zustandsansicht zeigt **Vorher** und **Nachher**. Geänderte Attribute erhalten
einen Punkt; dieser Vergleich bleibt beim Auswählen und Aktualisieren erhalten,
bis die nächste bewusste Aktion einen neuen Vergleich beginnt. Nach Fehlern
werden mögliche Teiländerungen ebenfalls sichtbar.

**Stopp** verwendet Thonnys Stop/Restart. **Ausblenden** erhält die laufende
Sitzung samt Objektbank. Die Anzeige
unterscheidet Laden, laufende Aufrufe, pausierte Bereitschaft und geänderten Code.
Aufrufe und Konstruktoren sind während einer laufenden Simulation gesperrt;
zuerst pausieren. Die Objekterzeugung ist zunächst eingeklappt. E2 verwendet
„Figur“ und „Methode ausprobieren“, Q1 „Instanz“ und „Konstruktor“.

Fehler erhalten einen kurzen Hinweis außerhalb des Aufrufprotokolls. Der
vollständige Fehlerbericht ist unter **Fehlerdetails** erreichbar.
Das Labor ist unter dem Editor angedockt; Aufrufbereich und Tabellen sind scrollbar. Die erste Implementierung verwendet Thonnys
native Tk/ttk-Oberfläche und benötigt keine weitere Grafikbibliothek.

## Angedocktes Objektlabor (0.8.0)

**Objektlabor starten** öffnet einen breiten Arbeitsbereich unter dem Editor,
ohne Zusatzfenster. Links bleiben die Figurenkarten sichtbar, in der Mitte stehen
Methodenauswahl, Parameter und Ergebnis. Q1 ergänzt rechts Klassenkarten mit
Vererbungslinien. Die Trennlinie lässt sich verschieben.
Beim ersten Öffnen erhält das Labor ausreichend Höhe; anschließend bleibt die
von dir eingestellte Aufteilung erhalten. Auch **Ansicht → miniworlds · Objektlabor**
öffnet den Bereich, ohne automatisch Schülercode zu starten.

Für Actors sind vorhandene Methoden wie `move`, `turn_left` und `turn_right`
direkt erreichbar. Unter **Weitere Methoden** versteht die Suche Python-Namen und die angebotenen
deutschen Beschreibungen, etwa „bewegen“. Gruppen filtern Bewegung, Aussehen
oder eigene Methoden. Es werden ausschließlich Methoden der ausgewählten Instanz angeboten.
E2 beginnt bei Actors mit `move`; Q1 bevorzugt eine eigene Methode und zeigt
vollständige Signaturen sowie das Klassendiagramm.

Benötigte Parameter und das erste optionale Feld stehen direkt im Formular.
**Weitere Parameter** öffnet zusätzliche optionale Eingaben. Ihre Werte gelten
auch im eingeklappten Zustand und sind in der Python-Vorschau sichtbar.
Eingaben bleiben beim Wechsel zwischen Methoden und Objekten erhalten.
**Enter** im Parameterfeld führt den Aufruf aus. Unter **Mehr** sind
**Vorhersage** und **Argumente als Python eingeben** zuschaltbar.

Ergebnis und geänderte Attribute erscheinen unmittelbar unter der Aktion.
Unter **Mehr → Alle Eigenschaften** öffnet sich der vollständige
Vorher/Nachher-Vergleich.
**Aufrufe in Code übernehmen …** öffnet die bestehende Vorschau für den gesamten
Experimentablauf. Unter **Mehr → Verlauf** lassen sich die Aufrufe lesen und der letzte
Methodenaufruf mit seinen ursprünglichen Argumenten und seinem ursprünglichen
Empfänger wiederholen. Konstruktoren werden nicht automatisch wiederholt.
Fehler stehen direkt beim Formular, ohne die Eingaben zu löschen; der komplette
Bericht lässt sich über **Fehlerdetails** öffnen.

**Start / Pause** ist ein gemeinsamer Schalter in der festen Steuerleiste. Die Weltwahl erscheint nur,
wenn mehrere Welten vorhanden sind. **Zurücksetzen** beendet den eigenen Laborlauf,
wartet auf Thonnys Backend-Neustart und startet den aktuellen Editorstand.
**Stopp** beendet das Programm und bricht auch einen geplanten Neustart ab.

**Ausblenden** erhält Verbindung, Objekte, Eingaben und Ergebnisse. Der erneute
Laboraufruf zeigt dieselbe Sitzung. Beim Entfernen der Ansicht werden Verbindung,
Ereignisbindungen und Hintergrundabfragen freigegeben.

Das pygame-Weltfenster wird weiterhin von der Engine dargestellt. Eingebettet
ist die Bedienoberfläche des Objektlabors; Einstellungen und Codeänderungs-
vorschauen behalten ihre bisherigen Dialoge.


## Werkstattoberfläche (0.9.0)

Die Objektbank zeigt Karten mit Figurenvorschau, Variablenname und Klasse.
Eine markierte Karte erhält einen Rahmen und ein Häkchen. Klick oder
Pfeiltasten wählen eine Figur; Home/End springen zur ersten/letzten Karte.
Lange Namen werden auf der Karte gekürzt und im Aufrufbereich vollständig
angezeigt. Kostümvorschauen kommen als kleine PNGs aus dem Backend; Thonnys
Oberfläche importiert weiterhin weder miniworlds noch pygame. Fehlt ein
Vorschaubild, erscheint der Anfangsbuchstabe der Klasse.

Im Q1-Modus stehen rechts Klassenkarten mit Vererbungslinien. Ein Klick wählt
die Klasse im bestehenden Konstruktorformular, ein Doppelklick öffnet ihre
Definition in der aktuellen Datei. E2 blendet diesen Bereich aus und zeigt
Methoden mit kurzen deutschen Beschreibungen statt Vererbungsangaben.

Im Aufrufbereich stehen Methode und Eingaben über der Python-Vorschau mit
**Ausführen**. Darunter fasst ein eigener Ergebnisbereich den Aufruf und seine
Wirkung zusammen. Suche und Methodengruppen werden über **Weitere Methoden**
geöffnet. **Mehr** bündelt Vorhersage, Python-Eingabe, Eigenschaften, Verlauf,
Fehlerdetails und ausführliche Hinweise. Die Wahl **Wert/Objekt** erscheint
bei untypisierten Parametern mit verfügbaren Objektreferenzen; einfache Zahlen-,
Text- und Richtungsfelder bleiben kompakt.

Unten bleiben **Laden / Zurücksetzen**, **Stopp**, **Start / Pause** und ein
kurzer Status sichtbar, auch wenn oben Formulare oder Details gescrollt werden.
**Zurücksetzen** führt den aktuellen Editorstand neu aus und verwirft dabei den
bisherigen Experimentzustand. Die Welt bleibt im vorhandenen pygame-Fenster;
die Werkstatt ist weiterhin direkt in Thonny angedockt.


## Weniger Umwege im Labor (0.10.0)

Die Werkstatt passt ihre Bedienelemente an die verfügbare Breite an: Häufige
Methoden werden umgebrochen, der Ausführen-Button rückt bei wenig Platz unter
den Python-Aufruf und die feste Steuerleiste nutzt bei Bedarf zwei Zeilen.
Im Q1-Modus lässt sich die Klassenübersicht über **Klassen anzeigen** ein- und
ausblenden. Diese Wahl bleibt innerhalb der Sitzung auch bei E2/Q1-Wechseln
bestehen.

Das Labor merkt sich die zuletzt gewählte Methode und ihre Eingaben pro Figur.
Beim Wechsel zurück wird dieser Arbeitsstand wieder angezeigt. Ab sieben
Objekten erscheint eine Suche nach Namen, Alias oder Klasse. Sie filtert nur
die Karten, ohne den Empfänger eines Methodenaufrufs stillschweigend zu ändern.
Ein Hinweis zeigt eine ausgeblendete Auswahl an. **×** oder **Escape** leeren
die Suche; die Pfeiltasten bewegen sich durch die sichtbaren Treffer.

Ungültige Eingaben erhalten Hinweise direkt am Feld. Solange Werte fehlen oder
ungültig sind, ist **Ausführen** gesperrt. Eine kurze Erklärung zeigt auch bei
laufender Simulation oder geändertem Code, welcher nächste Schritt nötig ist.
Der Ergebnisbereich nennt ausdrücklich den Empfänger des letzten Aufrufs und
behält dessen Änderungen beim Wechsel zu einer anderen Figur bei. Der komplette
Eigenschaftenvergleich unter **Mehr** bezieht sich weiterhin auf die aktuell
ausgewählte Figur.
