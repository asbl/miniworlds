# Loading Data from the Database

In this tutorial, you will learn how to create a data model and synchronize it with a database. You can use this for many purposes — for example, storing quiz questions and answers, high scores, game state loading, and more.

## Step 1: Creating the Model

Start by creating a model for your data in a new file — just as you would store it in Python.

For example, a high score could be represented as a simple list storing names and scores:

```python
[(Andreas, 100), (Martin, 200), (Julius, 50)]
```

Order doesn’t matter yet, because you can always sort the list later.

Your class might initially look like this:

**File: `highscore_model.py`**

```python
import sqlite3

class Highscore:
    def __init__(self, scores=[]):
        self.scores: list = scores
```

The class has an attribute `scores`, which is either passed as a parameter or defaults to an empty list.

## Setting Up the Database

Use the tool **DB Browser for SQLite** to set up your database.

Create a table with three fields: Name, Score, and ID.

Add sample data to the database so you can test reading from it later.

## Reading from the Database

Next, implement a method to load the data.

Add this method to your class:

```python
@classmethod
def from_db(cls):
    connection = sqlite3.connect("highscore_db.db")
    cursor = connection.cursor()
    sql = 'SELECT Name, Score FROM Highscore'
    cursor.execute(sql)
    rows = cursor.fetchall()
    connection.close()
    return cls(rows)
```

This is a `classmethod`, used like a factory to create a `Highscore` object from the database.

A connection to the database is opened, a SQL query is run via a cursor, and the results are fetched and returned.

To test it:

```python
hs = Highscore.from_db()
print(hs.scores)
```

## Writing to the Database

Add the following method to write to the database:

```python
def create(self, name, score):
    connection = sqlite3.connect("highscore_db.db")
    cursor = connection.cursor()
    sql = f"INSERT INTO Highscore (Name, Score) VALUES ('{name}', '{score}')"
    cursor.execute(sql)
    connection.commit()
    connection.close()
    self.scores.append((name, score))
```

This creates a new record both in the database and in the local data structure.

## CRUD Operations

CRUD stands for:

* **C**reate – Add a record
* **R**ead – Read records
* **U**pdate – Update existing records
* **D**elete – Remove records

You need to think about these when interacting with databases.

### Create

Implemented in the `create` method.

### Read

Handled by `from_db`.

### Update

To update an existing entry:

```python
def update(self, score_id, name, new_score):
    connection = sqlite3.connect("highscore_db.db")
    cursor = connection.cursor()
    sql = f"UPDATE Highscore SET Name = '{name}', Score = '{new_score}' WHERE ID='{score_id}'"
    cursor.execute(sql)
    connection.commit()
    connection.close()
    for score in self.scores:
        if score[0] == score_id:
            self.scores.remove(score)
            self.scores.append((score_id, name, new_score))
```

### Delete

To delete an entry:

```python
def delete(self, score_id):
    connection = sqlite3.connect("highscore_db.db")
    cursor = connection.cursor()
    sql = f"DELETE FROM Highscore WHERE ID='{score_id}'"
    cursor.execute(sql)
    connection.commit()
    connection.close()
    for score in self.scores:
        if score[0] == score_id:
            self.scores.remove(score)
```

## Complete Code

```python
import sqlite3

class Highscore:
    def __init__(self, scores=[]):
        self.scores: list = scores

    @classmethod
    def from_db(cls):
        connection = sqlite3.connect("highscore_db.db")
        cursor = connection.cursor()
        sql = 'SELECT ID, Name, Score FROM Highscore'
        cursor.execute(sql)
        rows = cursor.fetchall()
        connection.close()
        return cls(rows)

    def create(self, name, score):
        connection = sqlite3.connect("highscore_db.db")
        cursor = connection.cursor()
        sql = f"INSERT INTO Highscore (Name, Score) VALUES ('{name}', '{score}')"
        cursor.execute(sql)
        connection.commit()
        connection.close()
        self.scores.append((name, score))

    def update(self, score_id, name, new_score):
        connection = sqlite3.connect("highscore_db.db")
        cursor = connection.cursor()
        sql = f"UPDATE Highscore SET Name = '{name}', Score = '{new_score}' WHERE ID='{score_id}'"
        cursor.execute(sql)
        connection.commit()
        connection.close()
        for score in self.scores:
            if score[0] == score_id:
                self.scores.remove(score)
                self.scores.append((score_id, name, new_score))

    def delete(self, score_id):
        connection = sqlite3.connect("highscore_db.db")
        cursor = connection.cursor()
        sql = f"DELETE FROM Highscore WHERE ID='{score_id}'"
        cursor.execute(sql)
        connection.commit()
        connection.close()
        for score in self.scores:
            if score[0] == score_id:
                self.scores.remove(score)

hs = Highscore.from_db()
# hs.create("Max Meier", 200)
hs.update(2, "Max Meier2", 200)
hs.delete(2)
print(hs.scores)
```

## Integrating the Model into Your Game

Once you’ve written your model, you can use it in your main program.

Here's a sample game where the player avoids falling balls. Once hit, the game ends. Initially, it looks like this:

```python
from miniworlds import *
import random
import highscore_model
import easygui

world = World(200, 600)
enemies = []
player = Circle(100, 500)
player.radius = 20
my_score = 0
score_actor = Number(10, 10)

@player.register
def on_key_pressed_a(self):
    self.move_left()

@player.register
def on_key_pressed_d(self):
    self.move_right()

@player.register
def on_detecting_right_border(self):
    self.move_back()

@player.register
def on_detecting_left_border(self):
    self.move_back()

def create_enemy():
    enemy = Circle(random.randint(20, 180), 50)
    enemy.radius = random.randint(10, 30)
    enemies.append(enemy)

@world.register
def act(self):
    global my_score
    if self.frame % 100 == 0:
        create_enemy()
    for enemy in enemies:
        enemy.move_down()
        if "bottom" in enemy.detect_borders():
            enemies.remove(enemy)
            enemy.remove()
            my_score += 1
            score_actor.set_number(my_score)
```

To add a game over and display the high score:

```python
@world.register
def act(self):
    global my_score
    if self.frame % 100 == 0:
        create_enemy()
    for enemy in enemies:
        enemy.move_down()
        if "bottom" in enemy.detect_borders():
            enemies.remove(enemy)
            enemy.remove()
            my_score += 1
            score_actor.set_number(my_score)
        if enemy in player.detect_actors():
            world.reset()
            name = easygui.enterbox(f"You reached {my_score} points! Enter your name", "Highscore")
            new_highscore(name, my_score)
```

`new_highscore` is defined as:

```python
def new_highscore(name, points):
    highscore = highscore_model.Highscore.from_db()
    highscore.create(name, points)
    scores = highscore.from_db().scores
    scores.sort()
    for index, ranking in enumerate(scores[0:10]):
        t = Text((20, index * 40))
        t.text = f"{ranking[0]} - Points: {ranking[1]}"
        t.font_size = 10
```

This fetches, updates, and displays the top 10 scores.
