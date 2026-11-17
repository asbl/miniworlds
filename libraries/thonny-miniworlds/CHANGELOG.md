# Änderungen

## 0.10.0

- Methodenleiste, Python-Aufruf und feste Steuerleiste passen sich schmalen Ansichten an.
- Klassenübersicht in Q1 mit einem Klick ein-/ausblendbar.
- Letzte Methode und Eingaben pro Figur beim Wechsel erhalten.
- Objektkartensuche ab sieben Objekten mit Trefferzahl und Hinweis auf ausgeblendete Auswahl.
- Feldbezogene Eingabefehler und gesperrtes Ausführen bei ungültigen Werten; nächste Schritte unmittelbar erklären.
- Ergebnis mit eindeutigem Empfänger; Änderungen bleiben beim Wechsel zu anderen Figuren dem richtigen Aufruf zugeordnet.
- Wiederholen auf einem anderen Empfänger ohne konkurrierenden Auswahlaufruf; Weltmarkierung nach Rückmeldungen synchronisieren.

## 0.9.0

- Werkstattaufteilung mit Figurenkarten links, Aufruf/Ergebnis in der Mitte und Klassenkarten rechts im Q1-Modus.
- Figurenkarten mit echten Kostümvorschauen, Klasse, Auswahlrahmen und Häkchen; Auswahl auch per Tastatur.
- Klassenkarten zeigen Vererbung, öffnen den bestehenden Konstruktor und führen zur Klassendefinition.
- Suche und Methodengruppen unter Weitere Methoden; Vorhersage, Python-Eingabe, Eigenschaften und Verlauf unter Mehr.
- Einfache Parameter ohne dauerhaften Wert/Objekt-Umschalter; Referenzwahl bei passenden Parametern erhalten.
- Gemeinsamer Bereich für Python-Aufruf und Ausführen, Ergebnis in einem eigenen Rahmen.
- Feste Steuerleiste mit Laden/Zurücksetzen, Stopp, Start/Pause und kurzem Status.
- Vorschauen werden ausschließlich im Backend erzeugt, begrenzt und ohne zusätzliche Abhängigkeiten übertragen.

## 0.8.0

- Breites, angedocktes Objektlabor unter dem Editor statt Reitern in der Seitenleiste.
- Objekte, Methodenformular und unmittelbares Ergebnis gleichzeitig erreichbar.
- Häufige Methoden als Schaltflächen, Suche über Python-Namen und deutsche Beschreibungen sowie Methodengruppen.
- Kompakte Parameterformulare: zusätzliche optionale Parameter und Vorhersage aufklappbar, Eingaben pro Objekt/Methode behalten, Enter zum Ausführen.
- Änderungen direkt beim Ergebnis; Eigenschaften, Verlauf und Fehlerdetails bei Bedarf öffnen.
- Aufrufe direkt in Code übernehmen und letzten Methodenaufruf wiederholen.
- Pause/Weiter als gemeinsamer Schalter; Weltwahl nur bei mehreren Welten.
- Neu laden startet den eigenen Backend-Lauf neu; Stopp bricht auch einen geplanten Neustart ab.
- Q1 zeigt Klassen und vollständige Methodensignaturen; Moduswechsel aktualisiert das laufende Labor.
- Labor nach dem Programmstart sichtbar halten und beim ersten Öffnen ausreichend Platz einräumen.

## 0.7.0

- Objektlabor direkt in die miniworlds-Ansicht eingebettet, ohne Zusatzfenster.
- Kompakte Bereiche Objekte, Aufruf und Log für schmale Seitenleisten.
- Zurück/erneut öffnen erhält die Sitzung ohne erneute Programmausführung.
- Verbindung und Backend-Ereignisbindungen werden beim Entfernen der Ansicht freigegeben.


## 0.6.0

- Drei sichtbare Bereiche Start, Code und Medien statt acht Einträge im Auswahlmenü.
- Objektlabor mit einem Klick öffnen und laden; laufende Sitzung beibehalten.
- E2/Q1, Installation und Interpreter unter Mehr zusammengefasst.
- Projektvorlagen und Beispiele auf einer Startseite; ein gemeinsamer Anlegedialog.
- Code-Hilfe, Ereignisse und Prüfung direkt unter Code; Ziele und Prüfung automatisch laden.
- Galerie/Soundliste mit einer passenden Einfügeaktion statt vieler gleichzeitiger Knöpfe.
- Medien nach Import automatisch auswählen; Zusatzaktionen in einem Dateimenü.
- Hintergrundabfragen beim Schließen zuverlässig abmelden.


## 0.5.0

- Parameterformulare mit Standardwerten, Eingabeprüfung und Python-Vorschau.
- Objektparameter unabhängig vom Methodenempfänger auswählen.
- Dauerhafter Vorher/Nachher-Vergleich der letzten Aktion.
- Programm stoppen und Labor schließen als getrennte Aktionen.
- E2/Q1-Beschriftungen und eingeklappte Objekterzeugung.
- Bildschirmabhängige Fenstergröße und scrollbarere Aktionsansicht.
- Verständliche Fehlerhinweise mit separaten technischen Details.


## 0.4.1

- Experimentiermodus im echten Thonny-CPython-Backend mit unverändertem Schülercode.
- Authentifizierter Kommandokanal und Ausführung zwischen Frames auf dem Welt-Thread.
- Pause/Fortsetzen, Weltwahl, verschachtelte Objektreferenzen und Fehlerberichte.
- Sitzungswechsel bei Stop/Restart und Erkennung geänderter Projektstände.
- Sichere Exportsperre nach Konstruktorfehlern mit möglichen Teiländerungen.
- Benötigt miniworlds ab 4.4.0.12; Integration gegen Thonny 4.1.7 geprüft.

## 0.4.0

- BlueJ-artiges Objektlabor mit Klassendiagramm und Objektbank.
- Anbindung an miniworlds ExperimentSession / pause / invoke / refresh.
- Methoden- und Konstruktoraufrufe, Referenzen und Zustandsvergleich.
- Vorhersagen, Aufrufprotokoll und Übernahme als Programmcode.
- Revisionsprüfung und neue Sitzungsgeneration bei jedem Neustart.


## 0.3.0

- Automatische Versionsabfrage beim Öffnen der Bibliotheksinstallation.
- Anzeige verfügbarer Updates und Python-kompatibler regulärer Versionen.
- Diagnose unvollständiger Bibliotheksdateien und Paketinformationen.
- Reparatur mit vorherigem Download, Sicherung und Wiederherstellung.
- Fehlerhinweise und speicherbares Installationsprotokoll.


## 0.2.0

- Projektbezogener E2/Q1-Modus in `.miniworlds.json`.
- Installationsstatus unterscheidet Plugin-/Bibliotheksumgebung und erklärt PEP 668.
- Statische World-/Actor-Erkennung mit Aliasen und lokaler Vererbung.
- Passende Ereignisauswahl, Navigation zu vorhandenen Ereignissen und Änderungsvorschau.
- Kommentare und Einrückung erhalten; Codeänderungen als ein Rückgängig-Schritt.
- Kontexthilfe mit Typ, Parametern, Rückgabe und schrittweiser Erklärung.
- Vorlagen mit Aufgaben und Kommentaren; Beispiele nach Thema/Schwierigkeit filtern.
- Bildgalerie mit Maßen/Transparenz, vollständige Medienaufrufe und relative Pfade.
- Separate Soundvorschau mit Wiedergabe, Stopp und Lautstärke.
- Fehler-/Hinweisunterscheidung mit Erklärungen und optionalen Korrekturvorschauen.
- Bereichsauswahl für schmale Seitenleisten und scrollbarerer Medienbereich.

## 0.1.0

Erste Version mit Installationshilfe, E2/Q1-Hilfen, Vorlagen, Ereignis-Assistent,
Beispielen, Medienimport und grundlegender Codeprüfung.
