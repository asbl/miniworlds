# UI-Review und Gestaltungsvorschlag

Stand: 13. November 2026, Plugin 0.2.0. Dies ist ein überprüfbarer Entwurf;
die laufende Oberfläche wurde in diesem Arbeitsschritt nicht verändert.

[Visueller Entwurf](ui-concept.png) · [Editierbares SVG](ui-concept.svg)

## Befund

Die Funktionen sind vorhanden, aber ihre Bedienung folgt noch stark der
technischen Implementierung. Für den Unterricht sollte eine Frage wie
„Wie reagiert meine Figur auf eine Taste?“ den Ablauf bestimmen.

Die Seitenleiste wurde in einer frischen Thonny-Instanz gemessen: zunächst
184 Pixel breit. Zusätzlich wurden die echten Tk-Widgets isoliert unter
Xvfb bei 184 und 360 Pixeln dargestellt. Die dabei verwendeten Beispieldaten
enthalten keine Schülerdateien. Schrift und Theme können auf anderen Systemen
abweichen; die strukturellen Platzprobleme bleiben nachvollziehbar.

- [Ereignis-Assistent bei 184 Pixeln](current-events-184.png): Der Modus,
  Installationsknopf und Einfügeknopf werden abgeschnitten. Der lange
  Einleitungstext belegt viel Höhe. Python-Code wird mitten in Bezeichnern
  umgebrochen. Ziel- und Ereignisauswahl besitzen keine eigenen Feldlabels.
- [Medien bei 360 Pixeln](current-media-360.png): Bereits die Tabellenköpfe
  sind teilweise abgeschnitten. Dieselben Bilder erscheinen als Tabellenzeile
  und Miniatur. Für eine Bildauswahl werden zugleich Sound-, Pfad-, Kostüm-
  und Hintergrundaktionen gezeigt. Mehrere Scrollbereiche erschweren die
  Orientierung. „Extern öffnen“ und „Entfernen“ liegen weit unten.
- Über alle Bereiche haben viele Schaltflächen dasselbe visuelle Gewicht.
  Die dauerhaft hervorgehobene Installation lenkt von der Programmieraufgabe ab.
- Erklärung, Parameter und Code erscheinen im selben unstrukturierten
  Textfeld. „Nächster Schritt: Hinweis / Beispiel“ verrät nicht eindeutig,
  was der nächste Klick öffnet.
- Eine rohe Unified-Diff-Vorschau verlangt Kenntnisse über `@@`, `+` und `-`,
  die für das Lernen von Python nicht vorausgesetzt werden sollten.

Diese Aussagen stammen aus der Inspektion der Oberfläche und des Codes,
nicht aus einer bereits durchgeführten Studie mit Schülerinnen und Schülern.

## Gestaltungsziel

Eine ruhige, gut lesbare Lernhilfe mit klaren Schritten. Keine kindliche
Spieloberfläche und keine Bewertung der Lernenden. Bekannte Python- und
miniworlds-Begriffe bleiben sichtbar, werden aber kurz erklärt.

Pro Bereich gibt es eine erkennbare Hauptaktion. Seltene und technische
Aktionen bleiben erreichbar, beanspruchen aber nicht ständig Platz.

## Navigation und Platz

1. Kompakter Kopf mit Projektdatei, Modusbadge „Objekte · E2“ bzw.
   „Klassen · Q1“ und einem kurzen Status wie „Bereit“ oder „Einrichtung nötig“.
   Moduswechsel und Installationsdetails liegen unter „Projekteinstellungen“.
   Bei fehlender Bibliothek erscheint dort eine konkrete Installationsaktion.
2. Fünf Arbeitsbereiche: **Start**, **Ereignisse**, **Bilder & Sounds**,
   **Hilfe**, **Prüfen**. Start bündelt neue Projekte und Beispiele.
   Installation bleibt über Einstellungen erreichbar.
3. Die Bereichsauswahl trägt das sichtbare Label „Bereich“. So ist ihre
   Funktion ohne Ausprobieren erkennbar.
4. Breitenentscheidung anhand des verfügbaren Inhaltsraums und der
   Schriftgröße: ab ungefähr 320 logischen Pixeln kann der Assistent in der
   Seitenleiste arbeiten. Darunter zeigt er eine kompakte Zusammenfassung
   und „Assistent öffnen …“ für einen größeren, skalierbaren Dialog.
   Der genaue Grenzwert muss unter unterschiedlichen Skalierungen geprüft werden.
5. Auswahl und Entwürfe bleiben beim Öffnen/Schließen des Dialogs erhalten.
   Niemand muss die Seitenleiste zum Lesen von Code selbst passend ziehen.

## Ereignisse: eine verständliche Reihenfolge

**Wer reagiert? → Wann? → Was wird eingefügt?**

- E2 zeigt `player · Figur (Actor)` oder `world · Welt (World)`.
  Q1 zeigt `Player · Klasse von Actor` beziehungsweise `MyWorld · Klasse von World`.
- Ereignisse erhalten verständliche Namen mit API-Begriff als Zusatz:
  „In jedem Bild (act)“, „Taste einmal drücken (on_key_down)“ und
  „Taste halten (on_key_pressed)“. Der Unterschied zwischen einmaliger und
  wiederholter Ausführung bleibt ausdrücklich erklärt.
- Nicht automatisch die erste World als Ziel vorwählen. Ein erkennbarer
  Bezug am Cursor oder das zuletzt gültige Ziel hat Vorrang; sonst wählt
  die Person ihr Ziel ausdrücklich aus.
- Eine kurze Zusammenfassung bestätigt die Auswahl, beispielsweise
  „Solange du die rechte Pfeiltaste hältst, reagiert player in jedem Bild.“
- Code ist zunächst einklappbar. In der großen Vorschau bleibt Python
  ungebrochen und horizontal scrollbar; Fließtext bricht dagegen normal um.
- Hauptaktion: „In meinen Code einfügen …“. Bei einem vorhandenen Ereignis
  ändert sie sich zu „Im Code zeigen“. Der Knopf beschreibt immer eine Aktion.
- Wenn kein Ziel gefunden wird: „Noch keine Figur oder Welt erkannt“ mit
  „Beispiel öffnen“ und einem aufklappbaren technischen Hinweis. Ein
  Syntaxproblem erhält einen anderen Hinweis als ein leeres Programm.

## Medien: Auswahl bestimmt die Aktionen

- Zwischen **Bilder** und **Sounds** wechseln. Eine Galerie für Bilder;
  Dateiname und Maße stehen direkt an der Miniatur. Transparenz wird durch
  ein Schachbrett und zusätzlich durch Text erkennbar.
- Eine kompakte Dateiliste ist eine alternative Ansicht, nicht eine zweite
  Darstellung derselben Auswahl zur gleichen Zeit.
- Nach Bildauswahl ein Feld „Verwenden für“ anbieten. Das erkannte Ziel
  bestimmt „Als Kostüm verwenden …“ oder „Als Hintergrund verwenden …“.
  Vor dem Einfügen bleibt die Codevorschau erhalten.
- Nach Soundauswahl Wiedergabe/Stopp, Dateiname und einen beschrifteten
  Lautstärkeregler mit Zahlenwert anzeigen. Hauptaktion: „Sound im Code verwenden …“.
- „Pfad kopieren“, „Extern öffnen“ und „Datei entfernen“ in einem
  beschrifteten Menü „Weitere Aktionen“. Löschen bleibt mit Rückfrage versehen.
- Leerer Zustand: „Hier sind noch keine Bilder“ und „Bilder hinzufügen …“.
  Nicht erst eine leere Tabelle mit vielen unbrauchbaren Knöpfen zeigen.
- Ein Scrollbereich pro Seite. Aktionen für die gewählte Datei bleiben
  möglichst im sichtbaren unteren Bereich.

## Hilfe, Projekte und Beispiele

- Erklärung, Hinweis und Code als getrennte Abschnitte gestalten.
  Fließtext verwendet die normale UI-Schrift, Code die Editor-Schrift.
- Der nächste Knopf heißt zunächst „Hinweis zeigen“, anschließend
  „Beispielcode zeigen“. Der eigene Lernfortschritt wird nicht mit Punkten
  oder künstlichen Erfolgsanzeigen bewertet.
- Parameter und Rückgabe unter „Genauer erklärt“ aufklappbar machen.
  Kurze Grundbedeutung und ein konkreter Zusammenhang stehen davor.
- Start bietet zwei klare Entscheidungen: „Eigenes Projekt starten“ und
  „Mit einem Beispiel üben“. Beispiele zeigen Thema, Schwierigkeit,
  erwartetes Verhalten und eine Aufgabe vor dem Code.
- Such-/Filterfelder werden beschriftet. Kein Treffer führt zu
  „Keine passenden Beispiele – Filter zurücksetzen“.
- Der Modus ist einmal im Kopf sichtbar und wird nicht in jedem Textblock
  wiederholt. Inhaltlich bleiben E2 und Q1 konsequent verschieden.

## Codeprüfung und Änderungsvorschau

- Oben die Zusammenfassung „1 Fehler · 2 Hinweise“. Darunter kompakte
  Ergebniskarten mit kurzer Überschrift, Zeilennummer und Erklärung.
- Beispiel: „Ereignisparameter fehlt“ → „on_key_down benötigt self und einen
  Parameter für die Tasten.“ Aktionen: „Zeile 12 zeigen“ und gegebenenfalls
  „Korrektur ansehen …“.
- Kein Ergebnis bedeutet „Bei dieser Prüfung keine Probleme gefunden“ mit
  einer kleinen Erläuterung zum Prüfumfang. Keine pauschale Behauptung,
  das ganze Programm sei korrekt.
- In der Änderungsvorschau „Vorher“ und „Nachher“ zeigen, mit Zeilennummern,
  Syntaxfarben und ausdrücklich markierten neuen/geänderten Zeilen.
  Bei schmalen Fenstern untereinander; sonst nebeneinander.
- Rohes Unified-Diff optional unter „Technische Ansicht“ belassen.
  Nicht als erste Darstellung anbieten.
- Hauptaktion „Änderung übernehmen“, daneben „Zurück“. Die bestehenden
  Schutzmechanismen für veralteten Code, geschlossene Dateien und einen
  einzelnen Rückgängig-Schritt bleiben erhalten.

## Visuelle Regeln und Zugänglichkeit

- Ein Akzent für Hauptaktionen, neutrale Flächen für Informationen und
  großzügiger Abstand zwischen zusammengehörigen Gruppen. Eine ruhige
  grünblaue Variante ist im Entwurf gezeigt; sie ist noch keine festgelegte
  Markenfarbe. Keine Sammlung verschiedenfarbiger Funktionsbuttons.
- Farben aus dem aktiven Thonny-Theme ableiten und nur Plugin-eigene
  ttk-Stile verwenden. Helles und dunkles Theme ausdrücklich prüfen.
- Gleiche Abstandsabstufungen, beispielsweise 8/12/16 logische Pixel,
  und gut erreichbare Buttons von ungefähr 40 Pixeln Höhe bei Standardskalierung.
  Schrift und Maße müssen mit der System-/Thonny-Skalierung wachsen.
- Jedes Auswahlfeld erhält ein dauerhaftes Label. Sichtbarer Tastaturfokus,
  sinnvolle Tab-Reihenfolge und benannte Aktionen sind verbindlich.
- Status wird immer mit Text vermittelt, zusätzlich gegebenenfalls durch
  Symbol und Farbe. Die W3C-Erläuterungen zu [klaren Labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html)
  und [Farbe als zusätzlichem Signal](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)
  dienen hier als Gestaltungsgrundlage. Sie sind Web-Richtlinien und belegen
  keine vollständige Barrierefreiheit einer Tk-Anwendung.

## Umsetzung in drei Schritten

| Reihenfolge | Umfang | Hauptstellen im bisherigen Code |
|---|---|---|
| 1 | Kompakter Kopf, beschriftete Felder, klare Hauptaktionen, responsive Dialogansicht, getrennte Text-/Codeansicht | `MiniworldsView.__init__`, `combo`, `output`, `build_events`, `review_edit` |
| 2 | Mediengalerie und Dateiliste als Alternativen; Auswahl steuert Aktionen; Sounds als eigener Bereich | `build_media`, `media_selected`, `resize_gallery`, `insert_media_call` |
| 3 | Startbereich, Hilfekarten und Prüfkarten; leere Zustände und präzisere Texte | `build_help`, `build_templates`, `build_examples`, `build_checks` |

Die vorhandene AST-Erkennung, Projektdateien, Dateioperationen, Audioansteuerung
und Codeänderungslogik können weiterverwendet werden. Die Umgestaltung
betrifft primär Darstellung und Interaktionsabläufe. Der Live-Weltinspektor
bleibt ein eigener späterer Schritt.

## Abnahme und Schülerfeedback

- Bei 184, 320 und 480 Pixeln Breite sowie 100/150/200 % Skalierung prüfen:
  keine abgeschnittene Hauptaktion, alle Bereiche erreichbar, Python bleibt
  in der großen Ansicht lesbar, Auswahl bleibt beim Größenwechsel erhalten.
- Helles/dunkles Theme und vollständige Bedienung per Tastatur prüfen.
- Automatisch prüfen: Ziel-/Dateiauswahl steuert Aktionen, leere Zustände,
  vorhandene Ereignisse, erhaltene Auswahl, veraltete Vorschauen und Undo.
- Vor einer Festlegung mit einigen Lernenden aus E2 und Q1 beobachten:
  ein Projekt öffnen, Tastaturereignis ergänzen, Bild als Kostüm verwenden
  und einen Signaturfehler verstehen. Notieren, welche Beschriftungen und
  Schritte ohne zusätzliche Erklärung funktionieren.
- Die erwartete Verbesserung ist eine Gestaltungshypothese. Erfolg wird an
  verständlichen Abläufen und beobachteten Aufgabenlösungen beurteilt,
  nicht allein an einem gefälligeren Screenshot.
