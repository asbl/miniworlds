# Nachrichten 

## Nachrichten senden 

Mit **`send_message(self, message)`** kannst du eine Nachricht an alle Objekte in deiner Welt senden. 
Diese Nachrichten können von anderen Objekten empfangen und verarbeitet werden, wenn sie auf das entsprechende Ereignis hören.

### Beispiel:

In diesem Beispiel sendet player 1 eine Nachricht, dass er sich bewegt hat.
```python
@player1.register
def on_key_down(self, keys):
    if 'a' in keys:
        self.move()  # Bewegt player1
        self.send_message("p1moved")  # Sendet Nachricht "p1moved" an alle
```

## Nachrichten empfangen 

Mit dem decorator `register_message("message")` kannst du eine Nachricht registrieren:

### Beispiel:

Im folgenden Beispiel wird die Nachricht, die player1 versendet, von player2 empfangen.
Er bewegt sich immer dann in die Richtung von player1, wenn dieser sich bewegt

```python
@player1.register
def on_key_down(self, keys):
    if 'a' in keys:
        self.move()  # Bewegt player1
        self.send_message("p1moved")  # Sendet Nachricht "p1moved" an alle

@player2.register_message("p1moved") # Hier wird registriert, dass die folgende Funktion auf die Message "p1moved" reagieren soll.
def follow(self, data): # Der Funktionsname ist hier egal
    self.move_towards(player1)  # player2 bewegt sich in Richtung player1
```

### Erklärung:

- In diesem Beispiel sendet **player1** die Nachricht `"p1moved"`, wenn die Taste <kbd>A</kbd> gedrückt wird.
- **player2** hat eine Methode registriert, die auf diese Nachricht hört. 
  Sobald **player1** sich bewegt, empfängt **player2** die Nachricht und bewegt sich in Richtung von **player1**.
