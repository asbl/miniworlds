"""Aufgaben enthalten ausschließlich Informationstexte und boolesche Checkbox-Antworten."""


def checkbox_answers(answers):
    if not isinstance(answers, dict):
        return {}
    return {key: {"checked": value["checked"]} for key, value in answers.items()
            if isinstance(key, str) and key.isascii() and key.isdecimal()
            and isinstance(value, dict) and type(value.get("checked")) is bool}


def information_items(items):
    """Frühere Textantwort-Fragen bleiben als nicht beantwortbare Hinweise erhalten."""
    return [{**item, "kind": "text" if item.get("kind") == "textarea" else item.get("kind", "text")}
            for item in items]


def clean_snapshot(snapshot):
    if isinstance(snapshot.get("task"), dict):
        snapshot = {**snapshot, "task": {**snapshot["task"],
                    "items": information_items(snapshot["task"].get("items", []))}}
    if "answers" in snapshot:
        snapshot = {**snapshot, "answers": checkbox_answers(snapshot["answers"])}
    return snapshot
