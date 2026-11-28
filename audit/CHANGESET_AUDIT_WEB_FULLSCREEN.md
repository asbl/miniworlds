# Audit der Änderung: `fullscreen=True` im Browser

Geprüfter Bereich: Änderungssatz auf Basis von `a3e6f02`, insbesondere
`source/miniworlds/base/window.py`, die Pyodide-/Unit-Tests sowie Changelog und
Testdokumentation.

## Ziel

Programme, die mit `world.run(fullscreen=True)` geschrieben wurden, sollen im
miniworlds-Editor und in der WebAssembly-/Pyodide-Umsetzung starten und
zeichnen. Der Browser besitzt dort keinen frei positionierbaren
SDL-Fenstermodus; Vollbild wird von der einbettenden Seite angeboten.

## Befund (behoben)

`Window._update_surface()` rief bei `fullscreen=True` immer
`set_mode((width, height), pygame.SCALED)` auf. Unter Emscripten ist das im
Pyodide-Worker des Editors kein gültiger Fenstermodus: Der Aufruf kehrt nicht
zurück. Der vorhandene Guard in `PlatformAdapter.toggle_fullscreen()`
verhinderte nur den zweiten Schritt, nicht das Blockieren davor.

Reproduktion im echten Worker mit transferiertem `OffscreenCanvas`:

- vor dem Fix: letzter Fortschritt `set-fullscreen`, danach Timeout; der
  Python-Aufruf `window.fullscreen = True` wurde nie fortgesetzt.
- nach dem Fix: `fullscreen set`, `prepared`, `frame 3`,
  `window canvas (320, 240)`; der Worker lief normal weiter.

Die Änderung wertet `fullscreen`, `fit_desktop` und `replit` auf Web-Plattformen
nicht mehr als SDL-Fenstermodi aus, sondern verwendet den normalen,
weltgroßen Canvas-Pfad. Auf dem Desktop bleiben `pygame.SCALED`,
`toggle_fullscreen()` und `fit_desktop` unverändert.

## Weitere Prüfpunkte

- **Startreihenfolge:** `App.run()` setzt `window.fullscreen`, bevor
  `App.init` aktiv ist. Der Web-Pfad legt zunächst wie bisher eine
  1×1-Platzhalterfläche an und erhält nach `prepare_mainloop()` die
  Weltgröße. Der neue Pyodide-Test ruft deshalb nicht nur den Setter auf,
  sondern `world.run(fullscreen=True)` selbst.
- **Desktop-Regression:** Für den unveränderten Desktop-Pfad fehlte bisher
  eine explizite Prüfung. Ergänzt: `SCALED` wird weiterhin verwendet und
  `toggle_fullscreen()` aufgerufen.
- **Weitere `SCALED`-Verwendung:** `replit` war ebenfalls betroffen und ist
  im Web-Pfad mit abgedeckt. Außerhalb von `window.py` gibt es keine weiteren
  `pygame.SCALED`-Aufrufe.
- **Zustand und API:** `window.fullscreen` liefert im Browser weiterhin den
  gesetzten Wert. Im Quelltext liest ihn außer `Window` niemand, daher entsteht
  kein widersprüchlicher Zustand.
- **Anzeige-Abbau:** Die Änderung berührt weder `pygame.display.quit()` noch
  den Web-spezifischen Verzicht darauf; Stop-/Neustart-Verhalten bleibt
  unverändert.

## Validierung

- Vollständige Pyodide-/Chromium-Suite: **29 bestanden, 0 fehlgeschlagen**,
  inklusive des neuen End-to-End-Tests mit `world.run(fullscreen=True)`.
- Fokussierte Unit-Tests `test_window_position.py`: **5 bestanden**, darunter
  Web- und Desktop-Pfad.
- `test_app_lifecycle.py`: **11 bestanden**.
- Worker-Reproduktion vor/nach dem Fix wie oben beschrieben.
- `git diff --check` und `py_compile` sauber.

Die Docker-Suite konnte in dieser Umgebung nicht ausgeführt werden, weil kein
Docker verfügbar ist. Es wurden keine visuellen Referenzen verändert.

## Grenzen und offene Risiken

- Das Programm löst im Browser weiterhin **kein** echtes Browser-Vollbild aus.
  Das entspricht dem bestehenden Vertrag: Editor und H5P-Player steuern
  Vollbild über ihre eigene Schaltfläche.
- `fit_desktop` und `replit` gehörten nicht zum ursprünglichen Fehlerbericht.
  Sie werden mitbehandelt, weil beide im Web ebenfalls desktop-spezifische
  SDL-Modi verwenden (`(0, 0)` bzw. `SCALED`). Eine separate Browser-Prüfung
  des H5P-Hauptthread-Pfads fand nicht statt; er nutzt dieselbe
  `is_web()`-Verzweigung.
- Der automatisierte Pyodide-Test läuft im Hauptthread der Testseite. Den
  Worker-Deadlock kann er daher nicht selbst erzeugen; dieser wurde manuell im
  echten `OffscreenCanvas`-Worker verifiziert. Eine dauerhafte
  Worker-Regression gehört sinnvollerweise in die Editor-Tests, sobald dort
  eine Engine-Version mit diesem Fix verwendet wird.
- Der Changelog führt die Änderung unter `4.4.0.19`, ohne die Version in
  `source/pyproject.toml` zu erhöhen. Das folgt dem bisherigen Muster: Der
  Versionssprung erfolgt im separaten Release-Commit.

## Ergebnis

Kein blockierender Befund. Der ursprüngliche Deadlock ist behoben, der
Desktop-Pfad ist durch einen zusätzlichen Test abgesichert. Verbleibende
Risiken betreffen nur die nicht automatisierbare Worker-Reproduktion und die
bewusst beim Host liegende Vollbild-Funktion.
