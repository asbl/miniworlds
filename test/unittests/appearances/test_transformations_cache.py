import pytest
pygame = pytest.importorskip("pygame")
from miniworlds.appearances.managers.transformations_manager import TransformationsManager

class DummyParent:
    def __init__(self, size):
        self.size = size
        self.width = size[0]
        self.height = size[1]
        self.orientation = 0
        self.direction = 0
        self.fill_color = (255, 255, 255, 255)

class DummyAppearance:
    def __init__(self):
        self.parent = DummyParent((32, 32))
        self._is_scaled = True
        self._is_textured = False
        self._texture_size = (0, 0)
        self._is_scaled_to_width = False
        self._is_scaled_to_height = False
        self._is_upscaled = False
        self._is_flipped = False
        self._orientation = 0
        self._coloring = None
        self._transparency = False
        self._alpha = 255
        self.image_manager = None
        self._is_rotatable = False
        self.border = 0
        self.draw_images = []
        self.draw_shapes = []
        self._dirty = 0
        self._is_centered = True


def test_pipeline_cache_distinguishes_source_surfaces_and_evicts():
    app = DummyAppearance()
    mgr = TransformationsManager(app)

    src = pygame.Surface((10, 10))
    src.fill((255, 0, 0))

    res1 = mgr.process_transformation_pipeline(src, app)
    assert res1.get_at((0, 0))[:3] == (255, 0, 0)

    blue_src = pygame.Surface((10, 10))
    blue_src.fill((0, 0, 255))
    blue_result = mgr.process_transformation_pipeline(blue_src, app)
    assert blue_result.get_at((0, 0))[:3] == (0, 0, 255)
    assert len(mgr._pipeline_cache) == 2

    max_entries = mgr._pipeline_cache_max
    sources = []
    for i in range(max_entries + 5):
        other_src = pygame.Surface((10 + i, 10 + i))
        other_src.fill(((i * 37) % 255, (i * 61) % 255, (i * 17) % 255))
        sources.append(other_src)
        mgr.process_transformation_pipeline(other_src, app)

    assert len(mgr._pipeline_cache) <= mgr._pipeline_cache_max


def test_pipeline_cache_invalidates_when_target_size_changes():
    app = DummyAppearance()
    mgr = TransformationsManager(app)
    src = pygame.Surface((10, 10))
    src.fill((255, 0, 0))

    assert mgr.process_transformation_pipeline(src, app).get_size() == (32, 32)

    app.parent.size = (48, 24)
    app.parent.width, app.parent.height = app.parent.size

    assert mgr.process_transformation_pipeline(src, app).get_size() == (48, 24)


def test_pipeline_cache_hit_skips_transformations():
    app = DummyAppearance()
    mgr = TransformationsManager(app)
    src = pygame.Surface((10, 10))
    calls = 0
    original_scale = mgr.transformation_scale

    def counted_scale(image, appearance):
        nonlocal calls
        calls += 1
        return original_scale(image, appearance)

    mgr.transformations_pipeline[2]["func"] = counted_scale

    first = mgr.process_transformation_pipeline(src, app)
    second = mgr.process_transformation_pipeline(src, app)

    assert calls == 1
    assert second is first


def test_pipeline_cache_invalidates_changed_draw_actions():
    app = DummyAppearance()
    mgr = TransformationsManager(app)
    src = pygame.Surface((32, 32), pygame.SRCALPHA)
    app._is_scaled = False
    app.draw_shapes = [
        (pygame.draw.rect, ((255, 0, 0), pygame.Rect(0, 0, 10, 10)))
    ]

    red = mgr.process_transformation_pipeline(src, app)
    assert red.get_at((5, 5))[:3] == (255, 0, 0)

    app.draw_shapes[0] = (
        pygame.draw.rect,
        ((0, 0, 255), pygame.Rect(0, 0, 10, 10)),
    )
    mgr.flag_reload_actions_for_transformation_pipeline("draw_shapes")

    blue = mgr.process_transformation_pipeline(src, app)
    assert blue.get_at((5, 5))[:3] == (0, 0, 255)
