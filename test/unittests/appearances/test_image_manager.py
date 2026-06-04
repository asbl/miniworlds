import pytest
pygame = pytest.importorskip("pygame")
from miniworlds.appearances.managers.image_manager import ImageManager

class DummyParent:
    def __init__(self, size):
        self.size = size
        self.width = size[0]
        self.height = size[1]

class DummyAppearance:
    LOAD_NEW_IMAGE = 2
    RELOAD_ACTUAL_IMAGE = 1
    def __init__(self, parent):
        self.parent = parent
        self.fill_color = (255, 0, 255, 255)
        self.is_scaled = False
        self._dirty = 0
    def set_dirty(self, *args, **kwargs):
        # emulate Appearance.set_dirty behavior minimal
        self._dirty = kwargs.get('status', args[1] if len(args) > 1 else 1)
        return None


def test_add_image_from_path_keeps_original_source_size(tmp_path):
    pygame.init()
    surf = pygame.Surface((64, 64))
    surf.fill((0, 255, 0))
    file = tmp_path / "test_img.png"
    pygame.image.save(surf, str(file))

    parent = DummyParent((32, 32))
    app = DummyAppearance(parent)
    im = ImageManager(app)
    idx = im.add_image_from_path(str(file))
    entry = im.images_list[idx]

    assert entry["type"] == ImageManager.IMAGE
    assert entry["source"] == str(file)
    assert entry["image"].get_size() == (64, 64)
