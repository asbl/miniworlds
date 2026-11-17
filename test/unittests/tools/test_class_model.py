"""Static class model for UML views: source only, nothing is executed."""
import pytest

from miniworlds.tools.class_model import analyze

MAIN = '''import miniworlds as mw
from tiere import Tier


class Spielfeld(mw.World):
    def on_setup(self):
        self.add_background((1, 2, 3))


class Krabbe(Tier):
    """Frisst Würmer."""
    leben = 3

    def __init__(self, position=(0, 0)):
        super().__init__(position)
        self.gefressen = 0
        self._tempo: int = 2

    def act(self):
        self.gefressen += 1

    def fressen(self, menge=1, *, laut=False):
        self.gefressen += menge

    def _intern(self):
        pass

    def __repr__(self):
        return "Krabbe"

    @property
    def gefressen_text(self):
        return str(self.gefressen)


class Sonstiges:
    pass
'''

TIERE = '''import miniworlds as mw


class Tier(mw.Circle):
    pass
'''


def by_name(model):
    return {c["name"]: c for c in model["classes"]}


@pytest.mark.unit
class TestClassModel:
    def setup_method(self):
        self.model = analyze({"main.py": MAIN, "tiere.py": TIERE, "bild.png": b"x"})
        self.classes = by_name(self.model)

    def test_classes_are_ordered_main_first_and_located(self):
        assert [c["name"] for c in self.model["classes"]] == [
            "Spielfeld", "Krabbe", "Sonstiges", "Tier",
        ]
        krabbe = self.classes["Krabbe"]
        assert (krabbe["file"], krabbe["line"]) == ("main.py", 10)
        assert krabbe["end_line"] == 33
        assert self.classes["Tier"]["file"] == "tiere.py"

    def test_kind_follows_inheritance_across_files(self):
        assert self.classes["Spielfeld"]["kind"] == "world"
        assert self.classes["Krabbe"]["kind"] == "actor"  # Krabbe -> Tier -> mw.Circle
        assert self.classes["Tier"]["kind"] == "actor"
        assert self.classes["Sonstiges"]["kind"] == "other"

    def test_bases_use_the_last_name_part_and_keep_the_text(self):
        assert self.classes["Spielfeld"]["bases"] == ["World"]
        assert self.classes["Spielfeld"]["bases_text"] == ["mw.World"]
        assert self.classes["Krabbe"]["bases"] == ["Tier"]

    def test_library_chain_is_listed_up_to_the_root(self):
        libs = {lib["name"]: lib for lib in self.model["libraries"]}
        assert libs["World"]["kind"] == "world"
        assert libs["Circle"]["kind"] == "actor"
        names = set(libs)
        assert "Actor" in names  # Circle ... -> Actor
        # every library base is either another listed library class or the root
        assert all(lib["base"] is None or lib["base"] in libs for lib in libs.values())

    def test_methods_events_params_and_visibility(self):
        methods = {m["name"]: m for m in self.classes["Krabbe"]["methods"]}
        assert "__repr__" not in methods  # dunder noise is hidden
        assert methods["__init__"]["params"] == ["position"]
        assert methods["fressen"]["params"] == ["menge", "laut"]
        assert methods["act"]["kind"] == "event"
        assert methods["fressen"]["kind"] == "method"
        assert methods["_intern"]["visibility"] == "-"
        assert methods["fressen"]["visibility"] == "+"
        assert methods["fressen"]["line"] == 22
        assert self.classes["Spielfeld"]["methods"][0]["kind"] == "event"  # on_setup

    def test_attributes_from_class_body_and_self_assignments(self):
        attributes = {a["name"]: a for a in self.classes["Krabbe"]["attributes"]}
        assert set(attributes) == {"leben", "gefressen", "_tempo"}
        assert attributes["leben"]["static"] is True
        assert attributes["gefressen"]["static"] is False
        assert attributes["gefressen"]["line"] == 16  # first assignment wins
        assert attributes["_tempo"]["visibility"] == "-"
        assert "gefressen_text" not in attributes  # a property is a method

    def test_syntax_errors_are_reported_and_other_files_still_analyzed(self):
        model = analyze({"main.py": "class A(:\n", "b.py": "class B:\n    pass\n"})
        assert [c["name"] for c in model["classes"]] == ["B"]
        assert model["errors"][0]["file"] == "main.py"
        assert model["errors"][0]["line"] == 1

    def test_inheritance_cycles_and_unknown_bases_do_not_hang(self):
        model = analyze({"main.py": "class A(B): pass\nclass B(A): pass\nclass C(Fremd): pass\n"})
        assert {c["kind"] for c in model["classes"]} == {"other"}

    def test_nothing_is_executed(self):
        source = "import os\nos.system('exit 1')\nraise SystemExit\nclass A: pass\n"
        assert [c["name"] for c in analyze({"main.py": source})["classes"]] == ["A"]
