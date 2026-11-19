import json

import pytest

from miniworlds.tools.api_index import build_index


@pytest.mark.unit
class TestApiIndex:
    def setup_method(self):
        self.index = build_index()["classes"]

    def members(self, cls):
        return {m["name"]: m for m in self.index[cls]["members"]}

    def test_actor_and_world_are_indexed_with_kinds(self):
        assert self.index["Actor"]["kind"] == "actor"
        assert self.index["World"]["kind"] == "world"
        assert self.index["Circle"]["kind"] == "actor"
        assert self.index["TiledWorld"]["base"] == "World"

    def test_public_base_chain_ends_in_actor(self):
        name, seen = "Circle", []
        while name:
            seen.append(name)
            name = self.index[name]["base"]
        assert seen[-1] == "Actor"

    def test_methods_have_signature_and_first_doc_line(self):
        move = self.members("Actor")["move"]
        assert move["kind"] == "method"
        assert move["signature"].startswith("(")
        assert "self" not in move["signature"]
        assert move["doc"] and "\n" not in move["doc"]

    def test_properties_and_privates(self):
        actor = self.members("Actor")
        assert actor["center"]["kind"] == "property"
        assert not any(name.startswith("_") for name in actor)

    def test_docs_are_the_members_own_first_line_not_a_builtin_docstring(self):
        move = self.members("Actor")["move"]["doc"]
        assert "object" not in move and "bytes_or_buffer" not in move
        docs = {m["doc"] for c in self.index.values() for m in c["members"] if m["doc"]}
        assert len(docs) > 100  # distinct docs, not one shared text

    def test_members_of_internal_base_classes_are_listed_with_the_public_class(self):
        assert {"register", "remove"} <= set(self.members("Actor"))
        assert {"width", "height", "register"} <= set(self.members("World"))

    def test_engine_plumbing_is_hidden_not_listed(self):
        from miniworlds.tools.api_index import INTERNAL_MEMBERS

        for cls in ("Actor", "World", "Circle", "TiledWorld"):
            listed = {m["name"] for m in self.index[cls]["members"]}
            assert not listed & INTERNAL_MEMBERS, (cls, sorted(listed & INTERNAL_MEMBERS))
        assert {"position_manager", "costume_manager"} <= set(self.index["Actor"]["hidden"])
        assert "move" in self.members("Actor")  # student API stays

    def test_nothing_public_is_unknown_to_the_index(self):
        import miniworlds

        for name in ("Actor", "Circle", "World", "TiledWorld"):
            known, current = set(), name
            while current:
                entry = self.index[current]
                known |= {m["name"] for m in entry["members"]} | set(entry["hidden"])
                current = entry["base"]
            public = {n for n in dir(getattr(miniworlds, name)) if not n.startswith("_")}
            assert public <= known, (name, sorted(public - known))

    def test_index_is_json_serializable_and_small(self):
        text = json.dumps(build_index())
        assert len(text) < 400_000
