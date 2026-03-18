# Fehlermeldungen in miniworlds - Audit für Schüler-Freundlichkeit

## Zusammenfassung
Die Fehlermeldungen in miniworlds sind technisch korrekt, aber oft nicht optimal für Schüler. Sie könnten überwiegend verbessert werden mit:
1. Klarere, direkte Fehlerdefinitionen (nicht zu technisch)
2. Konkrete Beispiele für korrekte Verwendung
3. Hilfreiche Kontextinformationen
4. Konsistente Formatierung

---

## 🔴 KRITISCHE PROBLEME (High Priority)

### 1. **Mehrzeilige raise-Statements sind unleserlich**
**Betroffene Dateien:**
- `source/miniworlds/actors/widgets/button.py:54`
- `source/miniworlds/actors/widgets/single_widget.py:257`

**Aktuell:**
```python
raise TypeError("Argument 1 must be of type str, got", type(text), text)
# Output: TypeError: ('Argument 1 must be of type str, got', <class 'int'>, 123)
```

**Schüler sehen:** `TypeError: ('Argument 1 must be of type str, got', <class 'int'>, 123)`

**Problem:** Die Nachricht ist als Tupel formatiert und sehr unleserlich

**Empfehlung:**
```python
raise TypeError(f"Argument text must be str, got {type(text).__name__}: {repr(text)}")
# Output: TypeError: Argument text must be str, got int: 123
```

---

### 2. **Fehlermeldung fehlen konkrete Beispiele**
**Betroffene Dateien:**
- `source/miniworlds/actors/actor.py:119` - Position-Format
- `source/miniworlds/tools/inspection.py:48` - Method not found
- `source/miniworlds/base/window.py:35` - Window creation error

**Aktuell:**
```python
raise NoValidPositionOnInitException(
    f"No valid world position for {actor}, type is {type(value)} and should be a 2-tuple or Position"
)
# Error: No valid world position for Actor, type is <class 'list'> and should be a 2-tuple or Position
```

**Problem:** Schüler wissen nicht, was ein "2-tuple" konkret aussieht

**Empfehlung:**
```python
raise NoValidPositionOnInitException(
    f"Position for {actor} must be a tuple like (100, 200), but got {type(value).__name__}: {repr(value)}"
)
# Error: Position for Actor must be a tuple like (100, 200), but got list: [100, 200]
```

---

### 3. **Zu technische Wording in Fehlermeldungen**
**Betroffene Dateien:**
- `source/miniworlds/worlds/manager/sensor_manager.py:103` - Filter type

**Aktuell:**
```python
raise WrongFilterType(
    f"wrong type for filter sensor results - Should be subclass of actor or instance of actor or string, but is: {type(actor)}"
)
# Error: wrong type for filter sensor results - Should be subclass of actor or instance of actor or string, but is: <class 'int'>
```

**Problem:** "subclass of actor or instance of actor" ist verwirrt für Anfänger

**Empfehlung:**
```python
raise WrongFilterType(
    f"Actor filter must be an Actor class (like Enemy), an Actor instance, or a string name (like 'Enemy'). Got {type(actor).__name__}: {repr(actor)}"
)
```

---

## 🟡 MITTLERE PROBLEME (Medium Priority)

### 4. **Fehlermeldung sind zu generisch und geben keine Hilfe**
**Betroffene Dateien:**
- `source/miniworlds/base/window.py:35` - Window creation

**Aktuell:**
```python
raise RuntimeError(f"Error on creating window: {e}") from e
# Error: Error on creating window: [Errno 2] No such file or directory: 'assets/missing.png'
```

**Schüler lernt:** "Man, was habe ich falsch gemacht?" - Kein Kontext

**Empfehlung:**
```python
# Besserer Error mit Hinweis:
raise RuntimeError(
    f"Could not initialize window. Common causes:\n"
    f"- Missing image file: {e}\n"
    f"- Invalid file path in your code\n"
    f"- Corrupted asset files\n"
    f"Full error: {e}"
) from e
```

---

### 5. **Fehlendes Kontext bei AttributeError**
**Betroffene Dateien:**
- `source/miniworlds/tools/inspection.py:48`

**Aktuell:**
```python
raise AttributeError(f"Method '{name}' not found on instance {type(self.instance).__name__}")
# Error: Method 'on_update' not found on instance Actor
```

**Schüler lernt:** Dass die Methode nicht da ist - aber nicht, wo sie definiert werden sollte

**Empfehlung:**
```python
raise AttributeError(
    f"Method '{name}' not found on {type(self.instance).__name__}.\n"
    f"Make sure you defined `def {name}(self):` in your class."
)
```

---

### 6. **Zu lange/technische Exception-Repräsentation**
**Betroffene Dateien:**
- `source/miniworlds/worlds/manager/position_manager.py:57` (uses actor.__str__)

**Aktuell Error:**
```
OriginException: origin must be 'center' or 'topleft' for actor **Actor of type [Actor]: ID: 3 at pos (0, 0) with size (40, 40)**
```

**Problem:** Die Actor-Darstellung ist zu technisch und macht die Meldung unleserlich

**Empfehlung:**
```python
# In position_manager.py, kürzer:
raise OriginException(
    f"Actor origin must be 'center' or 'topleft', not '{origin}'"
)
```

---

### 7. **Operator-Fehler geben keine Hinweise**
**Betroffene Dateien:**
- `source/miniworlds/positions/vector.py:286`

**Aktuell:**
```python
raise TypeError("Unsupported operand type for multiply.")
# Error: Unsupported operand type for multiply.
```

**Schüler lernt:** Nichts - keine Hinweise, welche Typen OK sind

**Empfehlung:**
```python
raise TypeError(
    f"Can't multiply Vector by {type(other).__name__}. "
    f"Use Vector * (int or float), not {type(other).__name__}. "
    f"Example: my_vector * 2"
)
```

---

## 🟢 GUTE FEHLERMELDUNGEN (Keep these!)

Diese Fehlermeldungen sind bereits schülfreundlich:

✅ **Timer validation (Line 46-48)**
```
Timer interval must be int, got <class 'str'>
Timer interval must be > 0, got -5
```
→ Klar, direkt, mit Kontext

✅ **Vector direction validation (Line 124)**
```
Unsupported direction string 'forward'. Use one of: up, right, down, left, top, bottom.
```
→ Zeigt alle erlaubten Optionen!

✅ **Color validation (Lines 17, 44, 48)**
```
Color tuple must contain 3 (RGB) or 4 (RGBA) float values.
```
→ Klar, mit Beispiel

✅ **Origin validation (Line 57)**
```
origin must be 'center' or 'topleft' for actor [Actor]
```
→ Zeigt beide Optionen

---

## 📋 VERBESSERUNGSPLAN

### Phase 1: SOFORT (High Priority - 7 Fixes)
1. Button/Widget text: Tupel-Fehler beheben → f-string
2. Position validation: Konkrete Beispiele hinzufügen
3. WrongFilterType: Verständlichere Wording
4. Vector multiply: Erlaubte Typen zeigen
5. Inspection AttributeError: Kontext für Definition hinzufügen
6. Position manager: Kürzere Actor-Repräsentation
7. Window error: Hilfreiche Hinweise für Common Failures

### Phase 2: LANGFRISTIG (Medium Priority)
- Alle RuntimeError/TypeError auf f-strings konvertieren
- Konsistente Präfixes (z.B. kein "Error on..." - direkt zur Sache)
- In Docstrings Beispiele für häufige Fehler dokumentieren
- Error hints in Sphinx-Dokumentation

---

## 📊 METADATEN

- **Total error locations analyzed:** 29
- **Currently student-friendly:** ~8 (28%)
- **Needs improvement:** ~14 (48%)
- **Critical (breaks readability):** ~7 (24%)
- **Files to modify:** 9
- **Estimated effort:** 2-3 hours (straightforward replacements)

---

## 🎯 LEITPRINZIPIEN für miniworlds Fehler

**Für jeden Fehler:**
1. ✅ **Was ist falsch?** → Direkt und klar
2. ✅ **Warum ist es falsch?** → Mit Kontext
3. ✅ **Wie kann es behoben werden?** → Mit Beispiel oder Hinweis
4. ✅ **Soll Anfänger-freundlich sein** → Keine technischen DL-Begriffe

**Format-Regel:**
```
<What>: <Why> <How>
Beispiel: "Text must be a string like 'Hello', got int: 123"
```

