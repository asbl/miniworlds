# miniworlds Backend für den Unterricht

Einfaches Backend für den schulischen Betrieb von miniworlds: Admin vergibt Lehrercodes,
Lehrer erzeugen Projekt-Codes und Aufgaben, Schüler arbeiten code-basiert an ihren
Programmen, Medien und Abgaben. Klassen und mehrere Projekte je Code-Arbeitsbereich
werden ohne Personenlisten verwaltet. Es gibt keine Lehrer-/Schülerfeedback-Felder.

## Pyodide-Player

- `/play` und `/player` verwenden dieselbe Arbeitsfläche: Aufgaben, Quellcode mit Syntaxfarben,
  Start/Stop, Medien und ZIP-Download. `/player?public=<slug>` zeigt einen öffentlichen Snapshot.
- Lehrervorschau: `/player?teacher=<pid>`; eingefrorene Abgabe:
  `/player?submission=<sid>&version=<version>`. Beide sind nur für die besitzende Lehrkraft zugänglich.
- Schülerprogramme laufen in einem Worker in `/runner`, einem Sandbox-Iframe mit opakem Ursprung
  (`sandbox="allow-scripts"`, ohne `allow-same-origin`). Der Worker erhält nur Code, Datenbank,
  Medien und das Wheel; niemals Cookies, Schüler-Tokens oder eine allgemeine API-Brücke.
  CSP erlaubt Netzwerkzugriffe der Laufzeit ausschließlich auf die konfigurierte Pyodide-CDN.
  Stoppen verwirft die gesamte Laufzeit, auch bei einer Python-Endlosschleife.
  Grafik und Tastatur/Maus werden über OffscreenCanvas und SDL-Ereignisse vermittelt.
  Ton/Musik werden über eine auf hochgeladene Audio-Blobs beschränkte Brücke in der Sandbox
  abgespielt. Falls der Browser Autoplay blockiert, erscheint dort „Ton aktivieren“.
  Die miniworlds-Sound-/Musik-API wird an den Browser vermittelt; direkte
  `pygame.mixer`-Aufrufe sind im Worker nicht unterstützt.
- Das Backend serviert das miniworlds-Wheel unter `/wheel/miniworlds.whl`.
  **Wheel bauen** (bei Engine-Updates neu bauen):
  ```sh
  cd source && ../venv/bin/pip wheel . --no-deps --no-build-isolation -w /tmp/w && \
    cp /tmp/w/miniworlds-*.whl ../backend/app/static/wheel/miniworlds.whl
  ```
  (Pfad konfigurierbar: `MINIWORLDS_WHEEL_PATH`; Pyodide-CDN: `PYODIDE_BASE`, Default jsdelivr v0.29.3.)
- Nur die isolierte Laufzeit erlaubt zusätzlich `unsafe-eval`, das der dynamische SDL-Linker benötigt.
  Die angemeldete Oberfläche erlaubt dies nicht.
- Speichern: `PUT /api/play/save` mit `source`, `db` (base64) und `base_revision` aus
  `GET /api/play/project`. Die Antwort enthält die nächste `revision`. Ein veralteter Stand
  liefert `409`, statt neuere Arbeit zu überschreiben. Ohne `base_revision` ist ausschließlich
  Revision 0 adressierbar (Erstspeicherung/Kompatibilität).
- Automatisches Speichern nach einer Eingabepause; nicht gespeicherte Entwürfe bleiben im
  `sessionStorage` des jeweiligen Tabs, bis sie gespeichert, verworfen oder beim Abmelden gelöscht
  werden. Sie überleben ein Neuladen, nicht zuverlässig das Schließen des Tabs. Es gibt keine
  zusätzliche serverseitige Entwurfssammlung. Konflikte erfordern Herunterladen/Vergleichen
  bzw. explizites Laden des Serverstands. Medienaktionen ersetzen den Editor nicht.
- Datenbanken werden während laufender Programme regelmäßig aus dem Worker übernommen.
  Beim erzwungenen Stoppen ist der zuletzt übermittelte Datenbankstand verfügbar.
- **Versionen (git):** Jeder Save (und jeder Medien-Upload/Löschung) erzeugt serverseitig einen
  git-Commit im Repo des Projekts unter `MINIWORLDS_GIT_ROOT/project-<id>/` (Arbeitsbaum:
  `main.py`, `save.db`, `media/`). Optional mit Kommentar: `message` im Save-Body.
  Schüler-API: `GET /api/play/history` (Commit-Liste), `GET /api/play/history/{hash}` (Diff),
  `POST /api/play/restore/{hash}?base_revision=<n>` (Code/Datenbank einer alten Version übernehmen; erzeugt selbst
  wieder einen Commit). UI unter „Versionen und Git-Remote“. Medien werden beim Wiederherstellen aus Git nicht zurückgesetzt. Ohne git auf dem Server
  bleibt Speichern voll funktionsfähig (`available: false` im History-Response).
- **Remotes (Push/Pull, z. B. GitHub):** Pro Projekt ein Remote `origin` (URL + optionales Token).
  Das Token wird Fernet-verschlüsselt in `project_remotes` gespeichert, nie an Clients
  zurückgegeben und per `GIT_ASKPASS` übergeben (nie in argv oder `.git/config`). URL-Validierung:
  nur `https://`/`git@…`, keine Credentials in der URL, private IPs blockiert, optional
  Host-Whitelist via `GIT_ALLOWED_HOSTS` (z. B. `github.com,git.schule.de`).
  - Schüler: `GET/PUT/DELETE /api/play/remote`, `POST /api/play/push`, `POST /api/play/pull?base_revision=<n>`
    (Pull übernimmt den neuen HEAD als Save, Quota-Rollback bei Überschreitung; `read_only`
    blockiert Pull und Remote-Änderungen, Push bleibt erlaubt). UI im Player unter „Remote".
  - Lehrer (z. B. Klassen-Repo): `GET/PUT/DELETE /api/teacher/projects/{pid}/remote` —
    Schüler pushen dann ohne eigenes Token per Klick.
  - GitHub-Beispiel: Remote `https://github.com/<org>/<repo>.git`, Token = PAT (fine-grained,
    repo-Recht). Klassiker für Abgaben: Lehrer legt Klassen-Repo + Deploy-Token an.

## Stack

FastAPI + SQLite (SQLAlchemy) + Jinja2-Dashboards + argon2 (Passwörter) +
Fernet (Codes verschlüsselt at rest). Schüler-Authentifizierung: signiertes
Bearer-Token, an den Code-Hash gebunden (Code-Wechsel invalidiert sofort).

## Start (lokal)

```sh
pip install -r requirements.txt
# Einmalig anlegen; die Datei beim nächsten Start wiederverwenden:
python - <<'PY'
import secrets
from pathlib import Path
path = Path("backend.env")
with path.open("x") as config:
    config.write("SECRET_KEY=" + secrets.token_urlsafe(32) + "\n")
path.chmod(0o600)
PY
set -a
. ./backend.env
set +a
ADMIN_EMAIL=admin@schule.de ADMIN_PASSWORD=geheim123 \
python -m uvicorn app.main:create_app --factory --port 8000
```

Dann: `http://localhost:8000/admin/login` (Seed-Admin aus `ADMIN_EMAIL`/`ADMIN_PASSWORD`),
`http://localhost:8000/teacher` (Login bzw. `/teacher/claim` mit Lehrercode),
`http://localhost:8000/play` (Schüler, Code eingeben).

## Docker

```sh
docker build -f backend/Dockerfile -t miniworlds-backend .
docker run -p 8000:8000 -v mwdata:/data \
  -e SECRET_KEY=... -e ADMIN_EMAIL=... -e ADMIN_PASSWORD=... \
  -e BASE_URL=https://miniworlds.example.de -e COOKIE_SECURE=1 \
  miniworlds-backend
```

Hinter einem Reverse Proxy (Caddy/nginx) terminieren lassen; `COOKIE_SECURE=1` setzt
Secure-Cookies + HSTS.
Der Build wird vom Repository-Stamm gestartet und baut das Player-Wheel aus `source/` mit.
Der Container läuft ohne Root-Rechte; Anwendung und Bibliotheken können zur Laufzeit
schreibgeschützt bleiben. Schreibzugriffe benötigen nur `/data` und `/tmp`.

`deploy/compose.yml` enthält die Produktionskonfiguration für
`https://backend.editor.opencoding.de` am vorhandenen Traefik-Netz `traefik_default`.
Im Deployment-Verzeichnis werden `compose.yml`, eine geschützte `backend.env` mit dauerhaftem
Schlüssel und Admin-Seed sowie `release.env` mit `BACKEND_IMAGE=miniworlds-backend:<Commit>` benötigt.
Optional wählt `BACKEND_RUNTIME` eine bereits konfigurierte OCI-Runtime. Auf dem Zielserver
ist derzeit `php-security-compat` nötig: Sie verwendet den dort vorhandenen kompatiblen
containerd-Shim, ohne den Docker-Daemon und andere Dienste neu starten zu müssen.
`docker compose --env-file release.env -f compose.yml up -d backend` startet das Release;
`docker compose --env-file release.env -f compose.yml run --rm backup` erstellt eine geprüfte Sicherung.
Die User-Systemd-Dateien in `deploy/` aktivieren tägliche Sicherungen bei Installation unter
`~/projects/miniworlds-backend`; dafür muss der User-Manager dauerhaft laufen (Linger).

## Umgebungsvariablen

| Variable | Default | Bedeutung |
|---|---|---|
| `SECRET_KEY` | erforderlich | Dauerhafter Schlüssel für Codes/Remote-Tokens; fehlender oder zur Datenbank unpassender Schlüssel verhindert den Start |
| `DATABASE_URL` | `sqlite:///./data/app.db` | SQLAlchemy-URL |
| `MEDIA_ROOT` | `./data/media` | Ablage für Medien (Phase 2) |
| `MINIWORLDS_GIT_ROOT` | `./data/git` | git-Repos pro Projekt (Versionsverlauf im Player) |
| `GIT_ALLOWED_HOSTS` | `github.com,gitlab.com,codeberg.org` | Exakte, kommagetrennte Hosts; Subdomains separat angeben. Interne IPs einschließlich DNS-Auflösung werden gesperrt, HTTPS nur auf Port 443. Leer sperrt alle Remotes. `local` erlaubt Dateipfade ausschließlich für Tests. |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | — | Seed-Admin (nur beim ersten Start ohne Admin) |
| `BASE_URL` | `http://localhost:8000` | für Links/Mails |
| `SESSION_HOURS` / `STUDENT_TOKEN_HOURS` | 12 | Lebensdauer Session / Schüler-Token |
| `INVITE_EXPIRE_DAYS` | 30 | Ablauf Lehrercodes (0 = nie) |
| `DEFAULT_QUOTA_BYTES` | 10 MB | Quota neuer Projekt-Codes |
| `TEACHER_QUOTA_CAP` | 50 MB | Admin-Cap, bis zu dem Lehrer Quotas erhöhen dürfen |
| `COOKIE_SECURE` | `0` | `1` = Secure-Cookies + HSTS (Produktion) |
| `MINIWORLDS_WHEEL_PATH` | `app/static/wheel/miniworlds.whl` | Wheel für den Pyodide-Player |
| `PYODIDE_BASE` | jsdelivr v0.29.3 | Pyodide-CDN-Basis |
| `RETENTION_READ_ONLY_MONTHS` | 24 | inaktive Projekte → read-only |
| `RETENTION_DELETE_MONTHS` | 36 | inaktive Projekte → Löschung (kaskadierend) |
| `AUDIT_RETENTION_DAYS` | 30 | Technische Protokolle danach löschen; ältere Einträge werden sofort nicht mehr angezeigt |
| `HISTORY_MAX_BYTES` | 100 MiB | Git-Verwaltungsdaten je Projekt; mindestens 65536 Bytes |
| `SUBMISSION_MAX_VERSIONS` | 10 | Höchstens so viele eingereichte Fassungen je Aufgabe aufbewahren |
| `SUBMISSION_MAX_BYTES` | 100 MiB | Gesamtbudget der Abgabeversionen je Projekt (komprimierte Snapshots plus Checkboxwerte) |
| `MAX_REQUEST_BYTES` | 64 MiB | Maximale Save-Anfrage; sonstige API-Anfragen höchstens 1 MiB, Medien 25 MiB plus Formular-Metadaten |
| `FRONTEND_ORIGINS` | `https://editor.opencoding.de` | Kommagetrennte exakte Editor-Origins für CORS, ohne Cookie-Freigabe |
| `CODE_READONLY_DAYS` | 365 | Standard für neue Projekte: Code läuft so viele Tage nach Beginn des Schreibschutzes ab; pro Projekt änderbar |

## Eigenständiger Editor und Projektzugänge

Der statische Editor wird separat auf `editor.opencoding.de` betrieben. Seine optionale öffentliche
`config.json` enthält `backendUrl`; ohne diese Einstellung funktioniert er mit lokalem Speicher und
Import/Export. Python, Miniworlds-Wheel und Laufzeit benötigen keine FastAPI-Anmeldung. Lehrer- und
Adminverwaltung bleiben auf der Backend-Domain. Der Editor verwendet ausschließlich Schüler-Bearer-Tokens,
keine Lehrer-Cookies. Bei einem anderen Frontend-Host `FRONTEND_ORIGINS` und dessen CSP passend konfigurieren.

Projekt-Codes öffnen weiterhin direkt Projekte. Die Lehrkraft stellt unter „Zugang einstellen“ ein:
optionales Bearbeitungsende, Code-Gültigkeit nach Schreibschutz (Standard 365 Tage, leer unbegrenzt),
und optional ein festes Ablaufdatum. Das frühere Ablaufdatum gilt. Ein festes Bearbeitungsende ersetzt für
dieses Projekt den jährlichen Standard-Schreibschutz am 31.07. Ein abgelaufener Code sperrt auch bereits
ausgestellte Tokens und Projektwechsel zu diesem Projekt. Die Aufbewahrungs-/Löschfristen bleiben eigenständige
Regeln: Eine längere Code-Gültigkeit verlängert sie nicht. Bei der Migration beginnt für bereits
schreibgeschützte Projekte ohne bekannten Zeitpunkt die relative Zugangsfrist mit dem Migrationszeitpunkt.

„Einmalig eine Kopie erstellen“ erzeugt pro Code genau eine Kopie eines Startprojekts in dessen Klasse.
Die Einlösung wird über Prozesse hinweg exklusiv verarbeitet. Die Antwort enthält einen neuen persönlichen
Projekt-Code; der Vorlagencode verfällt unmittelbar. Passwörter, Tokens, Antworten und Abgaben des Originals
werden nicht übernommen. Verfügbare/eingelöste Vorlagencodes sind im Lehrer-Dashboard sichtbar und löschbar.
Kopien erhalten die Standard-Zugangsfrist; diese lässt sich anschließend wie bei normalen Projekten ändern.

Schüler können einen Passwortschutz setzen/ändern (`PUT /api/play/password`, mindestens 12 Zeichen,
aktuelles Passwort bei Änderungen erforderlich). Gespeichert wird ein Argon2-Hash im namenlosen Arbeitsbereich.
Passwortänderungen und Lehrer-Resets widerrufen alle Arbeitsbereichs-Tokens. Die Lehrkraft kann das Passwort
entfernen (`DELETE /api/teacher/projects/{id}/password`), es aber niemals auslesen. Code-/Passwortversuche
werden zusätzlich zur IP-Begrenzung je Code auf fünf Fehlversuche pro fünf Minuten begrenzt; diese kurzlebigen
Zähler überleben Worker-/App-Neustarts und werden anschließend gelöscht. Keine Schülerkonten oder E-Mails.

Mehrdateiprojekte verwenden zusätzlich `files` im Save-Payload (relative Pfade → Base64). Pfade und Inhalte
werden validiert; absolute Pfade, Traversal, Git-Verwaltungsdateien und Datei-/Ordnerkollisionen sind gesperrt.
Die Dateiliste bleibt bei alten Single-File-Speicheranfragen erhalten. Kopien, Abgaben, Versionswiederherstellung
und ZIP-Downloads erhalten alle Dateien. Der Editor hält fehlgeschlagene Speicherungen lokal zurück und
überschreibt bei Versionskonflikten keinen Serverstand. Checkbox-Entwürfe bleiben ebenfalls lokal erhalten;
freie Antworttexte oder Feedback sind weiterhin ausgeschlossen.

## Rollen & Rechte

- **Admin** (`/admin`): Lehrercodes erzeugen/löschen, Quota-Cap + Default-Quota setzen,
  Lehrer sperren/löschen, globales Audit.
- **Lehrer** (`/teacher`): Projekt-Codes erzeugen/anzeigen/ändern/löschen, Quota (≤ Cap),
  Klassen/Schuljahre gruppieren und archivieren, Sammelaktionen für Schreibschutz und Zuordnung,
  Aufgaben (Informationstext/Checkbox) erstellen/bearbeiten/sortieren und Codes oder Klassen
  zuweisen. Abgaben nach fehlend/abgegeben/erledigt filtern, ansehen, herunterladen und wieder öffnen.
  Keine freien Lehrernotizen oder Rückmeldungen.
- **Schüler** (`/play`): nur mit Code; Speichern/Laden/Download, Medien-Upload
  (PNG/JPG/GIF/WEBP/MP3/OGG/WAV/MP4/WEBM, Magic-Bytes-Prüfung, max 25 MB/Datei) mit
  Lizenz/Quelle pro Asset, Aufgaben bearbeiten und abgeben (Abgabe friert Version ein;
  Lehrer kann wieder öffnen), bis zu 30 Projekte im gleichen Code-Arbeitsbereich, Freigabe-Antrag mit Versicherungserklärung stellen.
  Read-Only sperrt Speichern, Medien und Abgaben; archivierte Klassen sperren zusätzlich neue
  Projekte. Das Reaktivieren einer Klasse hebt vorherige manuelle Projektsperren nicht auf.
- **Vollständige Abgaben:** Jede neue Einreichung friert Code, Datenbank, Medien samt Lizenzen,
  Aufgabenfassung und Checkbox-Antworten ein. Snapshots liegen komprimiert in der Datenbank und ändern sich
  durch spätere Bearbeitung oder Medienlöschung nicht. Alte Einreichungen erhalten keinen
  nachträglich erfundenen Projektstand. Historische Abgaben zählen nicht erneut zur Arbeitsquota;
  ihre Größe muss bei der Server-/Backupspeicherplanung berücksichtigt werden.
  Automatisch gespeicherte Checkbox-Antworten behalten nur den aktuellen Entwurf, eingereichte Fassungen
  werden nach den oben konfigurierten Grenzen aufbewahrt. Ältere Fassungen werden zuerst entfernt;
  die letzte eingereichte Fassung jeder Aufgabe bleibt erhalten. Falls diese geschützten Fassungen
  zusammen das Budget überschreiten würden, wird die neue Abgabe mit HTTP 413 zurückgewiesen,
  ohne den bisherigen Stand zu verändern. Bestehende geschützte Altbestände werden nicht gelöscht.
- **ZIP-Download:** `GET /api/play/download` liefert `main.py`, optional `save.db`, Mediendateien,
  `licenses.json` und `project.json`. Dateinamen entsprechen denen in der Laufzeit.
  Downloads und Mediendateien werden in der Schüleroberfläche authentifiziert abgerufen.
- **Klassenstart:** Erfolgreiche Code-Anmeldungen zählen nicht als Fehlversuche. Pro IP sind
  maximal 600 Requests/Minute möglich; nach 20 ungültigen Codes pro Minute greift die Sperre.
  Beim Erzeugen der Codes kann ein eigenes Projekt als Startprojekt ausgewählt werden.
  `POST /api/teacher/projects` akzeptiert dafür `template_project_id` neben `course_id` und `count`.
  Kopiert werden Programm, Medien samt Lizenzangaben und Aufgabenstellungen. Aufgaben einer
  anderen Klasse werden für die Zielklasse kopiert. Antworten, Abgaben, Freigaben und
  Git-Zugangstokens werden niemals übertragen; alle Kopien bleiben eigenständig.
- **Code erneuern:** Weil ein Code alle Projekte seines Arbeitsbereichs öffnet, werden beim
  Erneuern sämtliche Projektcodes und Tokens dieses Arbeitsbereichs ungültig.
- **Öffentlich teilen:** Lehrer gibt Antrag frei → Snapshot (Save + Medien + Lizenzen,
  Dateien kopiert) unter `/p/<slug>` öffentlich, Melden-Button, Widerruf jederzeit.
  Änderungen am Original ändern den Snapshot nicht.
- **Lehrer „sofort starten":** `POST /api/teacher/projects/{id}/fork` kopiert das
  Schüler-Projekt (Save + Medien) als eigene Kopie.
- **Aufgaben-Galerie (v4):** Lehrer veröffentlicht Aufgaben-Snapshots
  (`POST /api/teacher/tasks/{id}/publish`), andere Lehrer kopieren sie
  (`POST /api/teacher/gallery/{id}/copy`) — ohne Abgaben. Admin kann verbergen.
- **Excel/CSV-Export:** `GET /api/teacher/projects.xlsx|.csv` (nur Codes). Die
  Code↔Name-Zuordnung passiert **ausschließlich clientseitig** im Lehrer-Dashboard
  (vendored SheetJS, Datei wird nie hochgeladen).
- **Pyodide-Player:** `/player` startet das Projekt im Browser (siehe oben).
- **Retention:** `maybe_retention` (Startup + alle 30 Min.): Projekte ohne Save seit
  `RETENTION_READ_ONLY_MONTHS` → read-only, seit `RETENTION_DELETE_MONTHS` → kaskadierende
  Löschung; beides mit Audit-Eintrag.
- **DSGVO-Selbstauskunft:** `GET /api/teacher/export` (JSON aller eigenen Daten).
- **Öffentliche Aufgaben-Lese-Seite:** `/t/<slug>` (ohne Login, nur veröffentlichte).

Am **31.07. jedes Jahres** werden alle Projekte auf Read-Only gesetzt (Startup + Lazy-Check
alle 30 Min., Audit-Eintrag); Lehrer können Projekte gesammelt reaktivieren.

## Tests

```sh
cd backend
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=<venv-site-packages> python -m pytest tests -q
```

API-Regressionstests: Auth/Claim/CSRF, Projekte (Quota, Cap, Read-Only, Code-Regeneration, Isolation,
Löschen), Aufgaben (CRUD, Zuweisung, Abgabe/Versionen, Reopen, Template-Auto-Zuweisung,
Quota für Antworten), Jahreswechsel, Retention (read-only→Löschung), Security-Units, Medien
(Upload/Validierung/Quota/Serve), Freigabe-Workflow (Snapshot-Unveränderlichkeit,
Slug-Konflikte, Widerruf, Report, Isolation), Fork, Excel-Export, öffentliche Aufgaben
(Publish/Galerie/Kopie/Admin-Hide/„/t/<slug>“-Seite, keine Abgaben im Snapshot),
Player-Config/Wheel, DSGVO-Export, Klassenisolation/Archivierung, 30 Anmeldungen über dieselbe IP,
konkurrierende Speicherzugriffe, ZIP-Inhalte, unveränderliche vollständige Abgaben, Notizbereinigung
und die Entfernung freier Textantworten aus historischen Abgaben/Galerievorlagen.
Zusätzliche Tests prüfen vollständige Dateilöschung, Protokollisolation/-migration,
Schlüsselkontrolle über Neustarts, DNS-basierte Git-Sperren, Hintergrundwartung,
Startprojekte, begrenzte Versionsarchive und Wiederherstellung signierter Sicherungen.
`.github/workflows/backend-tests.yml` baut das Wheel und führt API- sowie Browserprüfungen
bei Änderungen und zusätzlich wöchentlich aus, einschließlich einer Wiederherstellung aus einer Testsicherung.

Browserprüfung gegen eine **separate Testinstanz** mit Test-Admin und gebautem Wheel:

```sh
MINIWORLDS_TEST_URL=http://127.0.0.1:8000 \
MINIWORLDS_TEST_ADMIN=admin@example.test MINIWORLDS_TEST_PASSWORD=... \
MINIWORLDS_RUNTIME_TEST=1 node tests/browser-workflow.cjs
```

Benötigt das Node-Paket `playwright` und Chromium (`CHROMIUM_PATH` optional). Ohne
`MINIWORLDS_RUNTIME_TEST=1` läuft der Unterrichtsablauf ohne CDN-/Grafikprüfung.
Der Test legt ausschließlich auf der Testinstanz Lehrkonto, Klasse, Projekte und Aufgaben an.
Bei wiederholtem Start eine frische Instanz verwenden, damit das Login-Limit nicht greift.

## API-Überblick

- `POST /api/auth/login`, `POST /api/auth/claim`, `POST /api/auth/logout`
- `POST /api/claim` (Schüler-Code → Token), `GET/PUT /api/play/...`, `GET /api/play/download`
- Admin: `/api/admin/invites|settings|teachers|audit|projects`
- Lehrer: `/api/teacher/courses`, `PATCH /api/teacher/courses/{id}` (Archivierung),
  `PATCH /api/teacher/projects/bulk`, `/api/teacher/projects*` (inkl. `regenerate-code`, `code`), `/api/teacher/tasks*`,
  `/api/teacher/submissions*`, `/api/teacher/audit`
- Schülerprojektwechsel: `GET/POST /api/play/projects`, `POST /api/play/projects/{id}/open`.
  Zugriff nur innerhalb desselben namenlosen Arbeitsbereichs.
- Eingereichte Versionen: `GET /api/teacher/submissions/{sid}/versions`,
  `GET /api/teacher/submissions/{sid}/versions/{version}` und `/download`.
- Antworten verwenden `base_version` aus der Aufgabe (`version`), damit ältere Tabs keine
  neueren Antworten überschreiben. Es sind ausschließlich `{item_id: {"checked": true|false}}` für Checkbox-Aufgabenteile erlaubt.
  Freitext, zusätzliche Felder und andere Antworttypen werden zurückgewiesen.
- Cookie-Auth + CSRF-Header (`X-CSRF-Token`, kommt aus dem Login-Response) bei allen
  schreibenden Lehrer/Admin-Requests. Schüler-Token: `Authorization: Bearer <token>`.

## Speicherkonflikte und Versionsspeicher

Bei einem Speicherkonflikt öffnet „Stände vergleichen“ den lokalen Entwurf und den aktuellen
Serverstand nebeneinander. Der Entwurf kann dort bearbeitet und mit erneuter Revisionsprüfung
gespeichert werden. Ändert sich der Server während des Vergleichs, bleibt der Entwurf erhalten
und der Vergleich wird aktualisiert. Unterschiedliche Programmdaten (`save.db`) können unabhängig
vom Quellcode ausgewählt werden. „Serverstand übernehmen“ verwirft den lokalen Programmentwurf
erst nach erfolgreichem Laden.

Das Git-Budget gilt für `.git` und zählt zusätzlich zur Arbeitsquota. Wird es durch einen neuen
Commit überschritten, wird dieser Commit zurückgenommen und die Versionierung pausiert sichtbar.
Der aktuelle Code und Medien bleiben gespeichert; frühere Git-Versionen werden nicht automatisch
umgeschrieben. Dadurch bleiben externe Git-Verläufe kompatibel. Ein bereits über dem neu gesetzten
Limit liegender Altbestand wird nicht nachträglich vernichtet. Ein zu großes Remote wird vor der
Übernahme in einer temporären Arbeitskopie abgewiesen. Diese temporäre Kopie benötigt zusätzlichen
freien Speicher. Git-Schreiboperationen werden pro Projekt prozessübergreifend serialisiert.
Auch vollständige Schüler-Schreibanfragen werden pro Projekt serialisiert, damit Quota,
Abgabe-Snapshots und Git-Stand bei parallelen Zugriffen zusammenpassen. Klassen-/Adminänderungen
und die Bereinigung laufen exklusiv gegenüber Schreibzugriffen; Leseanfragen bleiben möglich.
Bodies werden vor den Schreibsperren begrenzt eingelesen. Git-Pulls mit symbolischen Links oder
Submodulen werden abgewiesen; bereits vorhandenen Links wird beim Speichern nicht gefolgt.

Der Verlauf lässt sich als Git-Bundle herunterladen (`GET /api/play/history/download`).
`git clone miniworlds-verlauf.bundle` öffnet ihn lokal. Anschließend kann der Verlauf in der
Oberfläche gelöscht werden (`DELETE /api/play/history?base_revision=…`), um wieder Platz für
neue Versionen zu schaffen. Aktueller Code, Medien und Aufgabenabgaben bleiben dabei erhalten.
Vor dem Löschen muss ein konfiguriertes Remote entfernt werden; dessen externer Verlauf bleibt bestehen.
Push wird bei pausierter Versionierung gesperrt, damit kein unvollständiger Stand übertragen wird.

## Sicherung und geprüfte Wiederherstellung

Im Backend-Verzeichnis mit den gleichen Umgebungsvariablen wie der Server:

```sh
python -m app.backups create --directory /srv/miniworlds-backups --keep 7
python -m app.backups verify /srv/miniworlds-backups/miniworlds-ZEIT-ID.zip
python -m app.backups restore /srv/miniworlds-backups/miniworlds-ZEIT-ID.zip --destination /srv/miniworlds-restored
```

`create` sichert die SQLite-Datenbank, Projekt-/Veröffentlichungsmedien und Git-Repositories gemeinsam.
Währenddessen warten schreibende Anfragen und Hintergrundwartung auf eine gemeinsame Dateisperre;
Leseanfragen bleiben möglich. Die Sperre gilt auch über mehrere Serverprozesse. Alle Instanzen und
das Sicherungswerkzeug müssen dieselben Medien-/Git-Verzeichnisse verwenden. Externe direkte
Datenbank-/Dateiänderungen müssen während einer Sicherung unterbleiben.

Jede neue Sicherung wird vor der Erfolgsmeldung in ein temporäres Verzeichnis wiederhergestellt:
Signatur und SHA-256-Dateiprüfsummen, SQLite-Integrität/Fremdschlüssel, Entschlüsselbarkeit der Codes
und Remote-Tokens, Medien und eingefrorene Abgaben sowie `git fsck` werden geprüft. Der Schlüssel
wird separat aufbewahrt und **nicht** in die Sicherung geschrieben. Falsche Schlüssel, beschädigte
Dateien, symbolische Links und unsichere Archivpfade werden zurückgewiesen. Standardmäßig bleiben
die letzten sieben vom Werkzeug erzeugten Sicherungen im gewählten Verzeichnis erhalten.

`restore` schreibt ausschließlich in ein neues Zielverzeichnis und überschreibt keinen laufenden
Bestand. Für den anschließenden Start `DATABASE_URL=sqlite:////srv/miniworlds-restored/app.db`,
`MEDIA_ROOT=/srv/miniworlds-restored/media` und
`MINIWORLDS_GIT_ROOT=/srv/miniworlds-restored/git` sowie den bisherigen `SECRET_KEY` setzen.
Das Werkzeug unterstützt dateibasierte SQLite-Installationen.

Für regelmäßige produktive Sicherungen den `create`-Befehl in der vorhandenen Jobverwaltung
ausführen (z. B. täglich mit den Backend-Umgebungsvariablen). Jede Ausführung beinhaltet bereits
die vollständige Wiederherstellungsprüfung; `verify` kann zusätzlich bestehende Sicherungen prüfen.
Die CI führt unabhängig davon wöchentlich eine Wiederherstellung mit Testdaten durch.

## Datenschutz (Kurzfassung)

Serverseitig werden **keine Namen** gespeichert (Lehrer: E-Mail + Schule; Schüler:
nur Code-Arbeitsbereiche und deren Lernprojekte). Es gibt keine Personenlisten oder
Lehrer-/Schülerfeedback-Felder oder freien Textantworten als Aufgabenlösungen.
Programm-/Medieninhalte können selbst persönliche Angaben enthalten; die Plattform erhebt dafür keine weiteren Felder.
Die lokale Namenszuordnung wird weder hochgeladen noch dauerhaft im Browser gespeichert.
Codes liegen nur als SHA-256-Hash (Verifikation) bzw. Fernet-verschlüsselt
(Lehrer-Anzeige) in der DB. Das Protokoll verwendet technische Kennungen, keine zusätzlichen
E-Mail-/Schul-/Titelkopien und keine Melde-IP-Adressen. Lehrer sehen ausschließlich Einträge mit
ihrer Lehrerzuordnung; globale Systemereignisse bleiben beim Admin. Nach standardmäßig 30 Tagen
werden die Einträge gelöscht. Historische Protokolle werden einmalig entsprechend bereinigt.
Projektlöschungen entfernen auch die separaten Mediendateien veröffentlichter Snapshots.
Beim Start werden verwaiste Snapshot-Ordner früherer Löschungen bereinigt, sobald sie älter als
einen Tag sind. Laufende und kürzlich erzeugte Kopien bleiben erhalten.
Die tägliche Aufbewahrungsprüfung läuft in einem Hintergrundthread, unabhängig von HTTP-Anfragen;
auch ein Prüflauf ohne Änderungen speichert sein Ausführungsdatum.


## Bestehende Datenbanken

Beim Start werden fehlende Spalten/Tabellen und namenlose Arbeitsbereiche für bisherige Projekte
idempotent ergänzt. Bestehende Codes und Saves bleiben erhalten. Vorhandene `teacher_note`- und
`feedback`-Spalten werden einschließlich ihrer Inhalte entfernt; entsprechende Freitextwerte
werden auch aus Audit-Metadaten gelöscht. Eine weitere einmalige Datenschutzmigration entfernt
freie Antworttexte aus sämtlichen Entwürfen und eingereichten Abgabeversionen. Frühere
Textantwort-Aufgabenteile werden zu nicht beantwortbaren Informationstexten, auch in
Abgabe-Snapshots und Galerievorlagen. Checkboxen sowie Code, Datenbank und Medien bleiben erhalten.
Lokale alte Antwortentwürfe werden beim Laden einer Seite auf Checkboxwerte reduziert.
Bereits angelegte Backups werden dadurch nicht verändert.
Projektdateien und Datenbank gemeinsam sichern; `SECRET_KEY` muss über Neustarts stabil bleiben.

Die Worker-Ausführung folgt dem [Pyodide-Worker-Modell](https://pyodide.org/en/stable/usage/webworker.html).
Die Browserprüfung deckt zusätzlich Grafik, Tastatureingaben und das Stoppen blockierender Programme ab.
