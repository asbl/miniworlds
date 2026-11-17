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

    def test_index_is_json_serializable_and_small(self):
        text = json.dumps(build_index())
        assert len(text) < 400_000
