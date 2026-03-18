# Fehler-Beispiele: Vorher vs. Nachher

## 1. Button Text Type Error (KRITISCH - UNLESERLICH)

### 🔴 VORHER (Aktuell - SCHLECHT für Schüler)
```python
# Code in button.py:54
raise TypeError("Argument 1 must be of type str, got", type(text), text)

# Was der Schüler SIEHT:
TypeError: ('Argument 1 must be of type str, got', <class 'int'>, 123)
```
❌ Aktuell: Tuple-Format ist verwirrend und Argument Name "1" ist nicht hilfsreich

### ✅ NACHHER (Neu - GUT für Schüler)
```python
raise TypeError(
    f"Button text must be a string like 'Click me', got {type(text).__name__}: {repr(text)}"
)

# Was der Schüler SIEHT:
TypeError: Button text must be a string like 'Click me', got int: 123
```
✅ Neu: Klare Fehlermeldung mit Beispiel

---

## 2. Position Format Error

### 🔴 VORHER (Aktuell - UNVOLLSTÄNDIG)
```python
# Code in actor.py:119
raise NoValidPositionOnInitException(
    f"No valid world position for {actor}, type is {type(value)} and should be a 2-tuple or Position"
)

# Schüler Code der den Fehler verursacht:
actor.position = [100, 200]  # List stattTuple

# Was der Schüler SIEHT:
NoValidPositionOnInitException: No valid world position for Actor, type is <class 'list'> and should be a 2-tuple or Position
```
❌ Aktuell: "2-tuple" ist zu technisch, Schüler weiß nicht, wie ein Tuple aussieht

### ✅ NACHHER (Neu - GUT für Schüler)
```python
raise NoValidPositionOnInitException(
    f"Position for {actor} must be a tuple like (100, 200), not {type(value).__name__}: {repr(value)}. "
    f"Try: actor.position = (100, 200)"
)

# Was der Schüler SIEHT:
NoValidPositionOnInitException: Position for Actor must be a tuple like (100, 200), not list: [100, 200]. Try: actor.position = (100, 200)
```
✅ Neu: Konkret mit Beispiel und Fix

---

## 3. Sensor Filter Type Error

### 🔴 VORHER (Aktuell - VERWIRRT)
```python
# Code in sensor_manager.py:103
raise WrongFilterType(
    f"wrong type for filter sensor results - Should be subclass of actor or instance of actor or string, but is: {type(actor)}"
)

# Schüler Code der den Fehler verursacht:
enemies = actor.detect_actors(actor_type=123)

# Was der Schüler SIEHT:
WrongFilterType: wrong type for filter sensor results - Should be subclass of actor or instance of actor or string, but is: <class 'int'>
```
❌ Aktuell: "subclass of actor or instance of actor" ist Verwirrung

### ✅ NACHHER (Neu - GUT für Schüler)
```python
raise WrongFilterType(
    f"Actor filter must be:\n"
    f"  - An Actor class, like: actor_type=Enemy\n"
    f"  - An Actor name string, like: actor_type='Enemy'\n"
    f"  - Got {type(actor).__name__}: {repr(actor)}"
)

# Was der Schüler SIEHT:
WrongFilterType: Actor filter must be:
  - An Actor class, like: actor_type=Enemy
  - An Actor name string, like: actor_type='Enemy'
  - Got int: 123
```
✅ Neu: Klare Optionen, jede mit Beispiel

---

## 4. Vector Multiply Type Error

### 🔴 VORHER (Aktuell - UNHILFSREICH)
```python
# Code in vector.py:286
raise TypeError("Unsupported operand type for multiply.")

# Schüler Code der den Fehler verursacht:
v = Vector(10, 20)
result = v * "hello"

# Was der Schüler SIEHT:
TypeError: Unsupported operand type for multiply.
```
❌ Aktuell: 0% Hinweise, welche Typen OK sind

### ✅ NACHHER (Neu - GUT für Schüler)
```python
raise TypeError(
    f"Can't multiply Vector by {type(other).__name__}. "
    f"Multiply Vector by a number instead. "
    f"Example: my_vector * 2 or my_vector * 0.5"
)

# Was der Schüler SIEHT:
TypeError: Can't multiply Vector by str. Multiply Vector by a number instead. Example: my_vector * 2 or my_vector * 0.5
```
✅ Neu: Erlaubte Typen und Beispiel

---

## 5. Method Not Found Error

### 🔴 VORHER (Aktuell - UNVOLLSTÄNDIG)
```python
# Code in inspection.py:48
raise AttributeError(f"Method '{name}' not found on instance {type(self.instance).__name__}")

# Schüler Code der den Fehler verursacht:
# Der Actor hat `on_message_received` als Input definiert statt `on_message`

# Was der Schüler SIEHT:
AttributeError: Method 'on_message' not found on instance Actor
```
❌ Aktuell: Keine Hinweise, wo die Methode hätte definiert werden sollen

### ✅ NACHHER (Neu - GUT für Schüler)
```python
raise AttributeError(
    f"Method '{name}' not found on {type(self.instance).__name__}.\n"
    f"Did you remember to define `def {name}(self):` in your class?\n"
    f"Event methods must be named exactly: {name}\n"
    f"Hint: Check the spelling!"
)

# Was der Schüler SIEHT:
AttributeError: Method 'on_message' not found on Actor.
Did you remember to define `def on_message(self):` in your class?
Event methods must be named exactly: on_message
Hint: Check the spelling!
```
✅ Neu: Kontextiert mit Lösungshinweis

---

## 6. Window Creation Error (Zu generisch)

### 🔴 VORHER (Aktuell - UNHILFSREICH)
```python
# Code in window.py:35
raise RuntimeError(f"Error on creating window: {e}") from e

# Schüler hat ein fehlende Asset:
# world = World()

# Was der Schüler SIEHT:
RuntimeError: Error on creating window: [Errno 2] No such file or directory: 'assets/logo.png'
```
❌ Aktuell: Schüler hat keine Idee, was die häufigen Gründe sind

### ✅ NACHHER (Neu - GUT für Schüler)
```python
raise RuntimeError(
    f"Could not create the window. Common reasons:\n"
    f"1. Missing asset file: 'assets/logo.png'\n"
    f"2. Wrong file path (use 'assets/file.png', not 'assets\\file.png')\n"
    f"3. File format not supported (use PNG, JPG, or GIF)\n"
    f"Full error: {e}"
) from e

# Was der Schüler SIEHT:
RuntimeError: Could not create the window. Common reasons:
1. Missing asset file: 'assets/logo.png'
2. Wrong file path (use 'assets/file.png', not 'assets\file.png')
3. File format not supported (use PNG, JPG, or GIF)
Full error: [Errno 2] No such file or directory: 'assets/logo.png'
```
✅ Neu: Mit häufigen Ursachen und Lösungshinweisen

---

## 7. Origin Value Error

### 🔴 VORHER (Aktuell - ZU TECHNISCH)
```
OriginException: origin must be 'center' or 'topleft' for actor **Actor of type [Actor]: ID: 3 at pos (0, 0) with size (40, 40)**
```
❌ Aktuell: Actor-Darstellung ist viel zu lang und technisch

### ✅ NACHHER (Neu - GUT für Schüler)
```
OriginException: Actor origin must be 'center' or 'topleft', not 'middle'
```
✅ Neu: Kurz, prägnant, zeigt die ungültige Wert

---

## 📊 VERGLEICHES-RESÜMEE

| # | Fehler | Jetzt | Neu | Verbesserung |
|---|--------|-------|-----|--------------|
| 1 | Button Text | ❌ Tupel | ✅ f-String | Clear format |
| 2 | Position | ❌ Zu technisch | ✅ Mit Beispiel | +Code example |
| 3 | Filter | ❌ Verwirrend | ✅ Bulleted list | +Options |
| 4 | Vector multiply | ❌ Leer | ✅ Mit Beispiel | +What's allowed |
| 5 | Method | ❌ Unvollständig | ✅ Mit Hinweis | +How to fix |
| 6 | Window | ❌ Zu generisch | ✅ Mit Lösungen | +Troubleshooting |
| 7 | Origin | ❌ Zu lang | ✅ Kurz | -Noise |

---

## 🎓 SCHÜLER PERSPECTIVE

Wie unterschiedlich die User Experience ist:

### Scenario: Schüler macht einen Fehler

**JETZT (Schlecht):**
```
TypeError: ('Argument 1 must be of type str, got', <class 'int'>, 123)
💭 Schüler: "Was ist das? Ein Tupel? Was bedeutet 'Argument 1'?"
👎 Frustriert, verwirrt, gibt auf
```

**NEU (Gut):**
```
TypeError: Button text must be a string like 'Click me', got int: 123
💭 Schüler: "Aha! Ich soll einen Text geben, wie 'Click me', aber ich gab 123"
👍 Versteht den Fehler sofort, kann ihn beheben
```

