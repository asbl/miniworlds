"""Beginner hints from source only; conservative by design."""
import pytest

from miniworlds.tools.code_hints import check

HEADER = "import miniworlds as mw\n\n\n"


def hints(source, **extra):
    files = {"main.py": source}
    files.update(extra)
    return check(files)


def codes(found):
    return [h["code"] for h in found]


@pytest.mark.unit
class TestCodeHints:
    def test_correct_program_has_no_hints(self):
        source = HEADER + '''class Welt(mw.World):
    def on_setup(self):
        self.add_background((1, 2, 3))


class Krabbe(mw.Circle):
    def __init__(self, position=(0, 0)):
        super().__init__(position, 16)
        self.gefressen = 0

    def act(self):
        self.move(2)
        for wurm in self.detect_all(Krabbe):
            wurm.remove()
            self.gefressen += 1
        print(self.world.width, [x for x in range(3)])


welt = Welt(400, 300)
welt.run()
'''
        assert hints(source) == []

    def test_undefined_name_with_suggestion(self):
        found = hints(HEADER + "class A(mw.Actor):\n    def act(self):\n        pritn('x')\n\nw = mw.World()\nw.run()\n")
        assert codes(found) == ["undefined-name"]
        assert found[0]["replacement"] == "print"
        assert found[0]["line"] == 6
        assert "pritn" in found[0]["message"] and "print" in found[0]["message"]

    def test_forgotten_self_before_a_method(self):
        found = hints(HEADER + "class A(mw.Actor):\n    def act(self):\n        move(2)\n\nw = mw.World()\nw.run()\n")
        assert codes(found) == ["missing-self"]
        assert found[0]["replacement"] == "self.move"

    def test_unknown_member_close_to_a_known_one(self):
        found = hints(HEADER + "class A(mw.Actor):\n    def act(self):\n        self.mov(2)\n\nw = mw.World()\nw.run()\n")
        assert codes(found) == ["unknown-member"]
        assert found[0]["replacement"] == "self.move"

    def test_own_attributes_and_methods_are_known(self):
        source = HEADER + '''class A(mw.Actor):
    def __init__(self, position=(0, 0)):
        super().__init__(position)
        self.energie = 3

    def act(self):
        self.energy_low = self.energie < 2
        self.helfer()

    def helfer(self):
        pass

w = mw.World()
w.run()
'''
        assert hints(source) == []

    def test_unknown_member_without_a_close_match_is_not_reported(self):
        assert hints(HEADER + "class A(mw.Actor):\n    def act(self):\n        self.xyzzy_unrelated()\n\nw = mw.World()\nw.run()\n") == []

    def test_inheritance_across_files_is_followed(self):
        tiere = HEADER + "class Tier(mw.Actor):\n    def fressen(self):\n        pass\n"
        main = "from tiere import Tier\nimport miniworlds as mw\n\n\nclass Hund(Tier):\n    def act(self):\n        self.fresen()\n\nw = mw.World()\nw.run()\n"
        found = hints(main, **{"tiere.py": tiere})
        assert codes(found) == ["unknown-member"]
        assert found[0]["replacement"] == "self.fressen"

    def test_unresolvable_base_disables_member_checks(self):
        main = "from fremd import Mixin\nimport miniworlds as mw\n\n\nclass A(Mixin, mw.Actor):\n    def act(self):\n        self.mov(2)\n\nw = mw.World()\nw.run()\n"
        # Mixin lives in a file we can see, so the typo is found ...
        assert "unknown-member" in codes(hints(main, **{"fremd.py": "class Mixin: pass\n"}))
        # ... but a base we cannot see at all silences the check
        assert hints(main) == []
        assert hints("import miniworlds as mw\nfrom unbekannt import Base\n\n\nclass A(Base):\n    def act(self):\n        self.mov(2)\n\nmw.World().run()\n") == []

    def test_extension_packages_silence_member_checks(self):
        main = "import miniworlds as mw\nimport miniworlds_physics\n\n\nclass A(mw.Actor):\n    def act(self):\n        self.mov(2)\n\nmw.World().run()\n"
        assert hints(main) == []

    def test_hooks_defined_only_by_subclasses_are_known_on_the_base(self):
        source = HEADER + (
            "class Fabrik:\n    def bauen(self):\n        return self.erzeuge_objekt()\n\n\n"
            "class Mauer(Fabrik):\n    def erzeuge_objekt(self):\n        return 1\n\n"
            "    def erzeuge_objekte(self):\n        return 2\n\n"
            "mw.World().run()\n"
        )
        assert hints(source) == []

    def test_nested_handlers_with_their_own_self_are_not_checked_against_the_class(self):
        source = HEADER + (
            "class Tester:\n    def setup(self, world):\n        @world.register\n"
            "        def on_setup(self):\n            self.init_test()\n\n    def init_tests(self):\n        pass\n\n"
            "mw.World().run()\n"
        )
        assert hints(source) == []

    def test_columns_are_utf16_so_umlauts_do_not_shift_the_range(self):
        source = HEADER + 'class A(mw.Actor):\n    def act(self):\n        print("Größe äöü 😀", pritn(1))\n\nmw.World().run()\n'
        found = hints(source)
        line = source.split("\n")[found[0]["line"] - 1]
        utf16 = line.encode("utf-16-le")
        shown = utf16[found[0]["col"] * 2 : found[0]["end_col"] * 2].decode("utf-16-le")
        assert shown == "pritn"

    def test_method_without_self(self):
        found = hints(HEADER + "class A(mw.Actor):\n    def act():\n        pass\n\n    @staticmethod\n    def ok():\n        pass\n\nw = mw.World()\nw.run()\n")
        assert codes(found) == ["missing-self-param"]
        assert found[0]["line"] == 5

    def test_missing_run_is_reported_on_main_only(self):
        found = hints(HEADER + "w = mw.World()\n", **{"helfer.py": "x = 1\n"})
        assert codes(found) == ["no-run"]
        assert hints("import miniworlds as mw\nw = mw.World()\nw.run()\n") == []

    def test_star_import_from_another_module_silences_name_checks(self):
        assert "undefined-name" not in codes(hints("from fremd import *\nfoo()\n"))

    def test_miniworlds_star_import_knows_the_library_names(self):
        source = "from miniworlds import *\n\n\nclass W(World):\n    pass\n\nW().run()\n"
        assert hints(source) == []

    def test_scopes_do_not_cause_false_positives(self):
        source = '''import miniworlds as mw
import random as zufall


def helfer(a, *rest, b=2, **kw):
    total = sum(x for x in rest)
    try:
        pass
    except ValueError as fehler:
        print(fehler)
    with open("f") as datei:
        data = datei.read()
    callback = lambda q: q + a
    return callback(total), data, kw, b, zufall.random()


for i, (p, q) in enumerate([(1, 2)]):
    print(i, p, q)
mw.World().run()
'''
        assert hints(source) == []

    def test_broken_file_is_skipped_quietly(self):
        assert check({"main.py": "class A(:\n"}) == []
