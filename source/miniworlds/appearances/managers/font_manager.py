import pygame


class FontManager:
    def __init__(self, appearance):
        self.font_size = 0  #: font_size if actor-text != ""
        self.text_position = (0, 0)  #: Position of text relative to the top-left pixel of actor
        self.font_path = None  #: Path to font-file
        self.font_style = "monospace"
        self.text = ""
        self.appearance = appearance
        self._font_key = None
        self._font = None

    @property
    def font(self):
        return self._get_font_object()
    
    def _get_font_object(self):
        # The font module can be de-initialized by a host calling pygame.quit()
        # between runs (e.g. web player stop -> restart).
        if not pygame.font.get_init():
            pygame.font.init()
            self._font = None
        font_size = int(self.font_size)
        key = (self.font_path, self.font_style, font_size)
        if self._font is not None and key == self._font_key:
            try:
                # Another manager or host may already have reinitialized the
                # module after quit(), leaving get_init() true but this Font
                # invalid. pygame-ce checks the font's lifetime here.
                self._font.get_height()
            except pygame.error:
                self._font = None
            else:
                return self._font
        if self.font_path is None:
            font = pygame.font.SysFont(self.font_style, int(font_size))
        else:
            font = pygame.font.Font(self.font_path, font_size)
        self._font_key = key
        self._font = font
        return font

    def get_text_width(self, text=None):
        try:
            if not text:
                text = self.text
            font = self._get_font_object()
            return font.size(text)[0]
        except TypeError:
            return 0

    def get_text_height(self):
        try:
            font = self._get_font_object()
            return font.size(self.text)[1]
        except TypeError:
            return 0

    def transformation_write_text(self, image: pygame.Surface, parent, color) -> pygame.Surface:
        # called from write_text in transformations_manager
        font = self._get_font_object()
        if not self.appearance.parent.color:
            color = (255, 255, 255)
        else:
            color = self.appearance.parent.color
        rendered_text = font.render(self.text, True, color)
        image.blit(rendered_text, self.text_position)
        return image

    def set_font_size(self, value, update=True):
        self.font_size = value
        if update:
            self.appearance.set_dirty("write_text", self.appearance.RELOAD_ACTUAL_IMAGE)
